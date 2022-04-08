import logging

from datetime import datetime
from io import StringIO
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, QueryDict, StreamingHttpResponse
from django.forms import HiddenInput
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.utils.text import slugify
from django.utils.safestring import mark_safe
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic import RedirectView, TemplateView, View
from django_filters.views import FilterView

from guardian.mixins import PermissionListMixin
from guardian.shortcuts import get_objects_for_user, get_groups_with_perms, assign_perm

from tom_common.hints import add_hint
from tom_common.hooks import run_hook

from tom_observations.observation_template import ApplyObservationTemplateForm
from tom_observations.models import ObservationTemplate

from configdb.configdb_connections import ConfigDBInterface

from network.groups import (
    add_all_to_group, add_selected_to_group, remove_all_from_group, remove_selected_from_group,
    move_all_to_group, move_selected_to_group
)
from network.models import Instrument, InstrumentList
from network.utils import import_instruments, export_instruments

logger = logging.getLogger(__name__)

configdb = ConfigDBInterface(settings.CONFIGDB_URL)  # TODO: rethink how we store this property


class InstrumentListView(ListView):
    """
    View for listing instruments in the Calibration-TOM. Requires authorization.
    """
    template_name = 'network/instrument_list.html'
    #paginate_by = 25
    #strict = False
    model = Instrument
    #filterset_class = InstrumentFilter
    #ordering = ['-created']

    #def get_context_data(self, *args, **kwargs):
    #def get_context_data(self, **kwargs):
    #    """
    #    Adds the number of instruments visible, the available ``InstrumentList`` objects if the user is authenticated, and
    #    the query string to the context object.
 
    #    :returns: context dictionary
    #    :rtype: dict
    #    """
    #    context = super().get_context_data(*args, **kwargs)
    #    context = super().get_context_data(**kwargs)
    #    context['instrument_count'] = context['paginator'].count
    #    # hide instrument group list if user not logged in
    #    context['groups'] = (InstrumentList.objects.all()
    #                            if self.request.user.is_authenticated
    #                            else InstrumentList.objects.none())
    #    context['query_string'] = self.request.META['QUERY_STRING']

    #    # add to the context here
    #    context['kwargs'] = kwargs  # TODO: remove after debugging
    #    context['template_name'] = self.template_name

        # insert url parameter(s) into the context
    #    context['instrument_type'] = self.kwargs.get('instrument_type', '')

    #    return context

    #def get_queryset(self) -> list:
    #def get_queryset(self):
        #"""
        #Extract the a list of instrument_type dictionaries from configdb.
        #Dictionary list elements should have 'code' and 'name' keys.

        #:return: [{'name': "NAME", 'code': "code"}, ... ]
        #"""
        #instrument_type = self.kwargs['instrument_type']
        #instrument_infos = configdb.get_active_instruments_info(instrument_type=instrument_type)

        #queryset = []
        #for instrument_info in instrument_infos.values():
        #    if len(instrument_info) != 1:
        #        logger.warning(f'configdb instrument_info has more than one list element: {instrument_info}')
        #    instrument_info = instrument_info[0]  # NOTE: I'm not sure why there is a 1-element list in instrument_info
        #    queryset.append({
        #        'code': instrument_info['code'],
        #        'site': instrument_info['site'],
        #        'enclosure': instrument_info['observatory'],  # this is really enclosure
        #        'telescope': instrument_info['telescope'],
        #        'state': instrument_info['state'],
        #    })

        #return sorted(queryset, key=lambda item: item['code'])

    #    queryset = configdb.get_instruments_types('all')

    #    # process queryset here before returning

    #    return sorted(queryset, key=lambda item: item['code'])


class InstrumentDetailView(DetailView):
    """
    View that handles the display of the instrument details. Requires authorization.
    """
    #permission_required = 'network.view_instrument'
    model = Instrument

    def get_context_data(self, *args, **kwargs):
        """
        Adds the ``DataProductUploadForm`` to the context and prepopulates the hidden fields.

        :returns: context object
        :rtype: dict
        """
        context = super().get_context_data(*args, **kwargs)
        observation_template_form = ApplyObservationTemplateForm(initial={'instrument': self.get_object()})
        if any(self.request.GET.get(x) for x in ['observation_template', 'cadence_strategy', 'cadence_frequency']):
            initial = {'instrument': self.object}
            initial.update(self.request.GET)
            observation_template_form = ApplyObservationTemplateForm(
                initial=initial
            )
        observation_template_form.fields['instrument'].widget = HiddenInput()
        context['observation_template_form'] = observation_template_form
        return context

    def get(self, request, *args, **kwargs):
        """
        Handles the GET requests to this view. If update_status is passed into the query parameters, calls the
        updatestatus management command to query for new statuses for ``ObservationRecord`` objects associated with this
        instrument.

        :param request: the request object passed to this view
        :type request: HTTPRequest
        """
        update_status = request.GET.get('update_status', False)
        if update_status:
            if not request.user.is_authenticated:
                return redirect(reverse('login'))
            instrument_id = kwargs.get('pk', None)
            out = StringIO()
            call_command('updatestatus', instrument_id=instrument_id, stdout=out)
            messages.info(request, out.getvalue())
            add_hint(request, mark_safe(
                              'Did you know updating observation statuses can be automated? Learn how in'
                              '<a href=https://tom-toolkit.readthedocs.io/en/stable/customization/automation.html>'
                              ' the docs.</a>'))
            return redirect(reverse('network:detail', args=(instrument_id,)))

        obs_template_form = ApplyObservationTemplateForm(request.GET)
        if obs_template_form.is_valid():
            obs_template = ObservationTemplate.objects.get(pk=obs_template_form.cleaned_data['observation_template'].id)
            obs_template_params = obs_template.parameters
            obs_template_params['cadence_strategy'] = request.GET.get('cadence_strategy', '')
            obs_template_params['cadence_frequency'] = request.GET.get('cadence_frequency', '')
            params = urlencode(obs_template_params)
            return redirect(
                reverse('tom_observations:create',
                        args=(obs_template.facility,)) + f'?instrument_id={self.get_object().id}&' + params)

        return super().get(request, *args, **kwargs)


class InstrumentGroupView(PermissionListMixin, ListView):
    """
    View that handles the display of ``InstrumentList`` objects, also known as instrument groups. Requires authorization.
    """
    #permission_required = 'network.view_instrumentlist'
    template_name = 'network/instrument_group.html'
    model = InstrumentList
    paginate_by = 25

