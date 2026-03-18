from django.db import models


class OSCConfig(models.Model):
    """Configuration principale du serveur OSC"""
    name = models.CharField(max_length=100, default="Default", verbose_name="Nom")
    rx_ip = models.GenericIPAddressField(default="0.0.0.0", verbose_name="IP RX (écoute)")
    rx_port = models.PositiveIntegerField(default=9000, verbose_name="Port RX")
    auto_start = models.BooleanField(default=False, verbose_name="Auto-start")
    show_unmapped = models.BooleanField(default=False, verbose_name="Show unmapped logs")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration OSC"
        verbose_name_plural = "Configurations OSC"

    def __str__(self):
        return f"{self.name} - {self.rx_ip}:{self.rx_port}"


class OSCDispatcher(models.Model):
    """Mapping des adresses OSC"""
    config = models.ForeignKey(OSCConfig, on_delete=models.CASCADE, related_name='dispatchers')
    osc_input = models.CharField(max_length=255, verbose_name="Adresse OSC (entrée)")
    osc_output = models.CharField(max_length=255, verbose_name="Adresse OSC (sortie)")
    tx_ip = models.GenericIPAddressField(default="127.0.0.1", verbose_name="IP destination")
    tx_port = models.PositiveIntegerField(default=9000, verbose_name="Port destination")
    is_enabled = models.BooleanField(default=True, verbose_name="Activé")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Dispatcher OSC"
        verbose_name_plural = "Dispatchers OSC"
        ordering = ['osc_input']

    def __str__(self):
        status = "✓" if self.is_enabled else "✗"
        return f"{status} {self.osc_input} → {self.tx_ip}:{self.tx_port}{self.osc_output}"
