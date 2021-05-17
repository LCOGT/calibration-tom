from datetime import datetime, timedelta
from dateutil.parser import parse
from enum import Enum
import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, HTML, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from tom_observations.facilities.lco import LCOBaseObservationForm, LCOFacility
from tom_targets.models import Target

import configdb.site
from configdb.configdb_connections import ConfigDBInterface
from calibrations.fields import FilterMultiValueField, FilterMultiWidget
from targeted_calibrations.models import Filter



logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


class LCOCalibrationForm(LCOBaseObservationForm):
    # TODO: make a proper super-class out of this LCOCalibrationForm

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


def enum_to_choices(emum_class) -> [()]:
    """Turn an enum.Enum into a list of 2-tuples suitable for the forms.ChoiceField.choices parameter
     """
    return [(e.value, e.name) for e in emum_class]


# TODO: clean up unnecessary superclass overrides

# Diffusers, Slits, and Groups were part of the CLI of the calibration_utils submit_calibration script
# TODO: what's the deal with Diffusers?
#    (diffusers are part of MUSCat, I think) (from David: this is correct)
# TODO: what's the deal with Slits (from David: slit is almost certainly not necessary for PHOTOMETRIC standards)
# TODO: what's the deal with Groups (from David: group is not used in calibration_utils photometric standards)
# TODO: according to doc, photometric standards window is open at a certain time--should this be pre-filled into the form?


