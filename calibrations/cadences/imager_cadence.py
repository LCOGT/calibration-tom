import copy
from datetime import datetime
from dateutil.parser import parse
import logging

from django import forms
from django.conf import settings
from tom_observations.cadence import BaseCadenceForm
from tom_observations.cadences.resume_cadence_after_failure import ResumeCadenceAfterFailureStrategy
from tom_observations.facility import get_service_class
from tom_observations.models import ObservationRecord
from tom_targets.models import Target

from configdb.configdb_connections import ConfigDBInterface

logger = logging.getLogger(__name__)


class ImagerCadenceForm(BaseCadenceForm):
    site = forms.ChoiceField(required=True, choices=[(site, site) for site in settings.NRES_SITES])  # TODO: update with new sites setting
    instrument_code = forms.ChoiceField(required=True, choices=[])  # TODO: update with all instruments


class ImagerCadenceStrategy(ResumeCadenceAfterFailureStrategy):
    name = 'Imager Cadence Strategy'
    form = ImagerCadenceForm
    config_db = ConfigDBInterface(settings.CONFIGDB_URL)

    def update_observation_payload(self, observation_payload):
        logger.log(msg='Updating observation_payload', level=logging.INFO)
        observation_payload['target_id'] = self.dynamic_cadence.cadence_parameters['target_id']
        return observation_payload

    def update_observation_filters(self, observation_payload):
        logger.info(msg='Updating observation_payload filters')
        site = self.dynamic_cadence.cadence_parameters['site']
        instrument_code = self.dynamic_cadence.cadence_parameters['instrument_code']
        available_filters = {inst['code']: inst['code']
                             for inst
                             in (self.config_db.get_matching_instrument(site_code=site, instrument_name=instrument_code)
                                 .get('optical_elements', [{}]).get('optical_elements', []))
                             if inst['type'] == 'filters'}
        filters_copy = copy(available_filters)
        observation_records = self.dynamic_cadence.observation_group.observation_records.order_by('-created')
        for 



    def run(self):
        last_obs = self.dynamic_cadence.observation_group.observation_records.order_by('-created').first()
        target = Target.objects.get(pk=self.dynamic_cadence.cadence_parameters['target_id'])

        if last_obs is not None:
            facility = get_service_class(last_obs.facility)()
            facility.update_observation_status(last_obs.observation_id)
            last_obs.refresh_from_db()
            observation_payload = last_obs.parameters
        else:
            pass  # create an observation for the new cadence, as we do not have a previous one to use
            # facility = get_service_class('LCO Calibrations')()
            # form_class = facility.observation_forms['Imager Calibrations']

            # site = self.dynamic_cadence.cadence_parameters['site']

            # form_data = {
            #     'name': f'',
            #     'observation_types': 'IMAGER',
            #     'observation_mode': 'NORMAL',
            #     # 'instrument_type': ,
            #     'cadence_frequency': self.dynamic_cadence.cadence_parameters['cadence_frequency'],
            #     'site': site,
            # }

        # Boilerplate to get necessary properties for future calls
        start_keyword, end_keyword = facility.get_start_end_keywords()

        # Cadence logic
        # If the observation hasn't finished, do nothing
        if last_obs is not None and not last_obs.terminal:
            return
        elif last_obs is not None and last_obs.failed:  # If the observation failed
            # Submit next observation to be taken as soon as possible with the same window length
            window_length = parse(observation_payload[end_keyword]) - parse(observation_payload[start_keyword])
            observation_payload[start_keyword] = datetime.now().isoformat()
            observation_payload[end_keyword] = (parse(observation_payload[start_keyword]) + window_length).isoformat()
        else:  # If the observation succeeded
            # Advance window normally according to cadence parameters
            observation_payload = self.advance_window(
                observation_payload, start_keyword=start_keyword, end_keyword=end_keyword
            )
            observation_payload = self.update_observation_filters(observation_payload)
            

        observation_payload = self.update_observation_payload(observation_payload)

        # Submission of the new observation to the facility
        form = facility.get_form('Imager Calibrations')(observation_payload)
        logger.info(f'Observation form data to be submitted for {self.dynamic_cadence.id}: {observation_payload}',
                    extra={'tags': {
                        'dynamic_cadence_id': self.dynamic_cadence.id,
                        'target': target.name
                    }})
        if form.is_valid():
            observation_ids = facility.submit_observation(form.observation_payload())
        else:
            logger.error(f'Unable to submit next cadenced observation: {form.errors}',
                         extra={'tags': {
                            'dynamic_cadence_id': self.dynamic_cadence.id,
                            'target': target.name
                         }})
            raise Exception(f'Unable to submit next cadenced observation: {form.errors}')

        # Creation of corresponding ObservationRecord objects for the observations
        new_observations = []
        for observation_id in observation_ids:
            # Create Observation record
            record = ObservationRecord.objects.create(
                target=target,
                facility=facility.name,
                parameters=observation_payload,
                observation_id=observation_id
            )
            # Add ObservationRecords to the DynamicCadence
            self.dynamic_cadence.observation_group.observation_records.add(record)
            self.dynamic_cadence.observation_group.save()
            new_observations.append(record)

        # Update the status of the ObservationRecords in the DB
        for observation in new_observations:
            logger.info(f'Updating new cadence observation status for {observation}',
                        extra={'tags': {
                            'dynamic_cadence_id': self.dynamic_cadence.id,
                            'target': target.name,
                            'observation_id': observation.observation_id,
                        }})
            try:
                facility = get_service_class(observation.facility)()
                facility.update_observation_status(observation.observation_id)
            except Exception as e:
                logger.error(msg=f'Unable to update observation status for {observation}. Error: {e}')

        return new_observations
