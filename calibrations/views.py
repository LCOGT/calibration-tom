from typing import Dict, List

from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from .models import Instrument, Site


def index(request: HttpRequest) -> HttpResponse:
    context: Dict[str, List] = {
        'stuff_to_list': ['one', 'two', 'three', 'four'],
        'sites': Site.objects.all(),
        'instruments': Instrument.objects.all(),
    }
    return render(request, 'calibrations/index.html', context)
