from datetime import datetime, timedelta
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
from calibrations.models import Filter, Instrument, InstrumentFilter

logger = logging.getLogger(__name__)


class ImagerCadenceForm(BaseCadenceForm):
    instrument_code = forms.ChoiceField(required=True, choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instrument_code'].choices = [(code, code) for code in Instrument.objects.values_list('code', flat=True)]
        self.cadence_fields.update(['instrument_code', 'target_id'])


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
        instrument = Instrument.objects.get(code=self.dynamic_cadence.cadence_parameters['instrument_code'])
        filter_dates = []
        for inst_filter in instrument.instrumentfilter_set.all():
            filter_dates.append([inst_filter, inst_filter.get_last_calibration_age(self.dynamic_cadence.observation_group)])  # TODO: explore an annotation instead
        filter_dates.sort(key=lambda filters: filters[1] if filters[1] is not None else datetime.now())
        filters_by_calib_age = filter_dates[:2]  # change the name of "new filters" to "filter_by_age"

        for inst_filter in instrument.instrumentfilter_set.all():
            observation_payload[f'{inst_filter.filter.name}_selected'] = False

        for f in filters_by_calib_age:
            observation_payload[f'{f[0].filter.name}_selected'] = True

        return observation_payload

    def run(self):
        last_obs = self.dynamic_cadence.observation_group.observation_records.order_by('-created').first()
        target = Target.objects.get(pk=self.dynamic_cadence.cadence_parameters['target_id'])

        if last_obs is not None:
            facility = get_service_class(last_obs.facility)()
            facility.update_observation_status(last_obs.observation_id)
            last_obs.refresh_from_db()
            observation_payload = last_obs.parameters

            # Boilerplate to get necessary properties for future calls
            start_keyword, end_keyword = facility.get_start_end_keywords()
        else:
            # create an observation for the new cadence, as we do not have a previous one to use
            facility = get_service_class('Imager Calibrations')()
            form_class = facility.observation_forms['IMAGER']

            inst = Instrument.objects.get(code=self.dynamic_cadence.cadence_parameters['instrument_code'])
            inst_filters = inst.instrumentfilter_set.all()

            form_data = {
                'name': f'Photometric standard for {inst.code}',
                'facility': 'Imager Calibrations',  # TODO: Do something better here
                'proposal': self.dynamic_cadence.cadence_parameters.get('proposal', 'standard'),  # TODO: Do something better here
                'ipp_value': self.dynamic_cadence.cadence_parameters.get('ipp_value', 1.05),  # TODO: is this right?
                'instrument_type': inst.type,
                'observation_type': 'IMAGER',
                'observation_mode': 'NORMAL',
                'cadence_frequency': self.dynamic_cadence.cadence_parameters['cadence_frequency'],
                'site': inst.site,
                'enclosure': inst.enclosure,
                'telescope': inst.telescope,
                'instrument': inst.code,
                'target_id': target.id,
                'max_airmass': self.dynamic_cadence.cadence_parameters.get('max_airmass', 3),
                'min_lunar_distance': self.dynamic_cadence.cadence_parameters.get('min_lunar_distance', 20),
                'start': datetime.now(),
                'end': datetime.now() + timedelta(hours=self.dynamic_cadence.cadence_parameters['cadence_frequency']),
                'diffusers': 'Out',  # TODO: should we still have these on the facility?
                'g_diffuser': 'Out',
                'r_diffuser': 'Out',
                'i_diffuser': 'Out',
                'z_diffuser': 'Out'
            }

            for f in inst_filters:
                form_data[f'{f.filter.name}_exposure_count'] = f.filter.exposure_count
                form_data[f'{f.filter.name}_exposure_time'] = f.filter.exposure_time
            form_data[f'{inst_filters[0].filter.name}_selected'] = True

            form = form_class(data=form_data)
            if form.is_valid():
                # form.is_valid() produces cleaned_data, but cleaned_data modifies the structure of the data
                # As a result, we set observation_payload to form_data, so it can be further modified before form
                # submission (this is specifically due to the FilterMultiValueField)
                observation_payload = form_data

                # Because we're using the form_data rather than the cleaned_data, the start/end values need to be
                # converted to strings, or errors will be raised later on
                start_keyword, end_keyword = facility.get_start_end_keywords()
                observation_payload[start_keyword] = observation_payload[start_keyword].isoformat()
                observation_payload[end_keyword] = observation_payload[end_keyword].isoformat()
            else:
                logger.error(f'Unable to submit initial calibration for cadence {self.dynamic_cadence.id}', extra={
                    'tags': {'dynamic_cadence_id': self.dynamic_cadence.id, 'target': target.name}
                })
                raise forms.ValidationError(f'Unable to submit initial calibration for cadence {self.dynamic_cadence}')

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
        form = facility.get_form('IMAGER')(observation_payload)
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
