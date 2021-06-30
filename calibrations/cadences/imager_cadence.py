from tom_observations.cadence import BaseCadenceForm
from tom_observations.cadences.resume_cadence_after_failure import ResumeCadenceAfterFailureStrategy


class ImagerCadenceForm(BaseCadenceForm):
    pass


class ImagerCadenceStrategy(ResumeCadenceAfterFailureStrategy):
    name = 'Imager Cadence Strategy'
    form = ImagerCadenceForm
