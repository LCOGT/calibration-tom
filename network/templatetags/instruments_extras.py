from datetime import datetime, timedelta

from astroplan import moon_illumination
from astropy import units as u
from astropy.coordinates import Angle, get_moon, SkyCoord
from astropy.time import Time
from dateutil.parser import parse
from django import template
from django.conf import settings
from django.db.models import Q
from guardian.shortcuts import get_objects_for_user
import numpy as np
from plotly import offline
from plotly import graph_objs as go

from tom_observations.utils import get_sidereal_visibility
#from tom_targets.models import Target, TargetExtra, TargetList
#from tom_targets.forms import TargetVisibilityForm
from network.models import Instrument, InstrumentList

register = template.Library()


@register.inclusion_tag('network/partials/recent_instruments.html', takes_context=True)
def recent_instruments(context, limit=10):
    """
    Displays a list of the most recently created instruments in the Calibration-TOM up to the given limit, or 10 if not specified.
    """
    user = context['request'].user
    return {'instruments': get_objects_for_user(user, 'network.view_instrument').order_by('-created')[:limit]}


@register.inclusion_tag('network/partials/recently_updated_instruments.html', takes_context=True)
def recently_updated_instruments(context, limit=10):
    """
    Displays a list of the most recently updated instruments in the Calibration-TOM up to the given limit, or 10 if not specified.
    """
    user = context['request'].user
    return {'instruments': get_objects_for_user(user, 'network.view_instrument').order_by('-modified')[:limit]}


@register.inclusion_tag('network/partials/instrument_feature.html')
def instrument_feature(instrument):
    """
    Displays the featured image for an instrument.
    """
    return {'instrument': instrument}


@register.inclusion_tag('network/partials/instrument_buttons.html')
def instrument_buttons(instrument):
    """
    Displays the Update and Delete buttons for an instrument.
    """
    return {'instrument': instrument}


@register.inclusion_tag('network/partials/instrument_data.html')
def instrument_data(instrument):
    """
    Displays the data of an instrument.
    """
    extras = {k['name']: instrument.extra_fields.get(k['name'], '') for k in settings.EXTRA_FIELDS if not k.get('hidden')}
    return {
        'instrument': instrument,
        'extras': extras
    }


@register.inclusion_tag('network/partials/instrument_unknown_statuses.html')
def instrument_unknown_statuses(instrument):
    return {
        'num_unknown_statuses': len(instrument.observationrecord_set.filter(Q(status='') | Q(status=None)))
    }


@register.inclusion_tag('network/partials/instrument_groups.html')
def instrument_groups(instrument):
    """
    Widget displaying groups this instrument is in and controls for modifying group association for the given instrument.
    """
    groups = InstrumentList.objects.filter(instruments=instrument)
    return {'instrument': instrument,
            'groups': groups}


@register.inclusion_tag('network/partials/instrument_plan.html', takes_context=True)
def instrument_plan(context):
    """
    Displays form and renders plot for visibility calculation. Using this templatetag to render a plot requires that
    the context of the parent view have values for start_time, end_time, and airmass.
    """
    request = context['request']
    plan_form = InstrumentVisibilityForm()
    visibility_graph = ''
    if all(request.GET.get(x) for x in ['start_time', 'end_time']):
        plan_form = InstrumentVisibilityForm({
            'start_time': request.GET.get('start_time'),
            'end_time': request.GET.get('end_time'),
            'airmass': request.GET.get('airmass'),
            'target': context['object']
        })
        if plan_form.is_valid():
            start_time = parse(request.GET['start_time'])
            end_time = parse(request.GET['end_time'])
            if request.GET.get('airmass'):
                airmass_limit = float(request.GET.get('airmass'))
            else:
                airmass_limit = None
            visibility_data = get_sidereal_visibility(context['object'], start_time, end_time, 10, airmass_limit)
            plot_data = [
                go.Scatter(x=data[0], y=data[1], mode='lines', name=site) for site, data in visibility_data.items()
            ]
            layout = go.Layout(yaxis=dict(autorange='reversed'))
            visibility_graph = offline.plot(
                go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False
            )
    return {
        'form': plan_form,
        'instrument': context['object'],
        'visibility_graph': visibility_graph
    }


@register.inclusion_tag('network/partials/instrument_distribution.html')
def instrument_distribution(instruments):
    """
    Displays a plot showing on a map the locations of all instruments in the Calibration-TOM.
    """
    locations = instruments.filter(type=Instrument.SIDEREAL).values_list('ra', 'dec', 'name')
    data = [
        dict(
            lon=[location[0] for location in locations],
            lat=[location[1] for location in locations],
            text=[location[2] for location in locations],
            hoverinfo='lon+lat+text',
            mode='markers',
            type='scattergeo'
        ),
        dict(
            lon=list(range(0, 360, 60))+[180]*4,
            lat=[0]*6+[-60, -30, 30, 60],
            text=list(range(0, 360, 60))+[-60, -30, 30, 60],
            hoverinfo='none',
            mode='text',
            type='scattergeo'
        )
    ]
    layout = {
        'title': 'Instrument Distribution',
        'hovermode': 'closest',
        'showlegend': False,
        'geo': {
            'projection': {
                'type': 'mollweide',
            },
            'showcoastlines': False,
            'showland': False,
            'lonaxis': {
                'showgrid': True,
                'range': [0, 360],
            },
            'lataxis': {
                'showgrid': True,
                'range': [-90, 90],
            },
        }
    }
    figure = offline.plot(go.Figure(data=data, layout=layout), output_type='div', show_link=False)
    return {'figure': figure}


@register.filter
def deg_to_sexigesimal(value, fmt):
    """
    Displays a degree coordinate value in sexigesimal, given a format of hms or dms.
    """
    a = Angle(value, unit=u.degree)
    if fmt == 'hms':
        return '{0:02.0f}:{1:02.0f}:{2:05.3f}'.format(a.hms.h, a.hms.m, a.hms.s)
    elif fmt == 'dms':
        rep = a.signed_dms
        sign = '-' if rep.sign < 0 else '+'
        return '{0}{1:02.0f}:{2:02.0f}:{3:05.3f}'.format(sign, rep.d, rep.m, rep.s)
    else:
        return 'fmt must be "hms" or "dms"'


@register.filter
def instrument_extra_field(instrument, name):
    """
    Returns a ``InstrumentExtra`` value of the given name, if one exists.
    """
    try:
        return InstrumentExtra.objects.get(instrument=instrument, key=name).value
    except InstrumentExtra.DoesNotExist:
        return None


@register.inclusion_tag('network/partials/instrumentlist_select.html')
def select_instrument_js():
    """
    """
    return


#@register.inclusion_tag('network/partials/aladin.html')
#def aladin(instrument):
#    """
#    Displays Aladin skyview of the given target along with basic finder chart annotations including a compass
#    and a scale bar. The resulting image is downloadable. This templatetag only works for sidereal targets.
#    """
#    return {'instrument': instrument}


@register.inclusion_tag('network/partials/instrument_table.html')
def instrument_table(instruments):
    """
    Returns a partial for a table of instruments, used in the instrument_list.html template
    by default
    """
    return {'instruments': instruments}
