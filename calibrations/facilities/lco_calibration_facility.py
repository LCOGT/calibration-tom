from datetime import datetime, timedelta
from dateutil.parser import parse
import logging

from django import forms
from django.core.exceptions import ValidationError
from tom_observations.facilities.lco import LCOBaseObservationForm, LCOFacility
from tom_targets.models import Target

import configdb.site

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


class LCOCalibrationForm(LCOBaseObservationForm):
    # TODO: make a proper super-class out of this LCOCalibrationForm

    VALID_INSTRUMENT_CODES = ['1M0-NRES-SCICAM']  # TODO: Should this be in settings.py?
    VALID_PROPOSAL_CODES = ['ENG2017AB-001', 'NRES standards']  # TODO: Should this be in settings.py?
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

        exposure_time = target.targetextra_set.filter(key='exp_time').first()
        if exposure_time:
            self.fields['exposure_time'].initial = exposure_time.value

        exposure_count = target.targetextra_set.filter(key='exp_count').first()
        if exposure_count:
            self.fields['exposure_count'].initial = exposure_count.value

        min_lunar_distance = target.targetextra_set.filter(key='min_lunar_distance').first()
        if min_lunar_distance is not None:
            self.fields['min_lunar_distance'].initial = min_lunar_distance.value

        self.fields['max_airmass'].initial = 2
        self.fields['start'].initial = datetime.now()
        self.fields['end'].widget = forms.HiddenInput()
        self.fields['end'].required = False  # Not required on the form, but must be submitted to LCO

        for field_name in ['period', 'jitter', 'filter']:
            self.fields.pop(field_name)

    def _build_instrument_config(self):
        # According to ConfigDB, there are no available optical elements for NRES instruments.
        instrument_configs = []
        instrument_configs.append({
            'exposure_count': self.cleaned_data['exposure_count'],
            'exposure_time': self.cleaned_data['exposure_time']
        })
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

    def observation_payload(self):
        payload = super().observation_payload()
        logger.info(f'Observation request to be submitted to LCO: {payload}')
        return payload


class LCOCalibrationFacility(LCOFacility):
    name = 'LCO Calibrations'

    # these key-values appear as tabs in the Observations/create template
    observation_forms = {
        'NRES': LCOCalibrationForm,
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
