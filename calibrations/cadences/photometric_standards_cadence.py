from datetime import datetime, timedelta
from dateutil.parser import parse
import logging
import traceback

from django import forms
from django.conf import settings
import requests
from tom_observations.cadence import BaseCadenceForm
from tom_observations.cadences.resume_cadence_after_failure import ResumeCadenceAfterFailureStrategy
from tom_observations.facility import get_service_class
from tom_observations.models import ObservationRecord
from tom_targets.models import Target

from configdb.configdb_connections import ConfigDBInterface
from calibrations.models import Filter, FilterSet, Instrument, InstrumentFilterSet

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class PhotometricStandardsCadenceForm(BaseCadenceForm):
    instrument_code = forms.ChoiceField(required=True, choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instrument_code'].choices = [(code, code) for code in Instrument.objects.values_list('code', flat=True)]
        self.cadence_fields.update(['instrument_code', 'target_id'])


class PhotometricStandardsCadenceStrategy(ResumeCadenceAfterFailureStrategy):
    name = 'Photometric Standards Cadence Strategy'
    form = PhotometricStandardsCadenceForm
    config_db = ConfigDBInterface(settings.CONFIGDB_URL)

    def update_observation_payload(self, observation_payload):
        logger.log(msg='Updating observation_payload', level=logging.INFO)
        observation_payload['target_id'] = self.dynamic_cadence.cadence_parameters['target_id']
        return observation_payload

    def update_observation_filters(self, observation_payload):
        logger.info(msg='Updating observation_payload filters')
        instrument = Instrument.objects.get(code=self.dynamic_cadence.cadence_parameters['instrument_code'])
        #logger.info(msg=f'instrument : {instrument}')
        filter_dates = []
        logger.info(msg=f'instrumentfilter_set : {instrument.instrumentfilter_set.all()}')
        for inst_filter in instrument.instrumentfilter_set.all():
            logger.info(msg=f'inst_filter : {inst_filter}')
            filter_dates.append([inst_filter, inst_filter.get_last_calibration_age(self.dynamic_cadence.observation_group)])  # TODO: explore an annotation instead
        
        # float('inf') returns infinity, thus guaranteeing that filters with calibration age of None will be considered
        # as the oldest calibrations
        filter_dates.sort(key=lambda filters: filters[1] if filters[1] is not None else float('inf'), reverse=True)
        filters_by_calib_age = filter_dates[:3]  # change the name of "new filters" to "filter_by_age"

        for inst_filter in instrument.instrumentfilter_set.all():
            observation_payload[f'{inst_filter.filter.name}_selected'] = False

        for f in filters_by_calib_age:
            observation_payload[f'{f[0].filter.name}_selected'] = True

        return observation_payload

    def update_observation_filterset(self, observation_payload):
        logger.info(msg=f'Updating observation_payload filter set')
        instrument = Instrument.objects.get(code=self.dynamic_cadence.cadence_parameters['instrument_code'])
        #logger.info(msg=f'instrument : {instrument}')

        filterset_dates = [] 
        logger.info(msg=f'instrumentfilterset_set : {instrument.instrumentfilterset_set.all()}')
        for filter_set in instrument.instrumentfilterset_set.all(): # iterate through all filtersets on this instrument
            logger.info(msg=f'filter_set : {filter_set}')
            filterset_dates.append((filter_set, filter_set.get_last_instrumentfilterset_age(self.dynamic_cadence.observation_group)))  
            # Above: each element in the filterset_dates list is a tuple with element 1 = filterset, element 2 = age determined by get_last_instrumentfilterset_age

        filterset_dates.sort(key=lambda filterset: filterset[1] if filterset[1] is not None else float('inf'), reverse=True) # sorts by age
        # Above: float('inf') returns infinity, thus guaranteeing that filters with calibration age of None will be considered the oldest calibrations

        oldest_instrumentfilterset, age = filterset_dates[0]  # select only the oldest filterset
        #logger.info(f'oldest_instrumentfilterset : {oldest_instrumentfilterset} is {age} days old.')

        for instrument_filter_set in instrument.instrumentfilterset_set.all(): # iterate through all filtersets on this instrument
            
            for filter in instrument_filter_set.filter_set.filter_combination.all():
                observation_payload[f'{filter.name}_selected'] = False # De-select each filter in each instrument_filter_set

        for filter in oldest_instrumentfilterset.filter_set.filter_combination.all(): # iterate through each filter in the oldest filterset
            
            observation_payload[f'{filter.name}_selected'] = True # Select the filters that belong to this filterset
        
        return observation_payload
    
    def run(self):
        last_obs = self.dynamic_cadence.observation_group.observation_records.order_by('-created').first()
        target = Target.objects.get(pk=self.dynamic_cadence.cadence_parameters['target_id'])

        logger.info(f'Running PhotometricStandardsCadenceStrategy - last_obs: {last_obs}; target: {target}')

        if last_obs is not None:

            # Make sure the observation status hasn't changed at the facility since the last time we checked
            facility = get_service_class(last_obs.facility)()
            try:
                facility.update_observation_status(last_obs.observation_id)
            except requests.exceptions.HTTPError as e:
                # We didn't find an observation with the given observation_id at the facility.
                # This is proably a new cadence for a new instrument with a placeholder observation_id
                # So, just log the warning and continue.
                logger.warning(f'Could not find Observation with id:  {last_obs.observation_id}')
                logger.warning(f'Error updating observation status for {last_obs}: {type(e)} {e}')
                logger.warning(f'Continuing with most recent observation values from {last_obs.modified}')
            except Exception as e:
                logger.warning(f'Error updating observation status for {last_obs}: {type(e)} {e}')
                logger.warning(traceback.format_exc())
                logger.warning(f'Coninuing with most recent observation values from {last_obs.modified}')

            last_obs.refresh_from_db()

            observation_payload = last_obs.parameters  # copy the parameters from the previous observation

            # These boilerplate values have changed since initial observations were submitted, so we hardcode new ones
            # (i.e. the parameters copied from the previous observation may be out of date.
            # So, overwrite with new, correct values)
            # TODO: these values should not be hardcoded into the source code!!
            observation_payload['ipp_value'] = 1.0
            observation_payload['proposal'] = 'Photometric standards'  # see lco.py::LCOBaseForm.proposal_choices()

            # Boilerplate to get necessary properties for future calls
            start_keyword, end_keyword = facility.get_start_end_keywords()

        else:
            logger.info('No last_obs - creating a new cadenced observation')
            # create an observation for the new cadence, as we do not have a previous one to copy parameters from

            # TODO: the facility_settings for the service_class (the Facility) should be generalized
            #       and not hard coded like it is here
            facility = get_service_class('Photometric Standards')()
            form_class = facility.observation_forms['PHOTOMETRIC_STANDARDS']

            instrument_code = self.dynamic_cadence.cadence_parameters['instrument_code']
            inst = Instrument.objects.get(code=instrument_code)

            form_data = {
                'name': f'Photometric standard for {inst.code}',
                'facility': 'Photometric Standards',  # TODO: Do something better here
                # This proposal must match a 'current' proposal returned by lco.py::LCOBaseForm.proposal_choices()
                'proposal': self.dynamic_cadence.cadence_parameters.get('proposal', 'Photometric standards'),  # TODO: Do something better here
                'ipp_value': self.dynamic_cadence.cadence_parameters.get('ipp_value', 1.0),  # TODO: is this right?
                'instrument_type': inst.type,
                'observation_type': 'PHOTOMETRIC_STANDARDS',
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
                'g_narrowband': 'out',
                'r_narrowband': 'out',
                'i_narrowband': 'out',
                'z_narrowband': 'out'
            }

            inst_filters = inst.instrumentfilter_set.all()
            for f in inst_filters:
                form_data[f'{f.filter.name}_exposure_count'] = f.filter.exposure_count
                form_data[f'{f.filter.name}_exposure_time'] = f.filter.exposure_time

            if inst_filters:
                form_data[f'{inst_filters[0].filter.name}_selected'] = True
            else:
                logger.warning(f'No instrument filters found for {inst.code}')

            # instanciate a new form with the form_data for the new cadence
            form = form_class(data=form_data)

            logger.info(f'calling form.is_valid() with form_data for a new cadence: {form_data}')
            form_is_valid = False
            try:
                form_is_valid = form.is_valid()
            except Exception as e:
                logger.error(f'Error validating initial calibration form: {type(e)} {e}')
                logger.error(f'initial calibration form errors: {form.errors.as_data()}')

            if form_is_valid:
                logger.debug(f'Passed first form validity check')
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
                logger.error(f'Unable to submit initial calibration for new cadence {self.dynamic_cadence.id}',
                             extra={'tags': {
                                    'dynamic_cadence_id': self.dynamic_cadence.id,
                                    'target': target.name,
                                    'form.errors': form.errors.as_data()}
                                    })
                raise forms.ValidationError(f'Unable to submit initial calibration for cadence {self.dynamic_cadence}')

        # Cadence logic
        if last_obs is not None and not last_obs.terminal:
            # If the observation hasn't finished, do nothing
            return
        elif last_obs is not None and last_obs.failed:
            # If the observation failed,
            # then Submit next observation to be taken as soon as possible with the same window length
            window_length = parse(observation_payload[end_keyword]) - parse(observation_payload[start_keyword])
            observation_payload[start_keyword] = datetime.now().isoformat()
            observation_payload[end_keyword] = (parse(observation_payload[start_keyword]) + window_length).isoformat()
        else:
            # If the observation succeeded,
            # then advance window normally according to cadence parameters
            observation_payload = self.advance_window(
                observation_payload, start_keyword=start_keyword, end_keyword=end_keyword
            )
            #observation_payload = self.update_observation_filters(observation_payload)
            observation_payload = self.update_observation_filterset(observation_payload)

        observation_payload = self.update_observation_payload(observation_payload)

        form_class = facility.get_form('PHOTOMETRIC_STANDARDS')
        converted_observation_payload = form_class().convert_old_observation_payload_to_fields(observation_payload)

        # Submission of the new observation to the facility
        form = form_class(converted_observation_payload)

        logger.info((f'Observation form data to be validated and subitted for {self.dynamic_cadence.id}:'
                     f' {converted_observation_payload}'),
                    extra={'tags': {
                        'dynamic_cadence_id': self.dynamic_cadence.id,
                        'target': target.name
                    }})

        form_is_valid = False
        try:
            form_is_valid = form.is_valid()
        except Exception as e:
            logger.error(f'form.is_valid() raised {type(e)}: {e}')
            logger.error(traceback.format_exc())

        if form_is_valid:
            observation_ids = facility.submit_observation(form.observation_payload())
        else:
            logger.error(f'Unable to submit next cadenced observation: {form.errors.as_data()}',
                         extra={'tags': {
                            'dynamic_cadence_id': self.dynamic_cadence.id,
                            'target': target.name
                         }})
            raise Exception(f'Unable to submit next cadenced observation: {form.errors.as_data()}')

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
                facility = get_service_class(observation.facility)()#(facility_settings=OCSSettings('LCO'))
                facility.update_observation_status(observation.observation_id)
            except Exception as e:
                logger.error(msg=f'Unable to update observation status for {observation}. Error: {e}')

        return new_observations
