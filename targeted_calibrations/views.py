# from django.shortcuts import render

from tom_targets.models import Target
from django.views.generic import ListView, DetailView


class InstrumentTypeListView(ListView):
    # if not overridden, template_name is <app name>/<model name>_list.html
    #  template_name = ''

    # if not overridden, the context_object_name is <model>_list (used in {% for ... in ... %} template tags
    #  context_object_name = ''
    template_name = 'targeted_calibrations/instrument_type_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        context['template_name'] = self.template_name

        return context

    def get_queryset(self):
        #        self.queryset = super().get_queryset()
        print(f'queryset: {self.queryset}')
        if self.queryset is None:
            pass
        queryset = [
            {'code': '1M0-SCICAM-SINISTRO',
             'name': '1m0-SciCam-Sinistro'},
            {'code': '2M0-SCICAM-SPECTRAL',
             'name': '2.0 meter Spectral'},
            {'code': '0M4-SCICAM-SBIG',
             'name': '0.4 meter SBIG'},
            {'code': '2M0-FLOYDS-SCICAM',
             'name': '2.0 meter FLOYDS'},
            {'code': '1M0-NRES-SCICAM',
             'name': '1.0 meter NRES'},
        ]

        return queryset


class InstrumentListView(ListView):
    # if not overridden, template_name is <app name>/<model name >_detail.html
    template_name = 'targeted_calibrations/instrument_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        context['template_name'] = self.template_name  # TODO: remove after debugging

        # insert url parameter(s) into the context
        context['instrument_type'] = self.kwargs.get('instrument_type', '')

        return context

    def get(self, request, *args, **kwargs):  # TODO: remove after debugging
        print(f'get args {args}')
        print(f'get kwargs {kwargs}')  # this is where the url params are
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        #        self.queryset = super().get_queryset()
        print(f'queryset: {self.queryset}')
        if self.queryset is None:
            pass
        queryset = [
            {'code': 'nres01',
             'state': 'MANUAL'},
            {'code': 'nres02',
             'state': 'MANUAL'},
            {'code': 'nres03',
             'state': 'STANDBY'},
            {'code': 'nres04',
             'state': 'MANUAL'},
        ]

        return queryset


class InstrumentTargetListView(ListView):
    # if not overridden, template_name is <app name>/<model name >_detail.html
    template_name = 'targeted_calibrations/instrument_target_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # add to the context here
        context['kwargs'] = kwargs  # TODO: remove after debugging
        context['template_name'] = self.template_name  # TODO: remove after debugging

        # insert url parameter(s) into the context
        context['instrument_type'] = self.kwargs.get('instrument_type', '')
        context['instrument_code'] = self.kwargs.get('instrument_code', '')

        return context

    def _get_target_list_for_instrument(self):
        target_list = [
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
        return target_list

    def get_queryset(self):
        target_list = self._get_target_list_for_instrument()

        # here, convert the target list in to a sane queryset
        queryset = target_list  # the degenerate case

        return queryset


class InstrumentTargetDetailView(DetailView):
    # if not overridden, template_name is <app name>/<model name >_detail.html
    template_name = 'targeted_calibrations/instrument_target_detail.html'
    model = Target

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # add to the context here

        # insert url parameter(s) into the context
        context['instrument_type'] = self.kwargs.get('instrument_type', '')
        context['instrument_code'] = self.kwargs.get('instrument_code', '')
        context['target_id'] = self.kwargs.get('target_id', 1)

        context['kwargs'] = kwargs  # TODO: remove after debugging
        context['template_name'] = self.template_name  # TODO: remove after debugging

        return context
