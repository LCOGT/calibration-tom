from datetime import datetime, timedelta
from dateutil.parser import parse
import json
import logging

from django import forms

from tom_observations.cadence import BaseCadenceForm, CadenceStrategy
from tom_observations.models import ObservationRecord
from tom_observations.facility import get_service_class


logger = logging.getLogger(__name__)


class ResumeCadenceAfterFailureForm(BaseCadenceForm):
    pass


class ResumeCadenceAfterFailureStrategy(CadenceStrategy):
    """The ResumeCadenceAfterFailureStrategy chooses when to submit the next observation based on the success of the
    previous observation. If the observation is successful, it submits a new one on the same cadence--that is, if the
    cadence is every three days, it will submit the next observation three days in the future. If the observations
    fails, it will submit the next observation immediately, and follow the same decision tree based on the success
    of the subsequent observation.

    In order to properly subclass this CadenceStrategy, one should override ``update_observation_payload``.

    This strategy requires the DynamicCadence to have a parameter ``cadence_frequency``."""

    name = 'Resume Cadence After Failure'
    description = """This strategy schedules one observation in the cadence at a time. If the observation fails, it
                     re-submits the observation until it succeeds. If it succeeds, it submits the next observation on
                     the same cadence."""
    form = ResumeCadenceAfterFailureForm

    class ResumeCadenceForm(forms.Form):
        site = forms.CharField()

    def update_observation_payload(self, observation_payload):
        """
        :param observation_payload: form parameters for facility observation form
        :type observation_payload: dict
        """
        return observation_payload

    def run(self):
        logger.log(msg='Running cadence strategy resume_cadence_after_failure', level=logger.INFO)
        # gets the most recent observation because the next observation is just going to modify these parameters
        last_obs = self.dynamic_cadence.observation_group.observation_records.order_by('-created').first()
        logger.log(msg=f'Last obs id: {last_obs.id}')

        # Make a call to the facility to get the current status of the observation
        facility = get_service_class(last_obs.facility)()
        facility.update_observation_status(last_obs.observation_id)  # Updates the DB record
        last_obs.refresh_from_db()  # Gets the record updates

        logger.log(msg=f'Last obs status: {last_obs.status}')
        # Boilerplate to get necessary properties for future calls
        start_keyword, end_keyword = facility.get_start_end_keywords()
        observation_payload = last_obs.parameters_as_dict
        logger.log(msg=f'Last obs payload: {observation_payload}')

        # Cadence logic
        # If the observation hasn't finished, do nothing
        if not last_obs.terminal:
            logger.log(msg='Observation incomplete, do nothing', level=logger.INFO)
            return
        elif last_obs.failed:  # If the observation failed
            logger.log(msg='Observation failed, resubmit immediately', level=logger.INFO)
            # Submit next observation to be taken as soon as possible with the same window length
            window_length = parse(observation_payload[end_keyword]) - parse(observation_payload[start_keyword])
            observation_payload[start_keyword] = datetime.now().isoformat()
            observation_payload[end_keyword] = (parse(observation_payload[start_keyword]) + window_length).isoformat()
        else:  # If the observation succeeded
            logger.log(msg='Observation complete, submit according to cadence', level=logger.INFO)
            # Advance window normally according to cadence parameters
            observation_payload = self.advance_window(
                observation_payload, start_keyword=start_keyword, end_keyword=end_keyword
            )

        observation_payload = self.update_observation_payload(observation_payload)
        logger.log(msg=f'New observation payload: {observation_payload}')

        # Submission of the new observation to the facility
        obs_type = last_obs.parameters_as_dict.get('observation_type')
        form = facility.get_form(obs_type)(observation_payload)
        form.is_valid()
        logger.log(msg=f'Form valid: {form.is_valid()}')
        observation_ids = facility.submit_observation(form.observation_payload())

        logger.log(msg=f'New observation ids: {observation_ids}')
        # Creation of corresponding ObservationRecord objects for the observations
        new_observations = []
        for observation_id in observation_ids:
            # Create Observation record
            record = ObservationRecord.objects.create(
                target=last_obs.target,
                facility=facility.name,
                parameters=json.dumps(observation_payload),
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

    def advance_window(self, observation_payload, start_keyword='start', end_keyword='end'):
        cadence_frequency = self.dynamic_cadence.cadence_parameters.get('cadence_frequency')
        if not cadence_frequency:
            raise Exception(f'The {self.name} strategy requires a cadence_frequency cadence_parameter.')
        advance_window_hours = cadence_frequency
        new_start = parse(observation_payload[start_keyword]) + timedelta(hours=advance_window_hours)
        new_end = parse(observation_payload[end_keyword]) + timedelta(hours=advance_window_hours)
        observation_payload[start_keyword] = new_start.isoformat()
        observation_payload[end_keyword] = new_end.isoformat()

        return observation_payload
