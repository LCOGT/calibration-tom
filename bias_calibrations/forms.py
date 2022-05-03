from crispy_forms.helper import FormHelper
from crispy_forms.layout import ButtonHolder, Column, Layout, Row, Submit
from django import forms
from django.conf import settings
from django.urls import reverse

from tom_targets.models import Target, CoordinateField

from .models import HOUR_ANGLE_FIELDS, REQUIRED_HOUR_ANGLE_FIELDS



class BiasCalibrationsCadenceSubmissionForm(forms.Form):
    site = forms.ChoiceField(required=True,
                             choices=[('all', 'All Sites')] + [(site, site) for site in settings.BIAS_SITES],
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
                     for target in Target.objects.filter(targetextra__key='calibration_type', targetextra__value='BIAS')
                     if target.target_is_in_season()],
            label=False
        )
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_action = reverse('bias_calibrations:bias_calibrations_submission')

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

class BiasTargetForm(forms.ModelForm)
    groups = forms.ModelMultipleChoiceField(Group.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.extra_fields = {}
        for extra_field in settings.BIAS_EXTRA_FIELDS:
            # Add extra fields to the form
            field_name = extra_field['name']
            self.extra_fields[field_name] = extra_field_to_form_field(extra_field['type'])
            # Populate them with initial values if this is an update
            if kwargs['instance']:
                te = BiasTargetExtra.objects.filter(target=kwargs['instance'], key=field_name)
                if te.exists():
                    self.extra_fields[field_name].initial = te.first().typed_value(extra_field['type'])

            self.fields.update(self.extra_fields)

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit:
            for field in settings.BIAS_EXTRA_FIELDS:
                if self.cleaned_data.get(field['name']) is not None:
                    BiasTargetExtra.objects.update_or_create(
                            target=instance,
                            key=field['name'],
                            defaults={'value': self.cleaned_data[field['name']]}
                    )
            # Save groups for this target
            for group in self.cleaned_data['groups']:
                assign_perm('tom_targets.view_target', group, instance)
                assign_perm('tom_targets.change_target', group, instance)
                assign_perm('tom_targets.delete_target', group, instance)
            for group in get_groups_with_perms(instance):
                if group not in self.cleaned_data['groups']:
                    remove_perm('tom_targets.view_target', group, instance)
                    remove_perm('tom_targets.change_target', group, instance)
                    remove_perm('tom_targets.delete_target', group, instance)

        return instance

    class Meta:
        abstract = True
        model = Target
        fields = '__all__'
        widgets = {'type': forms.HiddenInput()}


class HourAngleTargetCreateForm(TargetForm)
    ha = CoordinateField(required=True, label='Hour Angle', c_type='ha',
                         help_text='Hour Angle, in decimal or sexagesimal hours. See '
                                   'https://docs.astropy.org/en/stable/api/astropy.coordinates.Angle.html for '
                                   'supported sexagesimal inputs.')
    dec = CoordinateField(required=True, label='Declination', c_type='dec',
                          help_text='Declination, in decimal or sexagesimal degrees. See '
                                    ' https://docs.astropy.org/en/stable/api/astropy.coordinates.Angle.html for '
                                    'supported sexagesimal inputs.')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in REQUIRED_HOUR_ANGLE_FIELDS:
            self.fields[field].required = True

    class Meta(TargetForm.Meta):
        fields = HOUR_ANGLE_FIELDS



