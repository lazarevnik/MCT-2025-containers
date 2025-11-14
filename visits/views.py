import os
from django.http import HttpResponse
from .models import Visit

def ping(request):
    ip = request.META.get('REMOTE_ADDR')
    Visit.objects.create(ip=ip)
    return HttpResponse("pong")

def visits(request):
    if os.getenv('DEV_MODE') == '1':
        return HttpResponse("-1")
    return HttpResponse(str(Visit.objects.count()))

def health(request):
    return HttpResponse("OK")