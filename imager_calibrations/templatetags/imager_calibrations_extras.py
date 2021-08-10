from django import template
from django.core.exceptions import ObjectDoesNotExist
from tom_observations.models import DynamicCadence

from calibrations.models import Instrument, InstrumentFilter


register = template.Library()


@register.filter
def inst_in_filter_data(inst_filters, inst):  # TODO: rename this
    try:
        if inst.code == 'fa03':
            print(inst.code)
            last_calibration_age = inst_filters.get(instrument__code=inst.code).get_last_calibration_age()
            if last_calibration_age is not None:
                print(inst_filters.get(instrument__code=inst.code).instrument.site)
                print(last_calibration_age)
        else:
            print(inst.code)
            return None
        # if not last_calibration_age:
        #     return 'Never'
        # return last_calibration_age
    except ObjectDoesNotExist:
        return ''


@register.filter
def css_color(calibration_age):
    if not calibration_age:
        return ''
    elif calibration_age <= 6:
        return 'green'
    elif calibration_age > 6 and calibration_age < 13:
        return 'yellow'
    elif calibration_age >= 13:
        return 'red'


@register.filter
def submitted_filters(obsr):
    filters = []

    for key, value in obsr.parameters.items():
        if '_selected' in key and value is True:
            filters.append(key.strip('_selected'))

    return ', '.join(filters)


@register.inclusion_tag('imager_calibrations/partials/instrument_filter_site_table.html')
def instrument_filter_site_table(site):
    instruments_at_site = Instrument.objects.filter(site=site)
    filters_at_site = InstrumentFilter.objects.filter(instrument__site=site).distinct('filter__name').values_list('filter__name', flat=True)
    inst_filter_data = {}
    for f in filters_at_site:
        inst_filter_data[f] = []

        for inst in instruments_at_site:
            try:
                inst_filter_data[f].append(
                    InstrumentFilter.objects.get(instrument__code=inst.code, filter__name=f).get_last_calibration_age()
                )
            except ObjectDoesNotExist:
                inst_filter_data[f].append('')

    return {
        'site': site,
        'instruments_at_site': instruments_at_site,
        'inst_filter_data': inst_filter_data
    }


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
