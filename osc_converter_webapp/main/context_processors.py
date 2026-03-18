from django.conf import settings


def app_version(request):
    return {
        'APP_VERSION': settings.APP_VERSION,
        'DEVELOPER_NAME': getattr(settings, 'DEVELOPER_NAME', ''),
        'DEVELOPER_EMAIL': getattr(settings, 'DEVELOPER_EMAIL', ''),
        'DEVELOPER_GITHUB': getattr(settings, 'DEVELOPER_GITHUB', ''),
    }
