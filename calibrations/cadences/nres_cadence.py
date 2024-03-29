from datetime import datetime
from dateutil.parser import parse
import logging

from crispy_forms.layout import Column, Div, HTML, Layout, Row
from django import forms
from django.conf import settings

from tom_observations.cadence import BaseCadenceForm
from tom_observations.cadences.resume_cadence_after_failure import ResumeCadenceAfterFailureStrategy
from tom_observations.facility import get_service_class
from tom_observations.models import ObservationRecord
from tom_targets.models import Target

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
        target = Target.objects.get(pk=self.dynamic_cadence.cadence_parameters['target_id'])

        logger.debug(f'NRESCadenceStrategy.run() last_obs: {last_obs}')

        if last_obs is not None:
            # Make a call to the facility to get the current status of the observation
            facility = get_service_class(last_obs.facility)()
            form_class = facility.observation_forms['NRES']
            standard_type = target.targetextra_set.filter(key='standard_type').first().value
            site = self.dynamic_cadence.cadence_parameters['site']

            form_data = {
                'name': f'NRES {standard_type} calibration for {site.upper()}',
                'observation_type': 'NRES',
                'observation_mode': 'NORMAL',
                'instrument_type': '1M0-NRES-SCICAM',
                'cadence_frequency': self.dynamic_cadence.cadence_parameters['cadence_frequency'],
                'site': site,
                'target_id': self.dynamic_cadence.cadence_parameters['target_id'],
                'facility': 'LCO Calibrations',
                'proposal': 'NRES standards',
                'ipp_value': 1.0,
                'filter': 'air',
                'exposure_time': target.targetextra_set.filter(key='exp_time').first().value,
                'exposure_count': target.targetextra_set.filter(key='exp_count').first().value,
                'max_airmass': 2,
                'start': datetime.now()
            }
            min_lunar_distance = target.targetextra_set.filter(key='min_lunar_distance').first()
            if min_lunar_distance is not None:
                form_data['min_lunar_distance'] = min_lunar_distance.value

            # add the form_data to the form_class: form = form_class instanciated with form_data
            form = form_class(data=form_data)

            logger.debug(f'calling form.is_valid() with form_data: {form_data}')
            form_is_valid = False
            try:
                form_is_valid = form.is_valid()
            except Exception as e:
                logger.error(f'Error validating calibration form: {type(e)} {e}')
                logger.error(f'calibration form errors: {form.errors.as_data()}')

            if form_is_valid:
                observation_payload = form.cleaned_data
            else:
                logger.error(f'Unable to submit initial calibration for cadence {self.dynamic_cadence.id}', extra={
                    'tags': {'dynamic_cadence_id': self.dynamic_cadence.id, 'target': target.name}
                })
                raise forms.ValidationError(f'Unable to submit initial calibration for cadence {self.dynamic_cadence}')

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

        observation_payload = self.update_observation_payload(observation_payload)

        # Submission of the new observation to the facility
        # obs_type = last_obs.parameters.get('observation_type')
        # form = facility.get_form(obs_type)(observation_payload)
        form = facility.get_form('NRES')(observation_payload)
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
            raise Exception(f'Unable to submit next cadenced observation due form.errors: {form.errors.as_data()}')

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
