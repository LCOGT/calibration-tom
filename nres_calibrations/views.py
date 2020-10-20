from django.shortcuts import render

from django.views.generic import TemplateView

# Create your views here.


class NRESCalibrationsIndex(TemplateView):
    template_name = 'nres_calibrations/index.html'


class NRESInstrumentTargetListView():
    pass


class NRESInstrumentTargetDetailView():
    pass