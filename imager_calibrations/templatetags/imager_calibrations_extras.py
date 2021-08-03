from django import template
from django.core.exceptions import ObjectDoesNotExist
from tom_observations.models import DynamicCadence, ObservationRecord

from calibrations.models import InstrumentFilter


register = template.Library()


@register.filter
def inst_in_filter_data(inst_filters, inst):  # TODO: rename this
    try:
        last_calibration_age = inst_filters.get(instrument__code=inst.code).get_last_calibration_age()
        if not last_calibration_age:
            return 'Never'
        return last_calibration_age
    except ObjectDoesNotExist:
        return ''


@register.filter
def css_color(filter_name, inst):
    try:
        calibration_age = InstrumentFilter.objects.get(
                            instrument=inst, filter__name=filter_name
                          ).get_last_calibration_age()
    except ObjectDoesNotExist:
        return ''

    if calibration_age <= 6:
        return 'green'
    elif calibration_age > 6 and calibration_age < 13:
        return 'yellow'
    elif calibration_age >= 13:
        return 'red'


@register.inclusion_tag('imager_calibrations/partials/instrument_filters_at_site.html')
def instrument_filter_at_site(instrument):  # TODO: make this take context
    instrument_data = {'instrument': instrument, 'filter_data': {}}
    inst_filters = InstrumentFilter.objects.filter(instrument=instrument)
    instrument_data['filter_data'] = inst_filters
    return instrument_data


@register.inclusion_tag('imager_calibrations/partials/instrument_observations_at_site.html')
def instrument_observations_at_site(instrument):  # TODO: make this take context
    try:
        cadence = DynamicCadence.objects.get(active=True, cadence_parameters__instrument_code=instrument.code)
    except ObjectDoesNotExist:
        return {}  # TODO: make this more robust
    records = cadence.observation_group.observation_records.order_by('-created')[:10]
    return {'observation_records': records}
