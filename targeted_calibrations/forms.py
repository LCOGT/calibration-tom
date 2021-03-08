from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.urls import reverse

from tom_targets.models import Target


class NRESCalibrationSubmissionForm(forms.Form):
    site = forms.ChoiceField(required=True,
                             choices=[('all', 'All Sites')] + [(site, site) for site in settings.NRES_SITES],
                             label=False)
    frequency = forms.IntegerField(label=False, widget=forms.NumberInput(attrs={'placeholder': 'Frequency (hours)'}))
    target = forms.ChoiceField(choices=[])  # Display standard type alongside target name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target'] = forms.ChoiceField(  # Create choices for standard_types of targets currently in season
            choices=[(target.id,
                      f"{target.targetextra_set.filter(key='standard_type').first().value} (currently {target.name})")
                     for target in Target.objects.all() if target.target_is_in_season()],
            label=False
        )
        self.helper = FormHelper()
#        self.helper.form_method = 'post'
#        self.helper.form_action = reverse('targeted_calibrations:nres_submission')
        # TODO: remove when you want to re-enable the submit button
        self.helper.form_method = 'get'
        self.helper.form_action = ''  # no-op

        self.helper.layout = Layout(
            Row(
                Column('site'),
                Column('frequency'),
                Column('target'),
                Column(
                    ButtonHolder(
                        Submit('submit', 'Update or Create Cadence')
                    )
                )
            )
        )