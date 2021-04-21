from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.layout import ButtonHolder, Column, HTML, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.urls import reverse

from tom_targets.models import Target
import configdb.site


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

    instrument = forms.ChoiceField(choices=[('ef12', 'ef12')])  # TODO: populate instrument choices from telescope choice
    filter = forms.MultipleChoiceField(
        choices=enum_to_choices(configdb.site.Filter)
    )  # TODO: populate filter choices instrument choice via ConfigDB

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
                                  choices=[(target.id,
                                            f"{target.name} plus additional helpful info")
                                           # TODO: filter to only Imager photometric standard targets
                                           for target in Target.objects.all()],
                                  label='Standard Field')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # TODO: define 'targeted_calibrations:imager_submission'
        #self.helper.form_action = reverse('targeted_calibrations:imager_submission')

        self.helper.layout = Layout(
            HTML("<hr/>"),
            Row(Column('site'), Column('enclosure'), Column('telescope'), Column('instrument')),
            Row(Column('target_id')),
            HTML("<hr/>"),
            Row(Column(InlineCheckboxes('filter'))),
            Row(Column('exposure_time'), Column('exposure_count')),
            HTML("<hr/>"),
            Row(Column('diffusers'), Column('g_diffuser'), Column('r_diffuser'), Column('i_diffuser'), Column('z_diffuser')),
            Row(Column('slit'), Column('group')),
            HTML("<hr/>"),
            Row(Column(ButtonHolder(Submit('submit', 'Submit Request'))))
        )


class NRESCadenceSubmissionForm(forms.Form):
    site = forms.ChoiceField(required=True,
                             choices=[('all', 'All Sites')] + [(site, site) for site in settings.NRES_SITES],
                             label=False)
    cadence_frequency = forms.IntegerField(label=False, min_value=1,
                                   widget=forms.NumberInput(attrs={'placeholder': 'Frequency (hours)'}))
    target_id = forms.ChoiceField(choices=[])  # Display standard type alongside target name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # target_id choices must  be defined here in the __init__ rather than in the class definition
        # because the target_is_in_season method used below is added dynamically to the Target class
        # and it doesn't yet exist at the time of class interpretation, but it does when the instance
        # is made (and __init__ is called)
        self.fields['target_id'] = forms.ChoiceField(  # Create choices for standard_types of targets currently in season
            choices=[(target.id,
                      f"{target.targetextra_set.filter(key='standard_type').first().value} (currently {target.name})")
                     for target in Target.objects.all() if target.target_is_in_season()],
            label=False
        )
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('targeted_calibrations:nres_submission')

        self.helper.layout = Layout(
            Row(
                Column('site'),
                Column('cadence_frequency'),
                Column('target_id'),
                Column(
                    ButtonHolder(
                        Submit('submit', 'Update or Create Cadence')
                    )
                )
            )
        )
