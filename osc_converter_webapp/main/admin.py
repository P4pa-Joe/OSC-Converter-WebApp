from django.contrib import admin
from .models import OSCConfig, OSCDispatcher


class OSCDispatcherInline(admin.TabularInline):
    model = OSCDispatcher
    extra = 1


@admin.register(OSCConfig)
class OSCConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'rx_ip', 'rx_port', 'auto_start']
    list_filter = ['auto_start']
    inlines = [OSCDispatcherInline]


@admin.register(OSCDispatcher)
class OSCDispatcherAdmin(admin.ModelAdmin):
    list_display = ['osc_input', 'tx_ip', 'tx_port', 'osc_output', 'is_enabled', 'config']
    list_filter = ['is_enabled', 'config']
    search_fields = ['osc_input', 'osc_output', 'tx_ip']
    list_select_related = ['config']
