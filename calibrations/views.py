from typing import Dict, List

from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from .models import Instrument, Site


def index(request: HttpRequest) -> HttpResponse:
    context: Dict[str, List] = {
        'sites': Site.objects.all(),
        'instrument_classes': ['FLOYDS']
    }
    return render(request, 'calibrations/index.html', context)


def floyds_ogg(request: HttpRequest) -> HttpResponse:
    context: Dict[str, List] = {
        'sites': Site.objects.all(),
        'instrument_classes': ['FLOYDS']
    }
    return render(request, 'calibrations/index.html', context)


def floyds_coj(request: HttpRequest) -> HttpResponse:
    context: Dict[str, List] = {
        'sites': Site.objects.all(),
        'instrument_classes': ['FLOYDS']
    }
    return render(request, 'calibrations/index.html', context)