class ImagerCalibrationManualSubmissionForm(LCOBaseObservationForm):
    """Form for submission of photometric standards to imagers.

    This is loosely based on the options to the calibration_util submit_calibration script.
    """
    config_db = ConfigDBInterface(settings.CONFIGDB_URL)
    # set up the self.fields dict of form.xFields; dict key is property name (i.e. 'target_id')
    site = forms.ChoiceField(required=True,
                            #  choices=enum_to_choices(SiteCode),
                             choices=[],
                             label='Site')
    enclosure = forms.ChoiceField(choices=[])

    telescope = forms.ChoiceField(choices=[])  # TODO: populate telescope choices from enclosure choice

    instrument = forms.ChoiceField(choices=[])  # TODO: populate instrument choices from telescope choice

    diffusers = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    g_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    r_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    i_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    z_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])

    target_id = forms.ChoiceField(required=True,
                                  # these choices must be defined at runtime (after the database is accessible)
                                  choices=[('No targets found in database', 'No targets found in database')],
                                  label='Standard Field')

    def optical_filters(self):
        """The single source of truth for the list filters that are included in the
        form, considered in the instrument_config, and checked in clean().
        """
        # if you want a subset of the Filters from the db, this is the place to restrict the queryset.
        return Filter.objects.all()

    def enclosure_choices(self):
        enclosures = set()

        for site in self.config_db.site_info:
            for enclosure in site['enclosure_set']:
                enclosures.add(enclosure['code'])

        return sorted([(e, e) for e in enclosures], key=lambda enclosure_tuple: enclosure_tuple[0])

    def instrument_choices(self):  # Overrides the LCOBaseForm instrument_choices()
        instruments = set()

        for dome_values in self.config_db.get_active_instruments_info().values():
            for instrument in dome_values:
                instruments.add((instrument['code'], instrument['code']))

        return sorted(instruments)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set up the form field choices that must be assigned at run-time (not when byte-compiling the class definition)
        self.fields['target_id'].choices = [(target.id, f'{target.name} et al') for target in Target.objects.all()]
        self.fields['target_id'].initial = Target.objects.first().id

        self.fields['site'].choices = [(site['code'].upper(), site['code']) for site in self.config_db.site_info]
        self.fields['enclosure'].choices = self.enclosure_choices()
        self.fields['telescope'].choices = sorted(set([(dome, dome) for dome, _ in self.config_db.get_active_instruments_info().items()]))
        self.fields['instrument'].choices = self.instrument_choices()

        # each filter gets an entry in the self.fields dictionary
        self.fields.update({
            f.name: FilterMultiValueField(filter=f,
                                          initial={  # see FilterMultiWidget for definition of widget_names
                                              f'{f.name}_selected': False,
                                              f'{f.name}_exposure_count': f.exposure_count,
                                              f'{f.name}_exposure_time': f.exposure_time,
                                          },
                                          required=False) for f in self.optical_filters()})

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # TODO: define 'targeted_calibrations:imager_submission'
        # self.helper.form_action = reverse('targeted_calibrations:imager_submission')

        # remove (pop) unwanted fields from the self.fields
        for field_name in ['filter', 'exposure_time', 'exposure_count']:
            self.fields.pop(field_name)

        # TODO: until we have cadences, we don't need a cadence_frequency in this form
        if 'cadence_frequency' in self.fields:
            self.fields['cadence_frequency'].required = False

        self.helper.layout = Layout(
            HTML("<hr/>"),  #
            self.common_layout,
            'name',  # TODO: deal
            'proposal',
            'ipp_value',
            'observation_mode',
            'instrument_type',
            'max_airmass',
            'start',
            'end',

            HTML("<hr/>"),  # Site.Enclosure.Telescope.Instrument section
            Row(Column('site'), Column('enclosure'), Column('telescope'), Column('instrument')),

            HTML("<hr/>"),  # new Filter section
            # TODO: somehow insert Column headers: 'Filter, Exposure Time, Exposure count
            # here, we  unpack (*) the tuple of Rows created by the list comprehension
            # this just adds one Row(Column(...) per Filter to the Layout args
            Row(
                Column(HTML('Filter')),
                Column(HTML('Exposure Count')),
                Column(HTML('Exposure Time'))
            ),
            *tuple([Row(Column(f.name)) for f in Filter.objects.all()]),

            HTML("<hr/>"),  # Diffuser and Slit section
            Row(Column('diffusers'), Column('g_diffuser'), Column('r_diffuser'), Column('i_diffuser'), Column('z_diffuser')),

            HTML("<hr/>"),  # Submit section
            Row(Column(ButtonHolder(Submit('submit', 'Submit Request')))),
        )

    def _build_configuration(self):
        configuration = super()._build_configuration()
        configuration['instrument_name'] = self.cleaned_data['instrument']

        return configuration

    def _build_instrument_config(self):
        """
        For example:
        .. code:: python
          instrument_config = {
              'exposure_count': self.cleaned_data['exposure_count'],
              'exposure_time': self.cleaned_data['exposure_time'],
              'optical_elements': {
                  'filter': self.cleaned_data['filter']
              }
          }

        Because the photometric sequence form provides form inputs for 10 different filters, they must be
        constructed into a list of instrument configurations as per the LCO API. This method constructs the
        instrument configurations in the appropriate manner.
        """
        logger.debug(f'instrument_config cleaned_data: {self.cleaned_data}')

        instrument_config = []
        # TODO: this list of filters must be consistent with the FilterMultiValueField instances
        #  created in the __init__
        for f in self.optical_filters():
            # check that field is selected (zero-th index is the checkbox)
            if self.cleaned_data.get(f.name)[0]:
                instrument_config.append({
                    # this indexing must be consistent with the field order in decompress
                    'exposure_count': self.cleaned_data[f.name][1],
                    'exposure_time': self.cleaned_data[f.name][2],
                    'optical_elements': {
                        'filter': f.name
                    }
                })

        logger.debug(f'instrument_config: {instrument_config}')
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
    #     logger.debug(f'observation_payload: {observation_payload}')
    #     return observation_payload

    def clean(self):
        cleaned_data = super().clean()
        logger.debug(f'cleaned_data: {cleaned_data}')  # TODO: remove logger.debug
        # check that at least one filter is marked for inclusion in the instrument config
        # by finding the value of the filter.name key (which is the decompress)
        # and the zero-th item is the checkbox
        for f in self.optical_filters():
            if cleaned_data[f.name][0]:
                break
        else:
            raise forms.ValidationError('At least one filter must be included in the request.')
        return cleaned_data

    # def is_valid(self):
    #     # TODO: remove me when logger.debug messages are not useful
    #     valid = super().is_valid()
    #     print(self.validate_at_facility())
    #     logger.debug(f'is_valid: {valid}')
    #     logger.debug(f'is_valid: errors: {self.errors}')
    #     return valid


class LCOCalibrationFacility(LCOFacility):
    name = 'LCO Calibrations'

    # these key-values appear as tabs in the Observations/create template
    observation_forms = {
        'NRES': LCOCalibrationForm,
        'IMAGER': ImagerCalibrationManualSubmissionForm,
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
