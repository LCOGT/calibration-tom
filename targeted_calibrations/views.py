import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView, TemplateView
from django.views.generic.edit import FormView

from configdb.configdb_connections import ConfigDBInterface
from tom_observations.models import DynamicCadence
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


# TODO: move this to a more appropriate class
class NRESCalibrationSubmissionForm(forms.Form):
    # site = forms.ChoiceField(choices=[('all', 'All'), ('cpt', 'cpt')])  # TODO: should be a ChoiceField
    frequency = forms.IntegerField(label=False, widget=forms.NumberInput(attrs={'placeholder': 'Frequency (hours)'}))
    target = forms.ChoiceField(  # Display standard type alongside target name
        choices=[(target.id,
                  f"{target.name} ({target.targetextra_set.filter(key='standard_type').first().value})")
                 for target in Target.objects.all()],
        label=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('targeted_calibrations:nres_submission')
        self.helper.layout = Layout(
            Row(
                Column('frequency'),
                Column('target'),
                Column(
                    ButtonHolder(
                        Submit('submit', 'Update or Create Cadence')
                    )
                )
            )
        )


class NRESCalibrationSubmissionView(FormView):
    form_class = NRESCalibrationSubmissionForm
    success_url = reverse_lazy('targeted_calibrations:nres_home')

    def form_invalid(self, form):
        messages.error(request, f'The form is invalid: {form.errors}.')
        logger.error(request, f'Invalid form submission for NRES cadence submission: {form.errors}.')
        return super().form_invalid(form)

    def form_valid(self, form):
        cadence_frequency = form.cleaned_data['frequency']
        target_id = form.cleaned_data['target']
        target = Target.objects.get(pk=target_id)
        standard_type = target.targetextra_set.filter(key='standard_type').first().value  # Get standard type of this dynamic cadence
        dynamic_cadences = DynamicCadence.objects.filter(  # Get DynamicCadences that match the standard type
            cadence_parameters__target_id__in=Target.objects.filter(targetextra__key='standard_type', targetextra__value=standard_type)  # TODO: get all dynamic cadences with targets of the matching standard type
        )
        for site in settings.NRES_SITES:  # TODO: exclude inactive configdb instruments (.get_active_nres_sites())
            dynamic_cadences_for_site = dynamic_cadences.filter(cadence_parameters__site=site)
            # if dynamic_cadences_for_site.count() == 0:
            #     # TODO: submit observation to get an ObservationRecord to start the cadence
            #     og = ObservationGroup.objects.create(name=f'Cadenced NRES {standard_type} calibrations for {site}')
            #     DynamicCadence.objects.create(
            #         cadence_strategy='NRESCadenceStrategy',
            #         cadence_parameters={
            #             'target_id': target_id,
            #             'cadence_frequency': cadence_frequency,
            #             'site': site
            #         },
            #         observation_group=og,
            #         active=True
            #     )
            for dc in dynamic_cadences_for_site:
                dc.cadence_parameters['target_id'] = target.id
                dc.cadence_parameters['cadence_frequency'] = cadence_frequency
                dc.save()

    # site, target standard_type

    # def post(self, request, *args, **kwargs):
    #     # update or submit cadence
    #     messages.success(request, 'POSTed successfully!')
    #     return super().post(request, args, kwargs)
