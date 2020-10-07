from datetime import datetime, timedelta

from django import forms
from django.core.exceptions import ValidationError

from tom_observations.facilities.lco import LCOBaseObservationForm, LCOFacility
from tom_targets.models import Target


class NRESCalibrationForm(LCOBaseObservationForm):
    VALID_INSTRUMENT_CODES = ['1M0-NRES-SCICAM']
    VALID_PROPOSAL_CODES = ['ENG2017AB-001']

    # TODO: remove end time from visible fields and default to one day window
    # TODO: remove "Apply Observation Template" from target detail page
    def __init__(self, *args, **kwargs):
        # target_id will be in a dict in args if the form is bound, and in initial otherwise
        target_id = kwargs.get('target_id', kwargs.get('initial')['target_id'])
        target = Target.objects.get(id=target_id)
        super().__init__(*args, **kwargs)
        # The first item in the tuple is the form value, the second is the display value
        self.fields['cadence_strategy'] = forms.ChoiceField(
            choices=[('', 'Once'), ('NRESCadenceStrategy', 'Repeating every')],
            required=False,
        )
        self.fields['cadence_frequency'] = forms.IntegerField(required=False, help_text='in hours', initial=120)
        self.fields['ipp_value'].initial = 1.05
        self.fields['filter'].initial = 'air'
        self.fields['exposure_time'].initial = target.targetextra_set.filter(key='exp_time').first().value
        self.fields['exposure_count'].initial = target.targetextra_set.filter(key='exp_count').first().value
        self.fields['max_airmass'].initial = 3
        self.fields['start'].initial = datetime.now()
        self.fields['end'].widget = forms.HiddenInput()

        # TODO: remove these fields, which requires ditching them from the layout
        # for field_name in ['period', 'jitter']:
        #     self.fields.pop(field_name)

    def _build_instrument_config(self):
        # According to ConfigDB, there are no available optical elements for NRES instruments.
        instrument_configs = super()._build_instrument_config()
        instrument_configs[0]['optical_elements'].pop('filter')
        # instrument_configs[0]['optical_elements']['slit'] = self.cleaned_data['filter']

        return instrument_configs

    def _build_location(self):
        """
        We override _build_location() because site is a hidden API option that is not normally
        included in end-user LCO submissions.
        """
        location = super()._build_location()
        location['site'] = self.cleaned_data['site']
        return location

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['end'] = datetime.strftime(datetime.now() + timedelta(hours=72), '%Y-%m-%dT%H:%M:%S')  # TODO: modify timedelta to 24 hours

        if cleaned_data.get('cadence_strategy') is not None and not cleaned_data.get('cadence_frequency'):
            raise ValidationError('Repeating cadence must include a cadence frequency.')

        return cleaned_data

    def instrument_choices(self):
        return [(inst[0], inst[1]) for inst in super().instrument_choices() if inst[0] in self.VALID_INSTRUMENT_CODES]

    def layout(self):
        # TODO: Fix layout to be better
        layout = super().layout()
        return layout

    def proposal_choices(self):
        # TODO: decide whether to limit proposal choices or prefill with initial value
        # return super().proposal_choices()
        return [(proposal[0], proposal[1])
                for proposal in super().proposal_choices()
                if proposal[0] in self.VALID_PROPOSAL_CODES]


class LCOCalibrationFacility(LCOFacility):
    name = 'LCO Calibrations'
    observation_forms = {
        'NRES': NRESCalibrationForm
    }
