from crispy_forms.layout import Column, Div, HTML, Layout, Row
from django import forms

from tom_observations.cadence import BaseCadenceForm
from tom_observations.cadences.resume_cadence_after_failure import ResumeCadenceAfterFailureStrategy


NRES_SITES = ['cpt', 'lsc', 'elp', 'tlv']  # TODO: This should go in settings.py or be pulled from ConfigDB


class NRESCadenceForm(BaseCadenceForm):
    site = forms.ChoiceField(required=True, choices=[(site, site) for site in NRES_SITES])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cadence_fields.update(['site', 'target_id'])  # self.cadence_fields is a set

    def cadence_layout(self):
        return Layout(
                Div(
                    HTML('<p>Dynamic cadencing parameters. Leave blank if no dynamic cadencing is desired.</p>'),
                ),
                Row(Column('site')),
                Row(Column('cadence_strategy'), Column('cadence_frequency')),
            )


class NRESCadenceStrategy(ResumeCadenceAfterFailureStrategy):
    """The ResumeCadenceAfterFailureStrategy chooses when to submit the next observation based on the success of the
    previous observation. If the observation is successful, it submits a new one on the same cadence--that is, if the
    cadence is every three days, it will submit the next observation three days in the future. If the observations
    fails, it will submit the next observation immediately, and follow the same decision tree based on the success
    of the subsequent observation.

    For the NRES Cadence Strategy, this will need to ensure that observations for a site are grouped together, not
    simply per target."""

    name = 'NRES Cadence Strategy'
    description = """This strategy schedules one observation in the cadence at a time. If the observation fails, it
                     re-submits the observation until it succeeds. If it succeeds, it submits the next observation on
                     the same cadence."""
    form = NRESCadenceForm

    def update_observation_payload(self, observation_payload):
        observation_payload['target_id'] = self.dynamic_cadence.cadence_parameters['target_id']
        return observation_payload
