from collections import namedtuple

from crispy_forms.layout import Div, HTML
from django import forms

from tom_observations.facilities.lco import LCOBaseObservationForm, LCOFacility


class NRESCalibrationForm(LCOBaseObservationForm):
    nres_sites = ['cpt', 'lsc', 'elp', 'tlv']

    # The first item in the tuple is the form value, the second is the display value
    site = forms.ChoiceField(choices=[(site, site) for site in nres_sites])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.fields['ipp_value'].widget = forms.HiddenInput()

    def proposal_choices(self):
        # TODO: decide whether to limit proposal choices or prefill with initial value
        return super().proposal_choices()

    def layout(self):
        # TODO: Fix layout to be better
        layout = super().layout()
        layout.append(Div('site'))
        return layout

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


class LCOCalibrationFacility(LCOFacility):
    name = 'LCO Calibrations'
    observation_forms = {
        'NRES': NRESCalibrationForm
    }
