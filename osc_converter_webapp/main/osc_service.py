"""
OSC Service - Manages multiple OSC servers in separate threads
"""
import re
import threading
import logging
from datetime import datetime

from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher

logger = logging.getLogger(__name__)

_PLACEHOLDER_RE = re.compile(r'\{\d+\}')


class OSCService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.servers = {}       # {config_pk: {'server': ..., 'thread': ..., 'config': ...}}
        self.clients = {}       # {(ip, port): SimpleUDPClient}
        self._clients_lock = threading.Lock()
        self.log_messages = {}  # {config_pk: [log_entries]}
        self.global_logs = []
        self.max_log_messages = 100

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, message, config_pk=None):
        log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        bucket = self.log_messages.setdefault(config_pk if config_pk is not None else '__global__', []) \
            if config_pk is not None else self.global_logs
        if config_pk is not None:
            self.log_messages.setdefault(config_pk, []).append(log_entry)
            logs = self.log_messages[config_pk]
        else:
            self.global_logs.append(log_entry)
            logs = self.global_logs
        if len(logs) > self.max_log_messages:
            logs.pop(0)
        logger.info(message)

    def _tail(self, logs, n=20):
        return logs[-n:] if logs else []

    # ------------------------------------------------------------------
    # UDP client cache
    # ------------------------------------------------------------------

    def _get_client(self, ip, port):
        key = (ip, port)
        if key not in self.clients:
            with self._clients_lock:
                if key not in self.clients:
                    self.clients[key] = udp_client.SimpleUDPClient(ip, port)
        return self.clients[key]

    # ------------------------------------------------------------------
    # Message templating
    # ------------------------------------------------------------------

    def _build_parts(self, addr, args):
        """addr='/a/b/c', args=('go', 1) → ['a','b','c','go',1] (1-indexed via {n})"""
        return [p for p in addr.split('/') if p] + list(args)

    def _apply_template(self, template, parts):
        """Replace {n} placeholders (1-based) with parts values."""
        result = template
        for i, val in enumerate(parts, start=1):
            result = result.replace(f'{{{i}}}', str(val))
        return result

    def _cast(self, value):
        """Cast string to int or float if possible."""
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _default_handler(self, config_name, config_pk):
        def handler(addr, *args):
            if addr == "/":
                return
            values = ", ".join(str(a) for a in args)
            suffix = f" = {values}" if values else ""
            self._log(f"[Rx] {addr}{suffix} (unmapped)", config_pk)
        return handler

    def _create_handler(self, config_name, config_pk, tx_ip, tx_port, osc_output):
        has_placeholders = bool(_PLACEHOLDER_RE.search(osc_output))

        def handler(addr, *args):
            if addr == "/":
                return
            try:
                parts = self._build_parts(addr, args)
                tokens = self._apply_template(osc_output, parts).split()
                if not tokens:
                    return
                out_addr = tokens[0]
                if has_placeholders:
                    out_args = [self._cast(t) for t in tokens[1:]]
                    out_value = out_args if len(out_args) > 1 else (out_args[0] if out_args else None)
                else:
                    out_value = list(args) if len(args) > 1 else (args[0] if args else None)
                in_values = ", ".join(str(a) for a in args)
                in_suffix = f" = {in_values}" if in_values else ""
                out_suffix = f" = {out_value}" if out_value is not None else ""
                self._log(f"[Rx] {addr}{in_suffix} → [Tx] {tx_ip}:{tx_port} @ {out_addr}{out_suffix}", config_pk)
                self._get_client(tx_ip, tx_port).send_message(out_addr, out_value)
            except Exception as e:
                self._log(f"[Error] handler {addr}: {e}", config_pk)

        return handler

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------

    def is_config_running(self, config_pk):
        return config_pk in self.servers

    def start_config(self, config):
        if config.pk in self.servers:
            self._log("Already running", config.pk)
            return False
        try:
            dispatcher = Dispatcher()
            dispatcher.set_default_handler(self._default_handler(config.name, config.pk))
            for disp in config.dispatchers.filter(is_enabled=True):
                handler = self._create_handler(config.name, config.pk, disp.tx_ip, disp.tx_port, disp.osc_output)
                dispatcher.map(disp.osc_input, handler)
                self._log(f"Dispatcher: {disp.osc_input} → {disp.tx_ip}:{disp.tx_port} @ {disp.osc_output}", config.pk)
            server = osc_server.ThreadingOSCUDPServer((config.rx_ip, config.rx_port), dispatcher)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.servers[config.pk] = {'server': server, 'thread': thread, 'config': config}
            self._log(f"Server started - RX {config.rx_ip}:{config.rx_port}", config.pk)
            return True
        except Exception as e:
            self._log(f"Error starting: {e}", config.pk)
            return False

    def stop_config(self, config_pk):
        if config_pk not in self.servers:
            self._log(f"Configuration {config_pk} not started", config_pk)
            return False
        try:
            self.servers.pop(config_pk)['server'].shutdown()
            self._log("Server stopped", config_pk)
            return True
        except Exception as e:
            self._log(f"Error stopping: {e}", config_pk)
            return False

    def restart_config(self, config):
        self._log("Restarting...", config.pk)
        self.stop_config(config.pk)
        return self.start_config(config)

    def stop_all(self):
        for config_pk in list(self.servers.keys()):
            self.stop_config(config_pk)
        self.clients = {}

    # ------------------------------------------------------------------
    # Status / logs
    # ------------------------------------------------------------------

    def get_running_configs(self):
        return list(self.servers.keys())

    def get_status(self):
        logs_by_config = {pk: self._tail(logs) for pk, logs in self.log_messages.items()}
        global_logs = self._tail(self.global_logs)
        return {
            'running_configs': self.get_running_configs(),
            'logs_by_config': logs_by_config,
            'global_logs': global_logs,
            'logs': global_logs,
        }

    def get_config_logs(self, config_pk):
        return self._tail(self.log_messages.get(config_pk, []))

    def clear_config_logs(self, config_pk):
        self.log_messages.pop(config_pk, None)

    @property
    def is_running(self):
        return bool(self.servers)


osc_service = OSCService()
