from typing import Dict, List

from django.shortcuts import render
from django.http import HttpResponse, HttpRequest


def index(request: HttpRequest) -> HttpResponse:
    context: Dict[str, List] = {
        'stuff_to_list': ['one', 'two', 'three', 'four']
    }
    return render(request, 'calibrations/index.html', context)
