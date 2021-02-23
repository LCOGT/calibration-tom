from datetime import datetime, timedelta
from dateutil.parser import parse
import logging

from django import forms
from django.core.exceptions import ValidationError

from tom_observations.facilities.lco import LCOBaseObservationForm, LCOFacility
from tom_targets.models import Target

logger = logging.getLogger(__name__)


class NRESCalibrationForm(LCOBaseObservationForm):
    VALID_INSTRUMENT_CODES = ['1M0-NRES-SCICAM']  # TODO: Should this be in settings.py?
    VALID_PROPOSAL_CODES = ['ENG2017AB-001']  # TODO: Should this be in settings.py?
    # This needs to exist on both the NRESCalibrationForm and the NRESCadenceForm
    site = forms.CharField(widget=forms.HiddenInput())

    # TODO: nothing exists to ensure there's only one DynamicCadence per target/site
    # TODO: remove "Apply Observation Template" from target detail page
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # target_id will be in data dict if the form is bound, and in initial otherwise
        # NOTE: making this self.data.get('target_id', kwargs.get('initial', {})['target_id']) results in
        # a KeyError--is the second statement evaluated in conjunction with the first??
        target_id = self.data.get('target_id', kwargs.get('initial', {}).get('target_id'))
        target = Target.objects.get(id=target_id)

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
        self.fields['max_airmass'].initial = 2
        self.fields['start'].initial = datetime.now()
        self.fields['end'].widget = forms.HiddenInput()
        self.fields['end'].required = False  # Not required on the form, but must be submitted to LCO

        for field_name in ['period', 'jitter']:
            self.fields.pop(field_name)

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

    # def is_valid(self):
    #     super().is_valid()
    #     self.validate_at_facility()
    #     if self._errors:  # TODO: This should migrate up into tom_base
    #         logging.log(msg=f'Observation submission errors: {self._errors}', level=logging.WARNING)
    #     return not self._errors

    # In order to prevent the superclass' clean_end from being called, we override it and return the submitted value.
    # The end field is hidden and is not set by the form.
    def clean_end(self):
        return self.cleaned_data.get('end')

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('end'):
            start = parse(cleaned_data['start'])
            cleaned_data['end'] = datetime.strftime(start + timedelta(hours=24), '%Y-%m-%dT%H:%M:%S')

        if cleaned_data.get('cadence_strategy') is not None and not cleaned_data.get('cadence_frequency'):
            raise ValidationError('Repeating cadence must include a cadence frequency.')

        return cleaned_data

    def instrument_choices(self):
        return [(inst[0], inst[1]) for inst in super().instrument_choices() if inst[0] in self.VALID_INSTRUMENT_CODES]

    def layout(self):
        layout = super().layout()
        layout = layout[0]
        return layout

    def proposal_choices(self):
        return [(proposal[0], proposal[1])
                for proposal in super().proposal_choices()
                if proposal[0] in self.VALID_PROPOSAL_CODES]


class LCOCalibrationFacility(LCOFacility):
    name = 'LCO Calibrations'
    observation_forms = {
        'NRES': NRESCalibrationForm
    }
    EXCLUDED_FRAME_SUFFIXES = (
        'e91',  # e91 frames are NRES Autoguider images and are not desirable to download
    )

    def data_products(self, observation_id, product_id=None):
        products = []
        # TODO: fix how data products are handled
        # for frame in self._archive_frames(observation_id, product_id):
        #     if all(suffix for suffix in self.EXCLUDED_FRAME_SUFFIXES) not in frame['filename']:
        #         products.append({
        #             'id': frame['id'],
        #             'filename': frame['filename'],
        #             'created': parse(frame['DATE_OBS']),
        #             'url': frame['url']
        #         })
        return products
