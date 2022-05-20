
import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, HTML, Layout, Row, Submit
from django import forms
from django.conf import settings
from tom_observations.facilities.lco import LCOBaseObservationForm, LCOFacility
from tom_observations.widgets import FilterField

from configdb.configdb_connections import ConfigDBInterface
#from calibrations.fields import FilterMultiValueField
#from calibrations.models import Filter

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

    config_db = ConfigDBInterface(settings.CONFIGDB_URL) # CONFIGDB_URL is set in calibration_tom/settings.py

    # set up the self.fields dict of form.xFields; dict key is property name (i.e. 'target_id')
    site = forms.ChoiceField(required=True, #  choices=enum_to_choices(SiteCode), # enum_to_choices is never used
                             choices=[],
                             label='Site')
    enclosure = forms.ChoiceField(choices=[])

    telescope = forms.ChoiceField(choices=[])  # TODO: populate telescope choices from enclosure choice

    instrument = forms.ChoiceField(choices=[])  # TODO: populate instrument choices from telescope choice

    readout_mode = forms.ChoiceField(choices=[]) #

    filter = forms.ChoiceField(choices=[]) #

    diffusers = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    g_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    r_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    i_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    z_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])

    target_id = forms.ChoiceField(required=True, # these choices must be defined at runtime (after the database is accessible)
                                  choices=[('No targets found in database', 'No targets found in database')],
                                  label='Standard Field')


    #start_time = forms.CharField(widget=forms.TextInput(attrs={'type': 'datetime'}))
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime'}), help_text="input format = %Y-%m-%d %H:%M:%S")

    #end_time = forms.CharField(widget=forms.TextInput(attrs={'type': 'datetime'}))
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime'}), help_text="input format = %Y-%m-%d %H:%M:%S")

    exposure_count = forms.IntegerField(widget=forms.NumberInput(attrs={'type': 'integer'}), help_text="minimum = 1")

    #exposure_time = forms.FloatField(widget=forms.NumberInput(attrs={'type': 'integer'}), help_text="seconds")

    # Save this as an example of how the label an be displayed on the form.
    #target_id = forms.ChoiceField(required=True, 
    #                              # these choices must be defined at runtime (after the database is accessible)
    #                              choices=[('No targets found in database', 'No targets found in database')],
    #                              label='This label is for target selection.')

    #name = forms.CharField(initial="LCOGT", widget=forms.HiddenInput())

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
                #instruments.add(instrument_index['code'])

        return sorted(instruments)

    def readout_mode_choices(self):
        readout_modes = set()
    
        for active_instrument_values in self.config_db.get_active_instruments_info().values():
            for instrument_value in active_instrument_values:
                for readout_mode_details in instrument_value['named_readout_modes']:
                    readout_modes.add((readout_mode_details['code'], readout_mode_details['code']))
    
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

        biastarget = { # from JC (2022-05-11): don't use class BiasTarget from bias_calibrations/models.py.
            'name': 'Bias target',
            'type': 'HOUR_ANGLE',
            'hour_angle': 1,
            'dec': 0
        }
        # This is the NULL_TARGET from calibration_type.py

        self.fields['site'].choices = [(site['code'], site['code']) for site in self.config_db.site_info]
        self.fields['enclosure'].choices = self.enclosure_choices()
        self.fields['telescope'].choices = sorted(set([(dome.split('.')[-1], dome.split('.')[-1]) for dome, _ in self.config_db.get_active_instruments_info().items()]))
        self.fields['instrument'].choices = self.instrument_granular_choices()
        self.fields['readout_mode'].choices = self.readout_mode_choices()
        self.fields['filter'].choices = self.optical_element_choices() 

        self.helper = FormHelper()
        self.helper.form_method = 'post'

        # TODO: define 'nres_calibrations:imager_submission'
        # self.helper.form_action = reverse('nres_calibrations:imager_submission')

        # TODO: until we have cadences, we don't need a cadence_frequency in this form
        #if 'cadence_frequency' in self.fields:
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
            #'name' = 'LCOGT', # Irrelevant for bias requests?
            #'proposal', # Fix to CALIBRATE for BIAS requests
            #'ipp_value', # irrelevant for DIRECT scheduled observations
            #'observation_mode', # irrelevant for DIRECT observations
            #'instrument_type', # typically a specific instrument, rather than an instrument_type
            #'max_airmass', # irrelevant for DIRECT observations
            #'min_lunar_distance', # irrelevant for DIRECT observations

            #HTML("<hr/>"),  # Site.Enclosure.Telescope.Instrument section
            #Row(Column('site'), Column('enclosure'), Column('telescope'), Column('instrument_type'), Column('instrument')),
            Row(Column('site'), Column('enclosure'), Column('telescope'), Column('instrument_type'), Column('instrument')),

            Row(Column('readout_mode'), Column('filter'), Column('exposure_count')),

            'start_time',
            #'end_time',

            HTML("<hr/>"),  # new Filter section

            #*tuple([Row(Column(f.name)) for f in Filter.objects.all()]),

            HTML("<hr/>"),  # Diffuser and Slit section
            Row(Column('diffusers'), Column('g_diffuser'), Column('r_diffuser'), Column('i_diffuser'), Column('z_diffuser')),

            HTML("<hr/>"),  # Submit section
            Row(Column(ButtonHolder(Submit('submit', 'Submit Request')))),
        )



    def _build_configuration(self):
        configuration = super()._build_configuration()
        #configuration['name'] = 'LCOGT', # Irrelevant for bias observations, but LCOGT is historical
        configuration['target'] = biastarget, # Make the target for the configuration the biastarget
        #configuration['proposal'] = 'calibrate', # 'calibrate' propid requests are DIRECTly scheduled
        configuration['type'] = 'BIAS' # Bias observation must have obstype BIAS
        #configuration['observation_mode'] = 'Normal' # Bias observation is neither TC nor RR
        #configuration['ipp_value'] = 1.0 # IPP default = 1.0
        configuration['instrument_name'] = self.cleaned_data['instrument']
        configuration['constraints']: {
            'max_airmass': 20,
            'min_lunar_phase': 0,
        }
        configuration['requests']: {
            'windows': [
                {
                    'start': self.cleaned_data['start_time'],
                }
            ],
        }

        return configuration

    def _build_instrument_config(self):
        
        #logger.debug(f"instrument = {self.cleaned_data['instrument']}\n") 
        #logger.debug(f"instrument_type = {self.cleaned_data['instrument_type']}\n")
        #logger.debug(f"exposure_time_g = {self.cleaned_data['g'][2]}\n")
        instrument_config = []
        if self.cleaned_data['instrument_type'] != '2M0-SCICAM-MUSCAT':
            # TODO: this list of filters must be consistent with the FilterMultiValueField instances
            #  created in the __init__
            #for f in self.optical_filters():
                # check that field is selected (zero-th index is the checkbox)
                #if self.cleaned_data.get(f.name)[0]:
                    #instrument_config.append({
            instrument_config.append({
                        # this indexing must be consistent with the field order in decompress
                        #'exposure_count': self.cleaned_data[f.name][1],
                        #'exposure_time': self.cleaned_data[f.name][2],
                        #'optical_elements': {
                        #    'filter': f.name
                        #}
                'mode': self.cleaned_data[readout_mode],
                'exposure_count': self.cleaned_data[exposure_count],
                'optical_elements': {
                    'filter': self.cleaned_data[filter]
                }
                        # Adding the 'mode' element below. How do I know if it's in "cleaned_data"? How do I add it if not?
                        #'mode': self.cleaned_data['mode'],
                    #})
            })
        else:
            extra_params = {
                'exposure_mode' : 'SYNCHRONOUS',
                'exposure_time_g' : self.cleaned_data['g'][2],
                'exposure_time_r' : self.cleaned_data['r'][2],
                'exposure_time_i' : self.cleaned_data['i'][2],
                'exposure_time_z' : self.cleaned_data['z'][2],
                "offset_ra": 0,
                "offset_dec": 0,
                "defocus": 0
            }
            instrument_config.append({
                'exposure_count' : self.cleaned_data['g'][1],
                'exposure_time' : max(
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
        #logger.debug(f'instrument_config = {instrument_config}\n')
        return instrument_config

    def _build_location(self):
        # TODO: Add support for submitting to all sites, which will require direct scheduler submission
        location = super()._build_location()
        location['site'] = self.cleaned_data['site']
        location['enclosure'] = self.cleaned_data['enclosure']
        location['telescope'] = self.cleaned_data['telescope']

        return location

    # def observation_payload(self):
    #     # TODO: remove me when logger.debug messages are not useful
    #     observation_payload = super().observation_payload()
    #     logger.debug(f'observation_payload: {observation_payload}\n')
    #     return observation_payload

    def clean(self):
        cleaned_data = super().clean()
        # logger.debug(f'cleaned_data: {cleaned_data}')  # TODO: remove logger.debug
        # check that at least one filter is marked for inclusion in the instrument config
        # by finding the value of the filter.name key (which is the decompress)
        # and the zero-th item is the checkbox
        #for f in self.optical_filters():
        #    if cleaned_data[f.name][0] is True:
        #        break
        #else:
        #    raise forms.ValidationError('At least one filter must be included in the request.')
        #return cleaned_data

    # def is_valid(self):
    #     # TODO: remove me when logger.debug messages are not useful
    #     valid = super().is_valid()
    #     print(self.validate_at_facility())
    #     logger.debug(f'is_valid: {valid}')
    #     logger.debug(f'is_valid: errors: {self.errors}')
    #     return valid

    def observation_payload(self):

        #payload = super().observation_payload()
        payload = {
            'name': 'LCOGT',
            'proposal': 'calibrate',
            'ipp_value': 1.0,
            'operator': 'SINGLE',
            'observation_type': 'NORMAL',
            'requests': [
                {
                    'configurations': [self._build_configuration()],
                    #'windows': [
                    #    {
                    #        'start': self.cleaned_data['start'],
                    #        'end': self.cleaned_data['end']
                    #    }
                    #],
                    'location': self._build_location()
                }
            ]
        }
        #if self.cleaned_data.get('period') and self.cleaned_data.get('jitter'):
        #    payload = self._expand_cadence_request(payload)

        return payload


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
