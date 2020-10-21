# from django.shortcuts import render

from django.views.generic import TemplateView


class NRESCalibrationsIndex(TemplateView):
    template_name = 'nres_calibrations/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        return context


class NRESInstrumentClassListView(TemplateView):
    """list of instruments for an instrument class
    """
    template_name = 'nres_calibrations/instrument_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        context['instruments'] = [
            {'name': 'nres01'},
            {'name': 'nres02'},
            {'name': 'nres03'},
            {'name': 'nres04'},
        ]
        return context


class NRESInstrumentTargetListView(TemplateView):
    """List of targets for a specific instrument
    """
    template_name = 'nres_calibrations/target_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        context['inst'] = kwargs['inst']
        context['targets'] = [
            {'id': 0,
             'name': 'target00',
             'active': False,
             'type': 'RV',
             },
            {'id': 1,
             'name': 'target01',
             'active': True,
             'type': 'RV',
             },
            {'id': 2,
             'name': 'target02',
             'active': False,
             'type': 'FLUX',
             },
        ]
        return context


class NRESInstrumentTargetDetailView(TemplateView):
    """Details of nres calibration target.
    """
    template_name = 'nres_calibrations/target_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        return context
