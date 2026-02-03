from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count
from datetime import datetime

from .models import OSCConfig, OSCDispatcher
from .forms import OSCConfigForm, OSCDispatcherForm
from .osc_service import osc_service


def dashboard(request):
    """Main page with service status and configurations"""
    configs = OSCConfig.objects.annotate(dispatcher_count=Count('dispatchers'))
    status = osc_service.get_status()
    running_configs = status['running_configs']

    return render(request, 'converter/dashboard.html', {
        'configs': configs,
        'status': status,
        'running_configs': running_configs,
    })


def config_edit(request, pk=None):
    """Edit or create a configuration"""
    if pk:
        config = get_object_or_404(OSCConfig, pk=pk)
    else:
        config = None

    if request.method == 'POST':
        form = OSCConfigForm(request.POST, instance=config)
        if form.is_valid():
            config = form.save()
            messages.success(request, 'Configuration saved')
            return redirect('dashboard')
    else:
        form = OSCConfigForm(instance=config)

    return render(request, 'converter/config_form.html', {
        'form': form,
        'config': config,
    })


def config_delete(request, pk):
    """Delete a configuration"""
    config = get_object_or_404(OSCConfig, pk=pk)
    if request.method == 'POST':
        config.delete()
        messages.success(request, 'Configuration deleted')
    return redirect('dashboard')


def dispatchers(request, config_pk):
    """Manage dispatchers for a configuration"""
    config = get_object_or_404(OSCConfig, pk=config_pk)
    dispatcher_list = config.dispatchers.all()

    if request.method == 'POST':
        form = OSCDispatcherForm(request.POST)
        if form.is_valid():
            dispatcher = form.save(commit=False)
            dispatcher.config = config
            dispatcher.save()
            messages.success(request, 'Dispatcher added')
            return redirect('dispatchers', config_pk=config_pk)
    else:
        form = OSCDispatcherForm()

    return render(request, 'converter/dispatchers.html', {
        'config': config,
        'dispatchers': dispatcher_list,
        'form': form,
    })


def dispatcher_edit(request, pk):
    """Edit a dispatcher"""
    dispatcher = get_object_or_404(OSCDispatcher, pk=pk)

    if request.method == 'POST':
        form = OSCDispatcherForm(request.POST, instance=dispatcher)
        if form.is_valid():
            form.save()
            messages.success(request, 'Dispatcher updated')
            return redirect('dispatchers', config_pk=dispatcher.config.pk)
    else:
        form = OSCDispatcherForm(instance=dispatcher)

    return render(request, 'converter/dispatcher_form.html', {
        'form': form,
        'dispatcher': dispatcher,
    })


def dispatcher_delete(request, pk):
    """Delete a dispatcher"""
    dispatcher = get_object_or_404(OSCDispatcher, pk=pk)
    config_pk = dispatcher.config.pk
    if request.method == 'POST':
        dispatcher.delete()
        messages.success(request, 'Dispatcher deleted')
    return redirect('dispatchers', config_pk=config_pk)


@require_POST
def service_start(request):
    """Start OSC service (deprecated)"""
    if osc_service.start():
        messages.success(request, 'Service started')
    else:
        messages.error(request, 'Error starting service')
    return redirect('dashboard')


@require_POST
def service_start_config(request, config_pk):
    """Start a specific configuration"""
    config = get_object_or_404(OSCConfig, pk=config_pk)

    if osc_service.start_config(config):
        messages.success(request, f'{config.name} started')
    else:
        messages.error(request, f'Error starting {config.name}')
    return redirect('dashboard')


@require_POST
def service_stop_config(request, config_pk):
    """Stop a specific configuration"""
    config = get_object_or_404(OSCConfig, pk=config_pk)

    if osc_service.stop_config(config_pk):
        messages.success(request, f'{config.name} stopped')
    else:
        messages.error(request, f'Error stopping {config.name}')
    return redirect('dashboard')


@require_POST
def service_restart_config(request, config_pk):
    """Restart a specific configuration"""
    config = get_object_or_404(OSCConfig, pk=config_pk)

    if osc_service.restart_config(config):
        messages.success(request, f'{config.name} restarted')
    else:
        messages.error(request, f'Error restarting {config.name}')
    return redirect('dashboard')


@require_POST
def service_stop(request):
    """Stop all OSC services"""
    osc_service.stop_all()
    messages.success(request, 'All services stopped')
    return redirect('dashboard')


@require_POST
def service_restart(request):
    """Restart OSC service (deprecated)"""
    if osc_service.restart():
        messages.success(request, 'Service restarted')
    else:
        messages.error(request, 'Error restarting service')
    return redirect('dashboard')


def service_status(request):
    """API: Service status (for AJAX)"""
    status = osc_service.get_status()

    # Convert config_pk keys to strings for JSON
    logs_by_config = {str(k): v for k, v in status.get('logs_by_config', {}).items()}

    return JsonResponse({
        'running_configs': status['running_configs'],
        'logs_by_config': logs_by_config,
        'global_logs': status.get('global_logs', []),
    })


