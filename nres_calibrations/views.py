# from django.shortcuts import render

from django.views.generic import TemplateView
from django.views.generic import ListView


class ExpertimentListView(ListView):
    template_name = 'targeted_calibrations/experiment_list_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging

#        context['instrument_types'] = [
#            {'code': '1M0-SCICAM-SINISTRO'},
#            {'code': '2M0-SCICAM-SPECTRAL'},
#            {'code': '0M4-SCICAM-SBIG'},
#            {'code': '2M0-FLOYDS-SCICAM'},
#            {'code': '1M0-NRES-SCICAM'},
#        ]
#        self.queryset = context['instrument_types']
        return context

    def get_queryset(self):
#        self.queryset = super().get_queryset()
        print(f'queryset: {self.queryset}')
        if self.queryset is None:
            pass
        queryset = [
            {'code': '1M0-SCICAM-SINISTRO'},
            {'code': '2M0-SCICAM-SPECTRAL'},
            {'code': '0M4-SCICAM-SBIG'},
            {'code': '2M0-FLOYDS-SCICAM'},
            {'code': '1M0-NRES-SCICAM'},
        ]

        return queryset


class NRESCalibrationsIndex(TemplateView):
    template_name = 'targeted_calibrations/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        context['instrument_types'] = [
            {'code': '1M0-SCICAM-SINISTRO'},
            {'code': '2M0-SCICAM-SPECTRAL'},
            {'code': '0M4-SCICAM-SBIG'},
            {'code': '2M0-FLOYDS-SCICAM'},
            {'code': '1M0-NRES-SCICAM'},
        ]
        return context


class NRESInstrumentClassListView(TemplateView):
    """list of instruments for an instrument class
    """
    template_name = 'targeted_calibrations/instrument_list.html'

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
    template_name = 'targeted_calibrations/target_list.html'

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
    template_name = 'targeted_calibrations/target_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        return context
