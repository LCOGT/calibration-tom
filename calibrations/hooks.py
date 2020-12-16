import logging

logger = logging.getLogger(__name__)


def observation_change_state(observation, previous_state):
    logger.info('Observation change state hook: %s from %s to %s', observation, previous_state, observation.status)

    # NRES RV calibration observation state change.
    # NOTE: this could be extracted into a method if desired

    facility_for_observation = observation  # TODO: get facility from observation
    if observation.status == 'COMPLETED':
        # TODO: 1 create DataProduct
        # create DataProduct for observation - this will trigger a FITS download from the archive

        # TODO: 2 trigger spectroscopic_processing
        # trigger spectroscopic_processing to create a ReducedDatum record

        pass