@require_POST
def dispatcher_test(request, pk):
    """Send a test message for a dispatcher"""
    from pythonosc import udp_client
    import json

    dispatcher = get_object_or_404(OSCDispatcher, pk=pk)

    try:
        data = json.loads(request.body)
        value = data.get('value', 0)

        # Convertir en float si possible
        try:
            value = float(value)
        except (ValueError, TypeError):
            pass

        client = udp_client.SimpleUDPClient(dispatcher.tx_ip, dispatcher.tx_port)
        client.send_message(dispatcher.osc_output, value)

        osc_service._log(f"[Test] {dispatcher.tx_ip}:{dispatcher.tx_port} @ {dispatcher.osc_output} = {value}")

        return JsonResponse({'success': True, 'message': f'Message envoyé: {dispatcher.osc_output} = {value}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


def export_logs(request):
    """Export logs as .txt file"""
    from .models import OSCConfig

    status = osc_service.get_status()
    logs_by_config = status.get('logs_by_config', {})

    lines = []
    for config_pk, logs in logs_by_config.items():
        try:
            config = OSCConfig.objects.get(pk=config_pk)
            config_name = config.name
        except OSCConfig.DoesNotExist:
            config_name = f"Config {config_pk}"

        lines.append(f"=== {config_name} ===")
        lines.extend(logs)
        lines.append("")

    content = '\n'.join(lines)
    filename = f"osc_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# =============================================================================
# Export / Import
# =============================================================================

def export_all_configs(request):
    """Export all configurations and dispatchers as JSON"""
    import json

    data = {
        'version': 1,
        'export_type': 'full',
        'exported_at': datetime.now().isoformat(),
        'configurations': []
    }

    for config in OSCConfig.objects.all():
        config_data = {
            'name': config.name,
            'rx_ip': config.rx_ip,
            'rx_port': config.rx_port,
            'auto_start': config.auto_start,
            'dispatchers': []
        }

        for disp in config.dispatchers.all():
            config_data['dispatchers'].append({
                'osc_input': disp.osc_input,
                'osc_output': disp.osc_output,
                'tx_ip': disp.tx_ip,
                'tx_port': disp.tx_port,
                'is_enabled': disp.is_enabled,
            })

        data['configurations'].append(config_data)

    content = json.dumps(data, indent=2)
    filename = f"osc_config_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    response = HttpResponse(content, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def export_config_dispatchers(request, config_pk):
    """Export dispatchers for a specific configuration as JSON"""
    import json

    config = get_object_or_404(OSCConfig, pk=config_pk)

    data = {
        'version': 1,
        'export_type': 'dispatchers',
        'exported_at': datetime.now().isoformat(),
        'config_name': config.name,
        'dispatchers': []
    }

    for disp in config.dispatchers.all():
        data['dispatchers'].append({
            'osc_input': disp.osc_input,
            'osc_output': disp.osc_output,
            'tx_ip': disp.tx_ip,
            'tx_port': disp.tx_port,
            'is_enabled': disp.is_enabled,
        })

    content = json.dumps(data, indent=2)
    filename = f"osc_dispatchers_{config.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    response = HttpResponse(content, content_type='application/json')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@require_POST
def import_configs(request):
    """Import configurations and/or dispatchers from JSON file"""
    import json

    if 'file' not in request.FILES:
        messages.error(request, 'No file provided')
        return redirect('dashboard')

    try:
        file = request.FILES['file']
        data = json.load(file)

        export_type = data.get('export_type', 'full')

        if export_type == 'full':
            # Import full configuration
            imported_configs = 0
            imported_dispatchers = 0

            for config_data in data.get('configurations', []):
                # Create or update config
                config, created = OSCConfig.objects.update_or_create(
                    name=config_data['name'],
                    defaults={
                        'rx_ip': config_data.get('rx_ip', '0.0.0.0'),
                        'rx_port': config_data.get('rx_port', 9000),
                        'auto_start': config_data.get('auto_start', False),
                    }
                )
                imported_configs += 1

                # Import dispatchers
                for disp_data in config_data.get('dispatchers', []):
                    OSCDispatcher.objects.create(
                        config=config,
                        osc_input=disp_data['osc_input'],
                        osc_output=disp_data['osc_output'],
                        tx_ip=disp_data.get('tx_ip', '127.0.0.1'),
                        tx_port=disp_data.get('tx_port', 9000),
                        is_enabled=disp_data.get('is_enabled', True),
                    )
                    imported_dispatchers += 1

            messages.success(request, f'Imported {imported_configs} configuration(s) and {imported_dispatchers} dispatcher(s)')

        elif export_type == 'dispatchers':
            messages.error(request, 'Use the dispatchers page to import dispatchers for a specific configuration')

        return redirect('dashboard')

    except json.JSONDecodeError:
        messages.error(request, 'Invalid JSON file')
        return redirect('dashboard')
    except Exception as e:
        messages.error(request, f'Import error: {str(e)}')
        return redirect('dashboard')


@require_POST
def import_dispatchers(request, config_pk):
    """Import dispatchers from JSON file into a specific configuration"""
    import json

    config = get_object_or_404(OSCConfig, pk=config_pk)

    if 'file' not in request.FILES:
        messages.error(request, 'No file provided')
        return redirect('dispatchers', config_pk=config_pk)

    try:
        file = request.FILES['file']
        data = json.load(file)

        dispatchers_data = data.get('dispatchers', [])

        # Also support full export format
        if data.get('export_type') == 'full':
            # Find the first configuration's dispatchers
            configs = data.get('configurations', [])
            if configs:
                dispatchers_data = configs[0].get('dispatchers', [])

        imported = 0
        for disp_data in dispatchers_data:
            OSCDispatcher.objects.create(
                config=config,
                osc_input=disp_data['osc_input'],
                osc_output=disp_data['osc_output'],
                tx_ip=disp_data.get('tx_ip', '127.0.0.1'),
                tx_port=disp_data.get('tx_port', 9000),
                is_enabled=disp_data.get('is_enabled', True),
            )
            imported += 1

        messages.success(request, f'Imported {imported} dispatcher(s)')
        return redirect('dispatchers', config_pk=config_pk)

    except json.JSONDecodeError:
        messages.error(request, 'Invalid JSON file')
        return redirect('dispatchers', config_pk=config_pk)
    except Exception as e:
        messages.error(request, f'Import error: {str(e)}')
        return redirect('dispatchers', config_pk=config_pk)
