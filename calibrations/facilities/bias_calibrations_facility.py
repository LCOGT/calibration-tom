
import logging
from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, HTML, Layout, Row, Submit
from django import forms
from django.conf import settings
from tom_observations.facilities.lco import LCOBaseObservationForm, LCOFacility
from tom_observations.widgets import FilterField

from configdb.configdb_connections import ConfigDBInterface
# from calibrations.fields import FilterMultiValueField
# from calibrations.models import Filter

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


def enum_to_choices(emum_class) -> [()]:
    """
    #Turn an enum.Enum into a list of 2-tuples suitable for the forms.ChoiceField.choices parameter
    
    return [(e.value, e.name) for e in emum_class]
    """
# TODO: clean up unnecessary superclass overrides

# Diffusers, Slits, and Groups were part of the CLI of the calibration_utils submit_calibration script


class BiasCalibrationsManualSubmissionForm(LCOBaseObservationForm):
    """
    Form for submission of bias observations to imagers.

    This is loosely based on the options to the calibration_util submit_calibration script.
    """

    config_db = ConfigDBInterface(settings.CONFIGDB_URL)  # CONFIGDB_URL is set in calibration_tom/settings.py

    # set up the self.fields dict of form.xFields; dict key is property name (i.e. 'site')
    site = forms.ChoiceField(required=True,  # choices=enum_to_choices(SiteCode), # enum_to_choices is never used
                             choices=[],
                             label='Site')
    enclosure = forms.ChoiceField(choices=[])

    telescope = forms.ChoiceField(choices=[])  # TODO: populate telescope choices from enclosure choice

    instrument = forms.ChoiceField(choices=[])  # TODO: populate instrument choices from telescope choice

    readout_mode = forms.ChoiceField(choices=[])  # TODO: populate readout_mode choices from telescope choice

    filter = forms.ChoiceField(choices=[])  # TODO: populate filter choices from telescope choice

    diffusers = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    g_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    r_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    i_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    z_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])

    # start_time = forms.CharField(initial=datetime.utcnow(),
    #                              widget=forms.DateTimeInput(attrs={'type': 'datetime', 'format': '%Y-%m-%d $H:%M:%S'}),
    #                              help_text="input format = %Y-%m-%d %H:%M:%S")

    # end_time = forms.CharField(widget=forms.DateTimeInput(attrs={'type': 'datetime', 'format': '%Y-%m-%d %H:%M:%S'}),
    #                            help_text="input format = %Y-%m-%d %H:%M:%S")

    exposure_count = forms.IntegerField(widget=forms.NumberInput(attrs={'type': 'integer'}), help_text="minimum = 1")

    # exposure_time = forms.FloatField(widget=forms.NumberInput(attrs={'type': 'integer'}), help_text="seconds")

    # Save this as an example of how the label can be displayed on the form.
    # target_id = forms.ChoiceField(required=True,
    #                              # these choices must be defined at runtime (after the database is accessible)
    #                              choices=[('No targets found in database', 'No targets found in database')],
    #                              label='This label is for target selection.')

    def enclosure_choices(self):
        enclosures = set()

        for site in self.config_db.site_info:
            for enclosure in site['enclosure_set']:
                enclosures.add(enclosure['code'])

        return sorted([(e, e) for e in enclosures], key=lambda enclosure_tuple: enclosure_tuple[0])

    def instrument_granular_choices(self):
        instruments = set()

        for dome_values in self.config_db.get_active_instruments_info().values():
            for instrument_index in dome_values:
                instruments.add((instrument_index['code'], instrument_index['code']))

        return sorted(instruments)

    def readout_mode_choices(self):
        readout_modes = set()
    
        for active_instrument_values in self.config_db.get_active_instruments_info().values():
            for instrument_value in active_instrument_values:
                for readout_mode_details in instrument_value['named_readout_modes']:
                    readout_modes.add((readout_mode_details['code'], readout_mode_details['name']))
    
        return sorted(readout_modes)

    def optical_element_choices(self):
        optical_elements = set()
    
        for active_instrument_values in self.config_db.get_active_instruments_info().values():
            for instrument_value in active_instrument_values:
                for optical_element_higher in instrument_value['optical_elements']:
                    for optical_element_lower in optical_element_higher['optical_elements']:
                        optical_elements.add((optical_element_lower['code'], optical_element_lower['code']))
    
        return sorted(optical_elements)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set up the form field choices that must be assigned at run-time (not when byte-compiling the class definition)

        self.fields['site'].choices = [(site['code'], site['code']) for site in self.config_db.site_info]
        self.fields['enclosure'].choices = self.enclosure_choices()
        self.fields['telescope'].choices = sorted(set([(dome.split('.')[-1], dome.split('.')[-1]) for dome, _ in self.config_db.get_active_instruments_info().items()]))
        self.fields['instrument'].choices = self.instrument_granular_choices()
        self.fields['readout_mode'].choices = self.readout_mode_choices()
        self.fields['filter'].choices = self.optical_element_choices()

        # Add constant fields for Biases
        self.fields['start'].initial = datetime.utcnow()
        self.fields['start'].widget = forms.DateTimeInput(attrs={'type': 'datetime', 'format': '%Y-%m-%d $H:%M:%S'})
        self.fields['end'].initial = datetime.utcnow()
        self.fields['end'].widget = forms.HiddenInput()
        self.fields['name'].initial = 'LCOGT'
        self.fields['name'].widget = forms.HiddenInput()
        self.fields['proposal'].choices = [('calibrate', 'calibrate')]
        self.fields['proposal'].initial = 'calibrate'
        self.fields['proposal'].widget = forms.HiddenInput()
        self.fields['ipp_value'].initial = 1.0
        self.fields['ipp_value'].widget = forms.HiddenInput()
        self.fields['observation_mode'].initial = 'NORMAL'
        self.fields['observation_mode'].widget = forms.HiddenInput()
        self.fields['exposure_time'].min_value = 0.0
        self.fields['exposure_time'].initial = 0.0
        self.fields['exposure_time'].widget = forms.HiddenInput()
        self.fields['max_airmass'].initial = 20
        self.fields['max_airmass'].widget = forms.HiddenInput()

        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # TODO: define 'nres_calibrations:imager_submission'
        # self.helper.form_action = reverse('nres_calibrations:imager_submission')

        # TODO: until we have cadences, we don't need a cadence_frequency in this form
        # if 'cadence_frequency' in self.fields:
        #    self.fields['cadence_frequency'].required = False

        self.helper.layout = Layout(
            HTML("<hr/>"),  # This is the horizontal line at the top of the form.
            # List defaults at the top.
            HTML("Defaults:<br>"),
            HTML("target =  Bias target (HA=1, DEC=0).<br>"),
            HTML("proposal =  calibrate<br>"),
            HTML("observation mode =  Normal<br>"),
            HTML("IPP =  1.0<br>"),
            HTML("exposure time =  0<br>"),
            HTML("maximum airmass = 20.0<br>"),
            HTML("minimum lunar distance = 0<br>"),
            HTML("<hr/>"),
            self.common_layout,

            # HTML("<hr/>"),  # Site.Enclosure.Telescope.Instrument section
            Row(Column('site'), Column('enclosure'), Column('telescope'), Column('instrument_type'),
                Column('instrument')),

            Row(Column('readout_mode'), Column('filter'), Column('exposure_count')),

            'start',
            # 'end_time',

            # HTML("<hr/>"),  # new Filter section
            # *tuple([Row(Column(f.name)) for f in Filter.objects.all()]),

            HTML("<hr/>"),  # Diffuser and Slit section
            Row(Column('diffusers'), Column('g_diffuser'), Column('r_diffuser'), Column('i_diffuser'),
                Column('z_diffuser')),

            # include hidden fields
            Row(Column('name'), Column('proposal'), Column('ipp_value'), Column('observation_mode'),
                Column('exposure_time'), Column('max_airmass'), Column('end'),),

            HTML("<hr/>"),  # Submit section
            Row(Column(ButtonHolder(Submit('submit', 'Submit Request')))),
        )

    def _build_target_fields(self):
        target_fields = {
            'name': 'Bias target',
            'type': 'HOUR_ANGLE',
            'hour_angle': 1,
            'dec': 0
        }

        return target_fields

    def _build_configuration(self):
        configuration = super()._build_configuration()
        configuration['type'] = 'BIAS'  # Bias observation must have obstype BIAS
        configuration['instrument_name'] = self.cleaned_data['instrument']
        configuration['constraints'] = {
            'max_airmass': self.cleaned_data['max_airmass'],
            'min_lunar_phase': 0,
        }

        return configuration

    def _build_instrument_config(self):
        instrument_config = []
        if self.cleaned_data['instrument_type'] != '2M0-SCICAM-MUSCAT':
            instrument_config.append({
                'mode': self.cleaned_data['readout_mode'],
                'exposure_count': self.cleaned_data['exposure_count'],
                'optical_elements': {
                    'filter': self.cleaned_data['filter']
                }
            })
        else:
            # Will need some work before ready for MUSCAT Bias
            extra_params = {
                'exposure_mode': 'SYNCHRONOUS',
                'exposure_time_g': self.cleaned_data['g'][2],
                'exposure_time_r': self.cleaned_data['r'][2],
                'exposure_time_i': self.cleaned_data['i'][2],
                'exposure_time_z': self.cleaned_data['z'][2],
                "offset_ra": 0,
                "offset_dec": 0,
                "defocus": 0
            }
            instrument_config.append({
                'exposure_count': self.cleaned_data['g'][1],
                'exposure_time': max(
                    self.cleaned_data['g'][2],
                    self.cleaned_data['r'][2],
                    self.cleaned_data['i'][2],
                    self.cleaned_data['z'][2]
                ),
                "mode": "MUSCAT_FAST",
                "rotator_mode": "",
                'optical_elements': {
                    'diffuser_g_position': "out",
                    'diffuser_r_position': "out",
                    'diffuser_i_position': "out",
                    'diffuser_z_position': "out"
                },
                "extra_params": extra_params,
            })
        # logger.debug(f'instrument_config = {instrument_config}\n')
        return instrument_config

    def _build_location(self):
        # TODO: Add support for submitting to all sites, which will require direct scheduler submission
        location = super()._build_location()
        location['site'] = self.cleaned_data['site']
        location['enclosure'] = self.cleaned_data['enclosure']
        location['telescope'] = self.cleaned_data['telescope']

        return location

    # def clean(self):
    #     cleaned_data = super().clean()
    #     print(cleaned_data)
    #     return cleaned_data

    # def is_valid(self):
    #     # TODO: remove me when logger.debug messages are not useful
    #     valid = super().is_valid()
    #     print(self.validate_at_facility())
    #     logger.debug(f'is_valid: {valid}')
    #     logger.debug(f'is_valid: errors: {self.errors}')
    #     return valid

    def observation_payload(self):
        payload = super().observation_payload()
        # payload = {
        #     'name': 'LCOGT',
        #     'proposal': 'calibrate',
        #     'ipp_value': 1.0,
        #     'operator': 'SINGLE',
        #     'observation_type': 'NORMAL',
        #     'requests': [
        #         {
        #             'configurations': [self._build_configuration()],
        #             'windows': [
        #                 {
        #                     'start': self.cleaned_data['start'],
        #                     # 'end': self.cleaned_data['end']
        #                 }
        #             ],
        #             'location': self._build_location()
        #         }
        #     ]
        # }
        # # if self.cleaned_data.get('period') and self.cleaned_data.get('jitter'):
        #    payload = self._expand_cadence_request(payload)

        return payload

    def submit_observation(self, observation_payload):

        response = super().submit_observation()
        response = make_request(
            'POST',
            PORTAL_URL + '/api/schedule/',
            json=observation_payload,
            headers=self._portal_headers()
        )
        return [r['id'] for r in response.json()['requests']]


class BiasCalibrationsFacility(LCOFacility):
    name = 'Bias Calibrations'

    # these key-values appear as tabs in the Observations/create template
    observation_forms = {
        'BIAS_CALIBRATIONS': BiasCalibrationsManualSubmissionForm,
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
