from datetime import datetime, timedelta
from dateutil.parser import parse
import logging

from django import forms
from django.core.exceptions import ValidationError

from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, HTML, Layout, Row, Submit

from tom_observations.facilities.lco import LCOBaseObservationForm, LCOFacility
from tom_targets.models import Target

from targeted_calibrations.models import Filter
import configdb.site


logger = logging.getLogger(__name__)


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
        self.fields['exposure_time'].initial = target.targetextra_set.filter(key='exp_time').first().value
        self.fields['exposure_count'].initial = target.targetextra_set.filter(key='exp_count').first().value
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

    def observation_payload(self):
        payload = super().observation_payload()
        logger.info(f'Observation request to be submitted to LCO: {payload}')
        return payload


class NRESCalibrationForm(LCOCalibrationForm):
    # TODO: make a proper subclass out of this NRESCalibrationForm
    pass


class ImagerCalibrationForm(LCOCalibrationForm):
    # TODO: make a proper subclass out of this ImagerCalibrationForm
    pass


class FilterMultiWidget(forms.MultiWidget):
    """Set up a checkbox and two integer widgets for the FilterMultiValueField
    """
    def __init__(self, attrs=None):
        widgets = [
            forms.CheckboxInput,  # to select the filter
            forms.NumberInput,  # for the exposure_time
            forms.NumberInput,  # for the exposure_count
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value) -> []:
        """Split the combined value of the form MultiValueField into the values for each widget"""

        logger.debug(f'FilterMultiWidget decompress value: {value}')
        if value:
            return [None, 0, 0]  # TOOD: return actual values
        return [None, None, None]


class FilterMultiValueField(forms.MultiValueField):

    def compress(self, data_list):
        """Combine cleaned field values in a single value"""
        return data_list
        #  raise NotImplemented  # TODO: implement me

    def __init__(self, **kwargs):
        logger.debug(f'FilterMultiValueField kwargs: {kwargs}')
        self.filter = kwargs.pop('filter')  # Filter model object instance
        # Define one message for all fields.
        error_messages = {
            'incomplete': 'Exposure time and count must be greater than zero for selected filters.',
        }

        # Or define a different message for each field.
        fields = (
            # use the filter if checkbox is checked
            forms.BooleanField(),

            # TODO: set exposure_time dynamically according to filter selection
            # exposure_time
            forms.IntegerField(
                min_value=1, label='time(s)',
                initial=self.filter.exposure_time,
                widget=forms.NumberInput(attrs={'placeholder': 'Exposure Time (seconds)'})
            ),

            # exposure_count
            forms.IntegerField(
                min_value=1, label='count',
                initial=self.filter.exposure_count,
                widget=forms.NumberInput(attrs={'placeholder': 'Exposure Count (exposures)'}))
        )

        self.widget = FilterMultiWidget()

        super().__init__(
            error_messages=error_messages, fields=fields,
            require_all_fields=False, **kwargs
        )


def enum_to_choices(emum_class) -> [()]:
    """Turn an enum.Enum into a list of 2-tuples suitable for the forms.ChoiceField.choices parameter
     """
    return [(e.value, e.name) for e in emum_class]


class ImagerCalibrationManualSubmissionForm(forms.Form):
    """Form for submission of photometric standards to imagers.

    This is loosely based on the options to the calibration_util submit_calibration script.
    """
    # set up the self.fields dict of form.xFields; dict key is property name (i.e. 'target_id')
    site = forms.ChoiceField(required=True,
                             choices=enum_to_choices(configdb.site.SiteCode),
                             label='Site')
    enclosure = forms.ChoiceField(
        # TODO: these are just temporary choices
        choices=[('doma', 'doma'),
                 ('domb', 'domb'),
                 ('domc', 'domc')]
    )  # TODO: populate enclosure choices from site choice

    telescope = forms.ChoiceField(
        choices=enum_to_choices(configdb.site.TelescopeCode),
    )  # TODO: populate telescope choices from enclosure choice

    instrument = forms.ChoiceField(
        choices=[('ef12', 'ef12')],
    )  # TODO: populate instrument choices from telescope choice

    filter = forms.MultipleChoiceField(
        # these choices must be defined at runtime (after the database is accessible)
        choices=[('No filters found in database', 'No filters found in database')],
    )  # TODO: limit filter choices by instrument choice via ConfigDB

    #filter_mv = FilterMultiValueField(fields=None)

    # TODO: set exposure_time dynamically according to filter selection
    exposure_time = forms.IntegerField(min_value=1, label=False,
                                       widget=forms.NumberInput(attrs={'placeholder': 'Exposure Time (seconds)'}))
    exposure_count = forms.IntegerField(min_value=1, label=False,
                                        widget=forms.NumberInput(attrs={'placeholder': 'Exposure Count (exposures)'}))

    diffusers = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    g_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    r_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    i_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    z_diffuser = forms.ChoiceField(choices=[('In', 'In'), ('Out', 'Out')])
    slit = forms.ChoiceField(choices=[('slit choice', 'slit choice')])  # TODO: populate slit choices
    group = forms.ChoiceField(choices=[('group choice', 'group choice')])  # TODO: populate group choices

    target_id = forms.ChoiceField(required=True,
                                  # these choices must be defined at runtime (after the database is accessible)
                                  choices=[('No targets found in database', 'No targets found in database')],
                                  label='Standard Field')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # set up the form field choices that must be assigned at run-time (when byte-compiling the class definition
        self.fields['filter'].choices = [(filter.name, f'{filter.name} et al') for filter in Filter.objects.all()]  # TODO: will go away
        self.fields['target_id'].choices = [(target.id, f'{target.name} et al') for target in Target.objects.all()]

        # set up FilterMultiValueFields
        for filter_instance in Filter.objects.all():
            self.fields.update({f'{filter_instance.name}': FilterMultiValueField(filter=filter_instance)})

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # TODO: define 'targeted_calibrations:imager_submission'
        #self.helper.form_action = reverse('targeted_calibrations:imager_submission')

        self.helper.layout = Layout(
            HTML("<hr/>"),  # Site.Enclosure.Telescope.Instrument section
            Row(Column('site'), Column('enclosure'), Column('telescope'), Column('instrument')),
            Row(Column('target_id')),

            HTML("<hr/>"),  # new Filter section
            # TODO: somehow insert Column headers: 'Filter, Exposure Time, Exposure count
            # here, we  unpack the tuple of Rows created by the list comprehension
            *tuple([Row(Column(f'{filter.name}')) for filter in Filter.objects.all()]),

            HTML("<hr/>"),  # Diffuser and Slit section
            Row(Column('diffusers'), Column('g_diffuser'), Column('r_diffuser'), Column('i_diffuser'), Column('z_diffuser')),
            Row(Column('slit'), Column('group')),

            HTML("<hr/>"),  # Submit section
            Row(Column(ButtonHolder(Submit('submit', 'Submit Request'))))
        )


class LCOCalibrationFacility(LCOFacility):
    name = 'LCO Calibrations'

    # these key-values appear as tabs in the Observations/create template
    observation_forms = {
        'NRES': NRESCalibrationForm,
        'IMAGER': ImagerCalibrationForm,
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
