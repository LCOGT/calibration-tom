from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit
from django import forms
from django.urls import reverse

from tom_targets.models import Target


class NRESCalibrationSubmissionForm(forms.Form):
    # site = forms.ChoiceField(choices=[('all', 'All'), ('cpt', 'cpt')])  # TODO: should be a ChoiceField
    frequency = forms.IntegerField(label=False, widget=forms.NumberInput(attrs={'placeholder': 'Frequency (hours)'}))
    target = forms.ChoiceField(choices=[])  # Display standard type alongside target name

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target'] = forms.ChoiceField(
            choices=[(target.id,
                      f"{target.name} ({target.targetextra_set.filter(key='standard_type').first().value})")
                     for target in Target.objects.all()],
            label=False
        )
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('targeted_calibrations:nres_submission')
        self.helper.layout = Layout(
            Row(
                Column('frequency'),
                Column('target'),
                Column(
                    ButtonHolder(
                        Submit('submit', 'Update or Create Cadence')
                    )
                )
            )
        )