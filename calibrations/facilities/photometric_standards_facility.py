import logging

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, HTML, Layout, Row, Submit
from django import forms
from django.conf import settings
from tom_observations.facilities.lco import (LCOFacility, LCOSettings,
                                             LCOFullObservationForm)

from tom_targets.models import Target

from configdb.configdb_connections import ConfigDBInterface
from calibrations.fields import FilterMultiValueField
from calibrations.models import Filter

logger = logging.getLogger(__name__)


def enum_to_choices(emum_class) -> [()]:
    """Turn an enum.Enum into a list of 2-tuples suitable for the forms.ChoiceField.choices parameter
     """
    return [(e.value, e.name) for e in emum_class]


# Narrowbands, Slits, and Groups were part of the CLI of the calibration_utils submit_calibration script
# TODO: according to doc, photometric standards window is open at a certain time
#  --should this be pre-filled into the form?

class PhotometricStandardsManualSubmissionForm(LCOFullObservationForm):
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

    narrowbands = forms.ChoiceField(
        label='Force narrowbands in', required=False,
        choices=[(True, 'True'), (False, 'False')], initial=False)
    g_narrowband = forms.ChoiceField(required=False, choices=[('in', 'In'), ('out', 'Out')], initial='out')
    r_narrowband = forms.ChoiceField(required=False, choices=[('in', 'In'), ('out', 'Out')], initial='out')
    i_narrowband = forms.ChoiceField(required=False, choices=[('in', 'In'), ('out', 'Out')], initial='out')
    z_narrowband = forms.ChoiceField(required=False, choices=[('in', 'In'), ('out', 'Out')], initial='out')

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

        # remove (pop) unwanted fields from the self.fields
        for field_name in ['filter', 'exposure_time', 'exposure_count']:
            if field_name in self.fields:
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

    def _build_configuration(self, build_id):
        configuration = super()._build_configuration(build_id)

        if configuration:
            configuration['type'] = 'STANDARD'  # Photometric standard observation must have obstype STANDARD
            configuration['instrument_name'] = self.cleaned_data['instrument']

        return configuration

    def _build_instrument_configs(self, instrument_type, configuration_id):
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
        instrument_config = []
        if not instrument_type:
            # early return because there's no instrument type
            return instrument_config

        if instrument_type != '2M0-SCICAM-MUSCAT':
            # TODO: this list of filters must be consistent with the FilterMultiValueField instances
            #  created in the __init__

            # this is the normal non-MuSCAT case
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
            force_narrowbands_in = self.cleaned_data['narrowbands']
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
                    'narrowband_g_position': 'in' if force_narrowbands_in else self.cleaned_data['g_narrowband'],
                    'narrowband_r_position': 'in' if force_narrowbands_in else self.cleaned_data['r_narrowband'],
                    'narrowband_i_position': 'in' if force_narrowbands_in else self.cleaned_data['i_narrowband'],
                    'narrowband_z_position': 'in' if force_narrowbands_in else self.cleaned_data['z_narrowband']
                },
                "extra_params": extra_params,
            })
        return instrument_config

    def _build_location(self):
        # TODO: Add support for submitting to all sites, which will require direct scheduler submission
        location = super()._build_location()
        location['site'] = self.cleaned_data['site']
        location['enclosure'] = self.cleaned_data['enclosure']
        location['telescope'] = self.cleaned_data['telescope']

        return location

    def clean(self):
        cleaned_data = super().clean()
        # check that at least one filter is marked for inclusion in the instrument config
        # by finding the value of the filter.name key (which is the decompress)
        # and the zero-th item is the checkbox
        for f in self.optical_filters():
            if cleaned_data[f.name][0] is True:
                break
        else:
            raise forms.ValidationError('At least one filter must be included in the request.')
        return cleaned_data

    def observation_payload(self):
        payload = super().observation_payload()

        # these were set to "" and None in self.cleaned_data by self.is_valid()
        # and need to be set to valid values here
        if not payload['requests'][0]['optimization_type']:
            payload['requests'][0]['optimization_type'] = 'TIME'
        if not payload['requests'][0]['configuration_repeats']:
            payload['requests'][0]['configuration_repeats'] = 1

        if payload['requests'][0]['configurations'][0]['instrument_type'] == '2M0-SCICAM-MUSCAT':
            # specify the narrowband filter positions
            payload['requests'][0]['configurations'][0]['instrument_configs'][0]['optical_elements']['narrowband_g_position'] = 'Out'
            payload['requests'][0]['configurations'][0]['instrument_configs'][0]['optical_elements']['narrowband_r_position'] = 'Out'
            payload['requests'][0]['configurations'][0]['instrument_configs'][0]['optical_elements']['narrowband_i_position'] = 'Out'
            payload['requests'][0]['configurations'][0]['instrument_configs'][0]['optical_elements']['narrowband_z_position'] = 'Out'

        return payload


class PhotometricStandardsFacility(LCOFacility):
    name = 'Photometric Standards'

    EXCLUDED_FRAME_SUFFIXES = (
        'e91',  # e91 frames are NRES Autoguider images and are not desirable to download
    )

    def __init__(self, facility_settings=LCOSettings('LCO')):
        super().__init__(facility_settings=facility_settings)
        # these key-values appear as tabs in the Observations/create template
        # do this in the init because we're calling update on the observation_forms dict
        self.observation_forms.update({
            'PHOTOMETRIC_STANDARDS': PhotometricStandardsManualSubmissionForm,
        })

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
