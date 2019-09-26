from typing import Dict, List
from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from tom_targets.models import Target
from .models import Instrument, Site


def _get_todays_target(site: Site) -> Dict:
    now = datetime.now()
    todays_target = Target.objects \
        .filter(targetextra__key='site', targetextra__value=site.code.lower()) \
        .filter(targetextra__key__contains='seasonal_start', targetextra__value__lte=now) \
        .filter(targetextra__key__contains='seasonal_end', targetextra__value__gte=now)
    assert(todays_target.count == 1, f"target_count: {todays_target.count}")
    return todays_target[0]


def _get_context_for_index(request: HttpRequest) -> Dict:
    # get today's targets for the context
    todays_target: Dict[str:Target] = {}
    for site, site_code in [(site, site.code) for site in Site.objects.all()]:
        todays_target[site_code] = _get_todays_target(site)

    context: Dict = {
        'sites': Site.objects.all(),
        'targets': todays_target,
    }
    return context


def index(request: HttpRequest) -> HttpResponse:
    context = _get_context_for_index(request)
    return render(request, 'calibrations/index.html', context)


def floyds_ogg(request: HttpRequest) -> HttpResponse:
    context = _get_context_for_index(request)
    return render(request, 'calibrations/index.html', context)


def floyds_coj(request: HttpRequest) -> HttpResponse:
    context = _get_context_for_index(request)
    return render(request, 'calibrations/index.html', context)

