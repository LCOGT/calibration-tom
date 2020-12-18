from datetime import datetime

from django import template
from django.db.models import F
from django.conf import settings
from guardian.shortcuts import get_objects_for_user

from configdb.configdb_connections import ConfigDBInterface

register = template.Library()


@register.inclusion_tag('calibrations/partials/site_calibration_button.html')
def site_calibration_button(site, instrument):
    """
    Renders a button for creating a new series of calibrations for a given instrument/site.
    """
    return {'site': site, 'instrument': instrument}


@register.simple_tag
def display_seasonal_start_or_end(month):
    return datetime(year=datetime.now().year, month=int(month), day=1).strftime('%B')


@register.inclusion_tag('calibrations/partials/sitecode_tag.html')
def sitecode_tag(instrument_code):
    configdb = ConfigDBInterface(settings.CONFIGDB_URL)
    instrument_data = configdb.get_matching_instrument(instrument_name=instrument_code)
    return {
        'instrument_code': instrument_code,
        'site': instrument_data["site"]
    }


@register.inclusion_tag('calibrations/partials/standard_type_tag.html')
def standard_type(target):
    return {'standard_type': target.extra_fields.get('standard_type', '')}


@register.inclusion_tag('calibrations/partials/last_obs.html', takes_context=True)
def last_observation_date(context, target):
    observation = (get_objects_for_user(context['request'].user, 'tom_observations.view_observationrecord')
                   .filter(target=target, status='COMPLETED')
                   .order_by(F('scheduled_start').desc(nulls_last=True))
                   .first())
    last_obs_date = observation.scheduled_start if observation else 'None'
    return {'last_obs_date': last_obs_date}


@register.inclusion_tag('calibrations/partials/next_obs.html', takes_context=True)
def next_observation_date(context, target):
    observation = (get_objects_for_user(context['request'].user, 'tom_observations.view_observationrecord')
                   .filter(target=target, status='PENDING')
                   .order_by(F('scheduled_start').asc(nulls_last=True))
                   .first())
    next_obs_date = observation.scheduled_start if observation else None
    if not next_obs_date:
        next_obs_date = 'Pending but unscheduled'
    return {'next_obs_date': next_obs_date}
