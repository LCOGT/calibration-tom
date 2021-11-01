from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models.functions import Cast
from django.db.models.fields.json import KeyTextTransform
from tom_observations.models import DynamicCadence

from calibrations.models import Instrument, InstrumentFilter

from tom_targets.models import Target

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


@register.inclusion_tag('photometric_standards/partials/instrument_filter_site_table.html')
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


@register.inclusion_tag('photometric_standards/partials/instrument_filters_at_site.html')
def instrument_filter_at_site(instrument):  # TODO: make this take context
    instrument_data = {'instrument': instrument, 'filter_data': {}}
    inst_filters = InstrumentFilter.objects.filter(instrument=instrument)
    instrument_data['filter_data'] = inst_filters
    return instrument_data


@register.inclusion_tag('photometric_standards/partials/photometric_standards_cadences_list.html')
def photometric_standards_cadences_list() -> dict:
    photometric_standards_cadences = (DynamicCadence.objects.filter(cadence_strategy='PhotometricStandardsCadenceStrategy')
                                      # Extract values from  the cadence_parameters JSONField and annotate (add as columns to) the QuerySet
                                      .annotate(site=Cast(KeyTextTransform('instrument_code','cadence_parameters'),models.TextField()))
                                      .annotate(target_id=Cast(KeyTextTransform('target_id', 'cadence_parameters'),models.TextField()))
                                      .order_by('site', '-target_id'))
    
    print(f"photometric_standards_cadences : {photometric_standards_cadences}")

    cadences_data = []
    for cadence in photometric_standards_cadences:
        target = Target.objects.filter(pk=cadence.target_id).first()
        #cadence["cadence_parameters"]["site"] = "XYZ"
        cadences_data.append({
            'cadence': cadence,
            'target': target,
            'prev_obs': cadence.observation_group.observation_records.filter(status='COMPLETED').order_by('-scheduled_end').first(),
            'next_obs': cadence.observation_group.observation_records.filter(status='PENDING').order_by('scheduled_start').first()
            })

    context = {'cadences_data': cadences_data}
    return context


@register.inclusion_tag('photometric_standards/partials/instrument_observations_at_site.html')
def instrument_observations_at_site(instrument):  # TODO: make this take context
    try:
        cadence = DynamicCadence.objects.get(active=True, cadence_parameters__instrument_code=instrument.code)
    except ObjectDoesNotExist:
        return {}  # TODO: make this more robust
    records = cadence.observation_group.observation_records.order_by('-created')[:10]
    return {'observation_records': records}

@register.inclusion_tag('photometric_standards/partials/photometric_standards_targets_list.html')
def photometric_standards_targets_list() -> dict:
    photometric_standards_targets = Target.objects.filter(targetextra__key='standard_type', targetextra__value__in=['photometric'])
    # determine "last" observation
    # determine "next" observation
    # annotate target with the observation
    # then, in the template extract these annotation for display in list

    context = {'targets_data': [{
        'target': photometric_standards_target,
        'prev_obs': photometric_standards_target.observationrecord_set.filter(status='COMPLETED').order_by('-scheduled_end').first(),
        'next_obs': photometric_standards_target.observationrecord_set.filter(status='PENDING').order_by('scheduled_start').first()
    } for photometric_standards_target in photometric_standards_targets]}
    return context


