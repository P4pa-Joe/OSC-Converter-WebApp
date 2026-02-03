from django import forms
from .models import OSCConfig, OSCDispatcher


class OSCConfigForm(forms.ModelForm):
    class Meta:
        model = OSCConfig
        fields = ['name', 'rx_ip', 'rx_port', 'auto_start']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rx_ip': forms.TextInput(attrs={'class': 'form-control'}),
            'rx_port': forms.NumberInput(attrs={'class': 'form-control'}),
            'auto_start': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OSCDispatcherForm(forms.ModelForm):
    class Meta:
        model = OSCDispatcher
        fields = ['osc_input', 'tx_ip', 'tx_port', 'osc_output', 'is_enabled']
        widgets = {
            'osc_input': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/osc/input'}),
            'tx_ip': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '127.0.0.1', 'value': '127.0.0.1'}),
            'tx_port': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '12321', 'value': '12321'}),
            'osc_output': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/osc/output'}),
            'is_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
