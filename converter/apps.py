from django.apps import AppConfig
import os
import sys
import threading


class ConverterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'converter'

    def ready(self):
        # Skip auto-start for management commands that don't need it
        skip_commands = {'migrate', 'makemigrations', 'collectstatic', 'check', 'shell', 'dbshell', 'inspectdb', 'showmigrations', 'sqlmigrate'}
        if any(cmd in sys.argv for cmd in skip_commands):
            return

        # Determine if we should run auto-start
        # Django runserver with reloader runs ready() twice:
        # 1. In the parent watcher process (RUN_MAIN not set)
        # 2. In the child reloader process (RUN_MAIN='true')
        # We only want to run auto-start once.

        run_main = os.environ.get('RUN_MAIN')
        is_runserver = 'runserver' in sys.argv

        if is_runserver:
            # For runserver: only run in the reloaded child process
            if run_main == 'true':
                self._schedule_auto_start()
        else:
            # For gunicorn/wsgi: always run (RUN_MAIN not set)
            self._schedule_auto_start()

    def _schedule_auto_start(self):
        # Start in a separate thread to avoid DB access during app initialization
        thread = threading.Thread(target=self._start_auto_configs, daemon=True)
        thread.start()

    def _start_auto_configs(self):
        try:
            from django.db import connection
            from django.db.utils import OperationalError, ProgrammingError

            # Check if the table exists before querying
            with connection.cursor() as cursor:
                table_names = connection.introspection.table_names(cursor)
                if 'converter_oscconfig' not in table_names:
                    # Migrations not yet applied, skip silently
                    return

            from .models import OSCConfig
            from .osc_service import osc_service

            for config in OSCConfig.objects.filter(auto_start=True):
                osc_service.start_config(config)
        except (OperationalError, ProgrammingError):
            # Database not ready yet (migrations pending)
            pass
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Auto-start failed: {e}")
