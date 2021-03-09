import logging

from django.conf import settings
from django.contrib import messages
from django.db import models
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from django.urls import reverse_lazy
from django.views.generic import DeleteView, DetailView, ListView, RedirectView, TemplateView
from django.views.generic.edit import FormView

from configdb.configdb_connections import ConfigDBInterface
from targeted_calibrations.forms import NRESCalibrationSubmissionForm
from tom_observations.models import DynamicCadence, ObservationGroup
from tom_targets.models import Target

logger = logging.getLogger(__name__)

configdb = ConfigDBInterface(settings.CONFIGDB_URL)  # TODO: rethink how we store this property


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

    # TODO: specify model = Target ; this override is unnecessary
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

        # target = kwargs['object']
        # extras = {key['name']: target.extra_fields.get(key['name'], '') for key in EXTRA_FIELDS if
        #           not key.get('hidden')}
        # context['extras'] = extras
        # context['target'] = target

        # insert url parameter(s) into the context
        context['instrument_type'] = self.kwargs.get('instrument_type', '')
        context['instrument_code'] = self.kwargs.get('instrument_code', '')
        context['target_id'] = self.kwargs.get('target_id', 1)

        context['kwargs'] = kwargs  # TODO: remove after debugging
        context['template_name'] = self.template_name  # TODO: remove after debugging

        return context


class NRESCalibrationsView(TemplateView):
    template_name = 'targeted_calibrations/nres_calibrations_view.html'

    def get_context_data(self, **kwargs):
        pass


class NRESCalibrationSubmissionView(FormView):
    form_class = NRESCalibrationSubmissionForm
    success_url = reverse_lazy('targeted_calibrations:nres_home')

    def form_invalid(self, form):
        messages.error(self.request, f'The form is invalid: {form.errors}.')
        logger.error(self.request, f'Invalid form submission for NRES cadence submission: {form.errors}.')
        return super().form_invalid(form)

    def _get_active_requested_nres_sites(self, requested_sites):
        """
        :return: list of site-code strings which are both active (SCHEDULABLE or COMMISSIONING) and requested by the form.
        """
        active_sites = []  # the sites with active (SCHEDULABLE or COMMISSIONING) NRES instruments
        for telcode, instruments in configdb.get_active_instruments_info(
                instrument_type=settings.NRES_INSTRUMENT_TYPE,
                include_commissioning=True).items():
            active_sites.append(instruments[0]['site'])

        active_requested_sites = [site for site in requested_sites if site in active_sites]
        return active_requested_sites

    def form_valid(self, form):
        """For each (configdb-approved) site, find the DynamicCadences that have the same
        target standard_type as the new (form-given) target and update them.
        """
        requested_site = form.cleaned_data['site']
        cadence_frequency = form.cleaned_data['frequency']
        target_id = form.cleaned_data['target']
        target = Target.objects.get(pk=target_id)

        # Sort out which sites are both requested and have scheduable/commissioning nres instruments
        requested_sites = settings.NRES_SITES  # handles the 'all' case
        if requested_site != 'all':
            requested_sites = [requested_site]
        active_requested_nres_sites = self._get_active_requested_nres_sites(requested_sites)

        # Get standard type of this dynamic cadence
        standard_type = target.targetextra_set.filter(key='standard_type').first().value
        # we have the target_id so we shouldn't need this
        targets_for_standard_type = Target.objects.filter(targetextra__key='standard_type',
                                                          targetextra__value=standard_type)
        # TODO: the standard_type should become one of the (arbitrary JSON) cadence_parameters

        # annotate the all the cadences with the target.id of their targets...
        dynamic_cadences = DynamicCadence.objects.annotate(
            target_id=Cast(KeyTextTransform('target_id', 'cadence_parameters'), models.IntegerField()))
        # ... so we can filter them (the dynamic cadences) down to the ones that match the standard_type
        dynamic_cadences = dynamic_cadences.filter(target_id__in=targets_for_standard_type)

        for site in active_requested_nres_sites:
            dynamic_cadences_for_site = dynamic_cadences.filter(cadence_parameters__site=site)  # TODO: must filter on standard_type also
            if dynamic_cadences_for_site.count() == 0:
                og = ObservationGroup.objects.create(name=f'NRES {standard_type} calibration for {site.upper()}')
                DynamicCadence.objects.create(
                    cadence_strategy='NRESCadenceStrategy',
                    cadence_parameters={
                        'target_id': target_id,
                        'cadence_frequency': cadence_frequency,
                        'site': site
                    },
                    observation_group=og,
                    active=True
                )
            for dc in dynamic_cadences_for_site:
                dc.cadence_parameters['target_id'] = target.id
                dc.cadence_parameters['cadence_frequency'] = cadence_frequency
                dc.save()
            # TODO: Should the next observation be cancelled and replaced?

        # report back to the user
        if active_requested_nres_sites:
            messages.success(
                self.request,
                (f'Created/updated {standard_type} cadences at {active_requested_nres_sites} '
                 f'with target {target} and frequency {cadence_frequency}.'))
        else:
            messages.warning(
                self.request,
                f'The requested site(s) ({requested_sites}) have no SCHEDULABLE or COMMISSIONING instruments.',)

        return super().form_valid(form)


class NRESCadencePlayPauseView(RedirectView):
    pattern_name = 'targeted_calibrations:nres_home'

    def get_redirect_url(self, *args, **kwargs):
        cadence_id = kwargs.pop('pk', None)
        active = self.request.GET.get('active', None)
        if active is not None:
            dc = DynamicCadence.objects.get(pk=cadence_id)
            dc.active = active
            dc.save()
        return super().get_redirect_url(*args, **kwargs)


class NRESCadenceDeleteView(DeleteView):
    model = DynamicCadence
    success_url = reverse_lazy('targeted_calibrations:nres_home')
    template_name = 'targeted_calibrations/dynamiccadence_confirm_delete.html'
