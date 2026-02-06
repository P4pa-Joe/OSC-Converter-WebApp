"""
OSC Service - Manages multiple OSC servers in separate threads
"""
import threading
import logging
from datetime import datetime

from pythonosc import osc_server, udp_client
from pythonosc.dispatcher import Dispatcher

logger = logging.getLogger(__name__)


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
        self.servers = {}  # {config_pk: {'server': server, 'thread': thread, 'config': config}}
        self.clients = {}  # UDP clients cache by (ip, port)
        self.log_messages = {}  # {config_pk: [log_entries]} - logs per configuration
        self.global_logs = []  # Global logs (system messages)
        self.max_log_messages = 100

    def _log(self, message, config_pk=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"

        if config_pk is not None:
            if config_pk not in self.log_messages:
                self.log_messages[config_pk] = []
            self.log_messages[config_pk].append(log_entry)
            if len(self.log_messages[config_pk]) > self.max_log_messages:
                self.log_messages[config_pk].pop(0)
        else:
            self.global_logs.append(log_entry)
            if len(self.global_logs) > self.max_log_messages:
                self.global_logs.pop(0)

        logger.info(message)

    def _get_client(self, ip, port):
        """Get or create a UDP client for the given IP:port"""
        key = (ip, port)
        if key not in self.clients:
            self.clients[key] = udp_client.SimpleUDPClient(ip, port)
        return self.clients[key]

    def _default_handler(self, config_name, config_pk):
        """Create a default handler for unmapped messages"""
        def handler(addr, *args):
            value = args[0] if args else ""
            if addr == "/":
                return
            self._log(f"[Rx] {addr} = {value} (unmapped)", config_pk)
        return handler

    def _create_handler(self, config_name, config_pk, tx_ip, tx_port, osc_output):
        def handler(unused_addr, *args):
            if not args:
                return
            value = args[0]
            if unused_addr == "/":
                return
            self._log(f"[Rx] {unused_addr} → [Tx] {tx_ip}:{tx_port} @ {osc_output} = {value}", config_pk)
            client = self._get_client(tx_ip, tx_port)
            client.send_message(osc_output, value)
        return handler

    def is_config_running(self, config_pk):
        """Check if a configuration is running"""
        return config_pk in self.servers

    def start_config(self, config):
        """Start a specific configuration"""
        if config.pk in self.servers:
            self._log(f"Already running", config.pk)
            return False

        try:
            dispatcher = Dispatcher()
            dispatcher.set_default_handler(self._default_handler(config.name, config.pk))

            for disp in config.dispatchers.filter(is_enabled=True):
                handler = self._create_handler(config.name, config.pk, disp.tx_ip, disp.tx_port, disp.osc_output)
                dispatcher.map(disp.osc_input, handler)
                self._log(f"Dispatcher: {disp.osc_input} → {disp.tx_ip}:{disp.tx_port} @ {disp.osc_output}", config.pk)

            server = osc_server.ThreadingOSCUDPServer(
                (config.rx_ip, config.rx_port),
                dispatcher
            )

            server_thread = threading.Thread(target=server.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            self.servers[config.pk] = {
                'server': server,
                'thread': server_thread,
                'config': config
            }

            self._log(f"Server started - RX {config.rx_ip}:{config.rx_port}", config.pk)
            return True

        except Exception as e:
            self._log(f"Error starting: {e}", config.pk)
            return False

    def stop_config(self, config_pk):
        """Stop a specific configuration"""
        if config_pk not in self.servers:
            self._log(f"Configuration {config_pk} not started")
            return False

        try:
            server_info = self.servers[config_pk]
            server_info['server'].shutdown()
            del self.servers[config_pk]
            self._log(f"Server stopped", config_pk)
            return True
        except Exception as e:
            self._log(f"Error stopping: {e}", config_pk)
            return False

    def restart_config(self, config):
        """Restart a specific configuration"""
        self._log(f"Restarting...", config.pk)
        self.stop_config(config.pk)
        return self.start_config(config)

    def stop_all(self):
        """Stop all servers"""
        config_pks = list(self.servers.keys())
        for config_pk in config_pks:
            self.stop_config(config_pk)
        self.clients = {}

    def get_running_configs(self):
        """Return list of running configuration IDs"""
        return list(self.servers.keys())

    def get_status(self):
        # Get logs per config (last 20 entries each)
        logs_by_config = {}
        for config_pk, logs in self.log_messages.items():
            logs_by_config[config_pk] = logs[-20:] if logs else []

        return {
            'running_configs': self.get_running_configs(),
            'logs_by_config': logs_by_config,
            'global_logs': self.global_logs[-20:] if self.global_logs else [],
            'logs': self.global_logs[-20:] if self.global_logs else []  # Backward compatibility
        }

    def get_config_logs(self, config_pk):
        """Get logs for a specific configuration"""
        if config_pk in self.log_messages:
            return self.log_messages[config_pk][-20:]
        return []

    def clear_config_logs(self, config_pk):
        """Clear logs for a specific configuration"""
        if config_pk in self.log_messages:
            self.log_messages[config_pk] = []

    @property
    def is_running(self):
        return len(self.servers) > 0


osc_service = OSCService()
