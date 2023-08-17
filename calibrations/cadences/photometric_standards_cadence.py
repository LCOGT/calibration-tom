from datetime import datetime, timedelta
from dateutil.parser import parse
import logging

from django import forms
from django.conf import settings
from tom_observations.cadence import BaseCadenceForm
from tom_observations.cadences.resume_cadence_after_failure import ResumeCadenceAfterFailureStrategy
from tom_observations.facility import get_service_class
from tom_observations.facilities.ocs import OCSSettings
from tom_observations.models import ObservationRecord
from tom_targets.models import Target

from configdb.configdb_connections import ConfigDBInterface
from calibrations.models import Filter, Instrument, InstrumentFilter

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
        filter_dates = []
        for inst_filter in instrument.instrumentfilter_set.all():
            filter_dates.append([inst_filter, inst_filter.get_last_calibration_age(self.dynamic_cadence.observation_group)])  # TODO: explore an annotation instead

        # float('inf') returns infinity, thus guaranteeing that filters with calibration age of None will be considered
        # as the oldest calibrations
        filter_dates.sort(key=lambda filters: filters[1] if filters[1] is not None else float('inf'), reverse=True)
        filters_by_calib_age = filter_dates[:2]  # change the name of "new filters" to "filter_by_age"

        for inst_filter in instrument.instrumentfilter_set.all():
            observation_payload[f'{inst_filter.filter.name}_selected'] = False

        for f in filters_by_calib_age:
            observation_payload[f'{f[0].filter.name}_selected'] = True

        return observation_payload

    def run(self):
        logger.debug('Running Photometric Standards Cadence Strategy')

        last_obs = self.dynamic_cadence.observation_group.observation_records.order_by('-created').first()
        target = Target.objects.get(pk=self.dynamic_cadence.cadence_parameters['target_id'])

        logger.debug(f'Running Photometric Standards Cadence Strategy - last_obs: {last_obs}')
        logger.debug(f'Running Photometric Standards Cadence Strategy - target: {target}')

        if last_obs is not None:
            #logger.debug(f'Progress flag: last_obs is not None\n')
            #This is an on-going (not first-run) cadence
            facility = get_service_class(last_obs.facility)(facility_settings=OCSSettings('LCO'))
            logger.debu(f'facility for OLD cadence: {facility}')

            facility.update_observation_status(last_obs.observation_id)
            
            last_obs.refresh_from_db()
            
            observation_payload = last_obs.parameters  # copy the parameters from the previous observation
            

            # These boilerplate values have changed since initial observations were submitted, so we hardcode new ones
            # (i.e. the parameters copied from the previous observation may be out of date. So, overwrite with new, correct values)
            # TODO: these values should not be hardcoded into the source code!!
            observation_payload['ipp_value'] = 1.0
            observation_payload['proposal'] = 'Photometric standards'  # see lco.py::LCOBaseForm.proposal_choices()

            # Boilerplate to get necessary properties for future calls
            start_keyword, end_keyword = facility.get_start_end_keywords()
            
        else:
            # create an observation for the new cadence, as we do not have a previous one to copy parameters from

            # TODO: the facility_settings for the service_class (the Facility) should be generalized
            #       and not hard coded like it is here
            facility = get_service_class('Photometric Standards')(facility_settings=OCSSettings('LCO'))
            logger.debug(f'facility for NEW cadence: {facility}')
            form_class = facility.observation_forms['PHOTOMETRIC_STANDARDS']

            instrument_code = self.dynamic_cadence.cadence_parameters['instrument_code']
            inst = Instrument.objects.get(code=instrument_code)
            logger.debug(f'inst code for NEW cadence: {instrument_code}')
            logger.debug(f'inst for NEW cadence: {inst}')
            inst_filters = inst.instrumentfilter_set.all()
            logger.debug(f'inst_filters = {inst_filters}') # e.g. mc03 - g

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
                'diffusers': 'Out',  # TODO: should we still have these on the facility?
                'g_diffuser': 'Out',
                'r_diffuser': 'Out',
                'i_diffuser': 'Out',
                'z_diffuser': 'Out'
            }
            logger.debug(f'form_data 1:{form_data}')

            for f in inst_filters:
                form_data[f'{f.filter.name}_exposure_count'] = f.filter.exposure_count
                #logger.debug(f"exposure count = {form_data[f'{f.filter.name}_exposure_count']}\n")
                form_data[f'{f.filter.name}_exposure_time'] = f.filter.exposure_time
                #logger.debug(f"exposure time = {form_data[f'{f.filter.name}_exposure_time']}\n")

            # if ist_filters[0] is NoneType, this is a problem.
            form_data[f'{inst_filters[0].filter.name}_selected'] = True

            logger.debug(f'form_data 2:{form_data}')
            #logger.debug(f'Progress flag: Form data created.\n')

            #logger.debug(f"Progress flag: Here's the first form validity check\n")
            form = form_class(data=form_data)
            logger.debug(f'form: {form}')

            form.is_valid()
            if form.is_valid():
                #logger.debug(f"Progress flag: Passed first form validity check\n")
                # form.is_valid() produces cleaned_data, but cleaned_data modifies the structure of the data
                # As a result, we set observation_payload to form_data, so it can be further modified before form
                # submission (this is specifically due to the FilterMultiValueField)
                observation_payload = form_data

                # Because we're using the form_data rather than the cleaned_data, the start/end values need to be
                # converted to strings, or errors will be raised later on
                start_keyword, end_keyword = facility.get_start_end_keywords()
                observation_payload[start_keyword] = observation_payload[start_keyword].isoformat()
                observation_payload[end_keyword] = observation_payload[end_keyword].isoformat()
                logger.debug(f'observation_payload 1: {observation_payload}')
            else:
                logger.error(f'Unable to submit initial calibration for cadence {self.dynamic_cadence.id}', extra={
                    'tags': {'dynamic_cadence_id': self.dynamic_cadence.id, 'target': target.name}
                })
                raise forms.ValidationError(f'Unable to submit initial calibration for cadence {self.dynamic_cadence}')

        # Cadence logic
        # If the observation hasn't finished, do nothing
        if last_obs is not None and not last_obs.terminal:
            #logger.debug(f"Progress flag: last_obs is still not None\n")
            return
        elif last_obs is not None and last_obs.failed:  # If the observation failed
            #logger.debug(f"Progress flag: last_obs is really still not None\n")
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
        logger.debug(f'observation_payload 2: {observation_payload}')

        # Submission of the new observation to the facility
        form = facility.get_form('PHOTOMETRIC_STANDARDS')(observation_payload)
        #logger.debug(f"observation_payload 1 = {observation_payload}\n")
        logger.info(f'Observation form data to be submitted for {self.dynamic_cadence.id}: {observation_payload}',
                    extra={'tags': {
                        'dynamic_cadence_id': self.dynamic_cadence.id,
                        'target': target.name
                    }})
        #logger.debug(f"Progress flag: Here's the second form validity check\n")
        # logger.debug(f'Valid2? = {form.is_valid()}\n')        
        if form.is_valid():
            #logger.debug(f"Progress flag: Passed second form valiity check\n")
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
                facility = get_service_class(observation.facility)(facility_settings=OCSSettings('LCO'))
                facility.update_observation_status(observation.observation_id)
            except Exception as e:
                logger.error(msg=f'Unable to update observation status for {observation}. Error: {e}')

        return new_observations
