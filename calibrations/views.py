from typing import Dict

from django.shortcuts import render
from django.http import HttpResponse, HttpRequest


def index(request: HttpRequest) -> HttpResponse:
    context: Dict[str, str] = {}
    return render(request, 'calibrations/index.html', context)
