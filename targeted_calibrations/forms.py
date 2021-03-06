from datetime import datetime

from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.urls import reverse

from tom_targets.models import Target


def target_is_in_season(self, query_date: datetime=datetime.utcnow()):
    """"Returns True if query_date is between target's seasonal_start and seasonal_end
    Note: seasonal_start and seasonal_end are month numbers (1=January, etc).

    This method will be added to the Target class with setattr (that's why it has a self argument).
    """
    seasonal_start = int(self.targetextra_set.filter(key='seasonal_start').first().value)
    seasonal_end = int(self.targetextra_set.filter(key='seasonal_end').first().value)

    return seasonal_start <= query_date.month <= seasonal_end
setattr(Target, 'target_is_in_season', target_is_in_season)  # noqa - add method to Target class


class NRESCalibrationSubmissionForm(forms.Form):
    site = forms.ChoiceField(required=True,
                             choices=[('all', 'All Sites')] + [(site, site) for site in settings.NRES_SITES],
                             label=False)
    frequency = forms.IntegerField(label=False, widget=forms.NumberInput(attrs={'placeholder': 'Frequency (hours)'}))
    target = forms.ChoiceField(  # Create choices for standard_types of targets currently in season
        choices=[(target.id,
                  f"{target.targetextra_set.filter(key='standard_type').first().value} (currently {target.name})")
                 for target in Target.objects.all() if target.target_is_in_season()],
        label=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('targeted_calibrations:nres_submission')
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