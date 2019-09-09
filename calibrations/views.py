from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    context = {}
    return render(request, 'calibrations/index.html', context)


def index1(request):
    return HttpResponse(f"this is the beginning of the calibrations app: {request}")
