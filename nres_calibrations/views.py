# from django.shortcuts import render

from django.views.generic import TemplateView


class NRESCalibrationsIndex(TemplateView):
    template_name = 'nres_calibrations/index.html'


class NRESInstrumentClassListView(TemplateView):
    """list of instruments for an instrument class
    """
    template_name = 'nres_calibrations/instrument_list.html'


class NRESInstrumentTargetListView(TemplateView):
    """List of targets for a specific instrument
    """
    template_name = 'nres_calibrations/target_list.html'


class NRESInstrumentTargetDetailView(TemplateView):
    """Details of nres calibration target.
    """
    template_name = 'nres_calibrations/target_detail.html'
