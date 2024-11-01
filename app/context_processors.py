from django.conf import settings

def base(request):
    return {
        'BASE': settings.BASE
    }
