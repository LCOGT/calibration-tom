import requests

from typing import Dict, List
from datetime import datetime

from django.views.generic import FormView, TemplateView 
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest

from tom_targets.models import Target
from .models import Instrument, Site


class CalibrationSubmissionView(TemplateView):
    template_name = 'calibrations/index.html'

    def _get_todays_targets(site: Site) -> Dict:
        now = datetime.now()
        todays_targets = Target.objects \
            .filter(targetextra__key='site', targetextra__value=site.code.upper()) \
            .filter(targetextra__key__contains='seasonal_start', targetextra__value__lte=now) \
            .filter(targetextra__key__contains='seasonal_end', targetextra__value__gte=now)
        return todays_targets

    def get_context_data(self, **kwargs):
        todays_targets: Dict[str:Target] = {}
        for site, site_code in [(site, site.code) for site in Site.objects.all()]:
            todays_targets[site_code] = _get_todays_targets(site)

        # Get NRES instruments
        response = requests.get('http://configdb.lco.global/sites/')
        response.raise_for_status()


        context: Dict = {
            'sites': Site.objects.all(),
            'site_targets': todays_targets
        }
        return context


class CalibrationsCreateView(FormView):
    pass



# def floyds_ogg(request: HttpRequest) -> HttpResponse:
#     context = _get_context_for_index(request)
#     return render(request, 'calibrations/index.html', context)


# def floyds_coj(request: HttpRequest) -> HttpResponse:
#     context = _get_context_for_index(request)
#     return render(request, 'calibrations/index.html', context)

