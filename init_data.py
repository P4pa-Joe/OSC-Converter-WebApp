#!/usr/bin/python3
"""
Script d'initialisation - Crée une configuration par défaut avec les dispatchers du script original
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'osc_converter.settings')
django.setup()

from converter.models import OSCConfig, OSCDispatcher

def init_default_config():
    # Créer la config si elle n'existe pas
    config, created = OSCConfig.objects.get_or_create(
        name="Default",
        defaults={
            'rx_ip': '0.0.0.0',
            'rx_port': 9000,
        }
    )

    if created:
        print(f"Configuration créée: {config}")

        # Dispatchers par défaut (osc_input, tx_ip, tx_port, osc_output)
        default_dispatchers = [
            ("/ext/master/faderpos", "127.0.0.1", 12321, "/varset/masterLevel"),
            ("/ext/master/mute", "127.0.0.1", 12321, "/varset/masterMute"),
            ("/ext/rev/master/faderpos", "127.0.0.1", 12321, "/varset/reverbLevel"),
            ("/ext/rev/master/mute", "127.0.0.1", 12321, "/varset/reverbMute"),
            ("/1/volume2", "127.0.0.1", 12321, "/varset/TotalMix_AES_Volume"),
            ("/1/volume2Val", "127.0.0.1", 12321, "/varset/TotalMix_AES_VolumeVal"),
            ("/1/mute/1/2", "127.0.0.1", 12321, "/varset/TotalMix_AES_Mute"),
        ]

        for osc_input, tx_ip, tx_port, osc_output in default_dispatchers:
            disp = OSCDispatcher.objects.create(
                config=config,
                osc_input=osc_input,
                tx_ip=tx_ip,
                tx_port=tx_port,
                osc_output=osc_output
            )
            print(f"  Dispatcher créé: {disp}")
    else:
        print(f"Configuration existante: {config}")

if __name__ == '__main__':
    init_default_config()
    print("\nInitialisation terminée!")
