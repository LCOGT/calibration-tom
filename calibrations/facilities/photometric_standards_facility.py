
import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, HTML, Layout, Row, Submit
from django import forms
from django.conf import settings
from tom_observations.facilities.lco import LCOOldStyleObservationForm, LCOFacility
from tom_targets.models import Target

from configdb.configdb_connections import ConfigDBInterface
from calibrations.fields import FilterMultiValueField
from calibrations.models import Filter

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


def enum_to_choices(emum_class) -> [()]:
    """Turn an enum.Enum into a list of 2-tuples suitable for the forms.ChoiceField.choices parameter
     """
    return [(e.value, e.name) for e in emum_class]


# TODO: clean up unnecessary superclass overrides

# Narrowbands, Slits, and Groups were part of the CLI of the calibration_utils submit_calibration script
# TODO: according to doc, photometric standards window is open at a certain time--should this be pre-filled into the form?
class PhotometricStandardsManualSubmissionForm(LCOOldStyleObservationForm):
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

    narrowbands = forms.ChoiceField(choices=[('in', 'In'), ('out', 'Out')])
    g_narrowband = forms.ChoiceField(choices=[('in', 'In'), ('out', 'Out')], initial='out')
    r_narrowband = forms.ChoiceField(choices=[('in', 'In'), ('out', 'Out')], initial='out')
    i_narrowband = forms.ChoiceField(choices=[('in', 'In'), ('out', 'Out')], initial='out')
    z_narrowband = forms.ChoiceField(choices=[('in', 'In'), ('out', 'Out')], initial='out')

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

    def instrument_granular_choices(self):
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

        self.fields['site'].choices = [(site['code'], site['code']) for site in self.config_db.site_info]
        self.fields['enclosure'].choices = self.enclosure_choices()
        self.fields['telescope'].choices = sorted(set([(dome.split('.')[-1], dome.split('.')[-1]) for dome, _ in self.config_db.get_active_instruments_info().items()]))
        self.fields['instrument'].choices = self.instrument_granular_choices()

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
        # TODO: define 'nres_calibrations:imager_submission'
        # self.helper.form_action = reverse('nres_calibrations:imager_submission')

        # remove (pop) unwanted fields from the self.fields
        for field_name in ['filter', 'exposure_time', 'exposure_count']:
            if field_name in self.fields:
                logger.debug(f'PhotometricStandardsManualSubmissionForm.__init__(): removing {field_name} from self.fields')
                self.fields.pop(field_name)
            else:
                logger.debug(f'PhotometricStandardsManualSubmissionForm.__init__(): {field_name} not found in self.fields (so, not removed)')

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
            'min_lunar_distance',
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

            HTML("<hr/>"),  # Narrow Band and Slit section
            Row(Column('narrowbands'), Column('g_narrowband'), Column('r_narrowband'), Column('i_narrowband'), Column('z_narrowband')),

            HTML("<hr/>"),  # Submit section
            Row(Column(ButtonHolder(Submit('submit', 'Submit Request')))),
        )

    def _build_configuration(self):
        # temporarily statisfy super requirements (these is just made up values)
        logger.debug(f'**** self.cleaned_data: {self.cleaned_data}')
        if 'exposure_count' not in self.cleaned_data:
            self.cleaned_data['exposure_count'] = 1
        if 'exposure_time' not in self.cleaned_data:
            self.cleaned_data['exposure_time'] = 1
        if 'filter' not in self.cleaned_data:
            self.cleaned_data['filter'] = 'ip'

        configuration = super()._build_configuration()
        configuration['type'] = 'STANDARD' # Photometric standard observation must have obstype STANDARD
        configuration['instrument_name'] = self.cleaned_data['instrument']
        configuration['min_lunar_distance'] = self.cleaned_data['min_lunar_distance']  # TODO: this needs to go into tom_base

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

        This method constructs the instrument configurations in the appropriate manner.
        """
        
        logger.debug(f"instrument = {self.cleaned_data['instrument']}\n") 
        logger.debug(f"instrument_type = {self.cleaned_data['instrument_type']}\n")
        logger.debug(f"exposure_time_g = {self.cleaned_data['g'][2]}\n")
        instrument_config = []
        if self.cleaned_data['instrument_type'] != '2M0-SCICAM-MUSCAT':
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
            base_narrowband_position = None
            if 'narrowbands' in self.cleaned_data and self.cleaned_data['narrowbands']:
                base_narrowband_position = self.cleaned_data['narrowbands']
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
                    'narrowband_g_position': base_narrowband_position if base_narrowband_position else self.cleaned_data['g_narrowband'],
                    'narrowband_r_position': base_narrowband_position if base_narrowband_position else self.cleaned_data['r_narrowband'],
                    'narrowband_i_position': base_narrowband_position if base_narrowband_position else self.cleaned_data['i_narrowband'],
                    'narrowband_z_position': base_narrowband_position if base_narrowband_position else self.cleaned_data['z_narrowband']
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
        for f in self.optical_filters():
            if cleaned_data[f.name][0] is True:
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


class PhotometricStandardsFacility(LCOFacility):
    name = 'Photometric Standards'

    # these key-values appear as tabs in the Observations/create template
    observation_forms = {
        'PHOTOMETRIC_STANDARDS': PhotometricStandardsManualSubmissionForm,
    }

    EXCLUDED_FRAME_SUFFIXES = (
        'e91',  # e91 frames are NRES Autoguider images and are not desirable to download
    )


    #def __init__(self, facility_settings=OCSSettings('LCO')):
    #    super().__init__(facility_settings=facility_settings)


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
