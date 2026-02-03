from django.apps import AppConfig
import os
import sys


class ConverterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'converter'

    def ready(self):
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
                self._start_auto_configs()
        else:
            # For gunicorn/wsgi: always run (RUN_MAIN not set)
            self._start_auto_configs()

    def _start_auto_configs(self):
        try:
            from .models import OSCConfig
            from .osc_service import osc_service

            for config in OSCConfig.objects.filter(auto_start=True):
                osc_service.start_config(config)
        except Exception as e:
            # Database might not be ready yet (migrations pending)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Auto-start failed: {e}")
