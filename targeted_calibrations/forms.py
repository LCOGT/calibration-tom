from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit
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
    site = forms.ChoiceField(required=True,
                             choices=enum_to_choices(configdb.site.SiteCode),
                             label='Site')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        pass


class NRESCalibrationSubmissionForm(forms.Form):
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
