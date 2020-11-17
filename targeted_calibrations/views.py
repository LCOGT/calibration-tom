# from django.shortcuts import render
import logging

from django.views.generic import ListView, DetailView
from tom_targets.models import Target

from calibration_tom.settings import CONFIGDB_URL
from configdb.configdb_connections import ConfigDBInterface

logger = logging.getLogger(__name__)

configdb = ConfigDBInterface(CONFIGDB_URL)  # TODO: rethink how we store this property


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

    def get_queryset(self) -> list:
        """
        Extract the a list of instrument_type dictionaries from configdb.
        Dictionary list elements should have 'code' and 'name' keys.

        :return: [{'name': "NAME", 'code': "code"}, ... ]
        """
        queryset = configdb.get_instruments_types('all')

        # process queryset here before returning

        return sorted(queryset, key=lambda item: item['code'])


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

    def get_queryset(self):
        """
        Construct queryset from configdb.
        :return:
        """
        instrument_type = self.kwargs['instrument_type']  # from URL via instance kwargs
        instrument_infos = configdb.get_active_instruments_info(instrument_type=instrument_type)

        queryset = []
        for instrument_info in instrument_infos.values():
            if len(instrument_info) != 1:
                logger.warning(f'configdb instrument_info has more than one list element: {instrument_info}')
            instrument_info = instrument_info[0]  # NOTE: I'm not sure why there is a 1-element list in instrument_info
            queryset.append({
                'code': instrument_info['code'],
                'site': instrument_info['site'],
                'enclosure': instrument_info['observatory'],  # this is really enclosure
                'telescope': instrument_info['telescope'],
                'state': instrument_info['state'],
            })

        return sorted(queryset, key=lambda item: item['code'])


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

    def _get_target_list_for_instrument(self):  # noqa
        """
        Return the Targets for the given instrument.
        (instrument_type and instrument_code available in instance self.kwargs).
        :return:
        """
        return Target.objects.all()  # noqa

    def get_queryset(self):
        targets = self._get_target_list_for_instrument()

        # here, convert the target list in to a sane queryset
        queryset = targets  # the degenerate case

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
