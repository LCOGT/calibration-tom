from datetime import datetime
from dateutil.parser import parse
import logging

from crispy_forms.layout import Column, Div, HTML, Layout, Row
from django import forms
from django.conf import settings

from tom_observations.cadence import BaseCadenceForm
from tom_observations.cadences.resume_cadence_after_failure import ResumeCadenceAfterFailureStrategy
from tom_observations.facility import get_service_class

logger = logging.getLogger(__name__)


class NRESCadenceForm(BaseCadenceForm):
    # TODO: maybe initialize choices in the init in a try/except?
    site = forms.ChoiceField(required=True, choices=[(site, site) for site in settings.NRES_SITES])

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
        logger.log(msg='Updating observation_payload', level=logging.INFO)
        observation_payload['target_id'] = self.dynamic_cadence.cadence_parameters['target_id']
        return observation_payload

    def run(self):
        # gets the most recent observation because the next observation is just going to modify these parameters
        last_obs = self.dynamic_cadence.observation_group.observation_records.order_by('-created').first()

        if last_obs is not None:
            # Make a call to the facility to get the current status of the observation
            facility = get_service_class(last_obs.facility)()
            facility.update_observation_status(last_obs.observation_id)  # Updates the DB record
            last_obs.refresh_from_db()  # Gets the record updates
            observation_payload = last_obs.parameters
        else:
            # We need to create an observation for the new cadence, as we do not have a previous one to use
            form_class = get_service_class('LCO Calibrations')().observation_forms['NRES']
            form = form_class(data={
                'cadence_frequency': self.dynamic_cadence.cadence_parameters['cadence_frequency'],
                'site': self.dynamic_cadence.cadence_parameters['site'],
                'target_id': self.dynamic_cadence.cadence_parameters['target_id'],
            })
            if form.is_valid():
                observation_payload = form.cleaned_data
            else:
                logger.error(f'Unable to submit initial calibration for cadence {self.dc.id}')
                raise forms.ValidationError(f'Unable to submit initial calibration for cadence {self.dc}')

        # Boilerplate to get necessary properties for future calls
        start_keyword, end_keyword = facility.get_start_end_keywords()

        # Cadence logic
        # If the observation hasn't finished, do nothing
        if not last_obs.terminal:
            return
        elif last_obs.failed:  # If the observation failed
            # Submit next observation to be taken as soon as possible with the same window length
            window_length = parse(observation_payload[end_keyword]) - parse(observation_payload[start_keyword])
            observation_payload[start_keyword] = datetime.now().isoformat()
            observation_payload[end_keyword] = (parse(observation_payload[start_keyword]) + window_length).isoformat()
        else:  # If the observation succeeded
            # Advance window normally according to cadence parameters
            observation_payload = self.advance_window(
                observation_payload, start_keyword=start_keyword, end_keyword=end_keyword
            )

        observation_payload = self.update_observation_payload(observation_payload)

        # Submission of the new observation to the facility
        obs_type = last_obs.parameters.get('observation_type')
        form = facility.get_form(obs_type)(observation_payload)
        if form.is_valid():
            observation_ids = facility.submit_observation(form.observation_payload())
        else:
            logger.error(msg=f'Unable to submit next cadenced observation: {form.errors}')
            raise Exception(f'Unable to submit next cadenced observation: {form.errors}')

        # Creation of corresponding ObservationRecord objects for the observations
        new_observations = []
        for observation_id in observation_ids:
            # Create Observation record
            record = ObservationRecord.objects.create(
                target=last_obs.target,
                facility=facility.name,
                parameters=observation_payload,
                observation_id=observation_id
            )
            # Add ObservationRecords to the DynamicCadence
            self.dynamic_cadence.observation_group.observation_records.add(record)
            self.dynamic_cadence.observation_group.save()
            new_observations.append(record)

        # Update the status of the ObservationRecords in the DB
        for obsr in new_observations:
            facility = get_service_class(obsr.facility)()
            facility.update_observation_status(obsr.observation_id)

        return new_observations
