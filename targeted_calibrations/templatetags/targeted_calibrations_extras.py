import json
import statistics

from django import template
from django.conf import settings
from django.db import models
from django.db.models.fields.json import KeyTextTransform
from django.db.models.functions import Cast
from guardian.shortcuts import get_objects_for_user
from plotly import offline
import plotly.graph_objs as go

from targeted_calibrations.forms import NRESCalibrationSubmissionForm
from tom_common.templatetags.tom_common_extras import truncate_number
from tom_dataproducts.models import ReducedDatum
from tom_observations.models import DynamicCadence, ObservationRecord
from tom_targets.models import Target


register = template.Library()


@register.filter
def prev_observation(observations):
    """
    :param observations: an Observation QuerySet
    """
    # TODO: remove COMPLETED which is a magic number
    return observations.filter(status='COMPLETED').order_by('-scheduled_end').first()


# TODO: generalize this method in tom_base
# TODO: nres_cadence_list table should be managed by a templatetag
@register.filter
def prop_from_model(model, prop):
    if model is not None:
        model_prop = model.__getattribute__(prop)
        if model_prop is not None:
            return model_prop


@register.filter
def prev_observation_id(observations):
    """
    :param observations: an Observation QuerySet
    """
    # TODO: remove COMPLETED which is a magic number
    return observations.filter(status='COMPLETED').order_by('-scheduled_end').first().id


@register.filter
def next_observation(observations):
    """
    :param observations: an Observation QuerySet
    """
    # TODO: remove PENDING which is a magic number
    return observations.filter(status='PENDING').order_by('scheduled_start').first()


@register.filter
def next_observation_id(observations):
    """
    :param observations: an Observation QuerySet
    """
    # TODO: remove PENDING which is a magic number
    # TODO: this is unsafe if the filter result is NoneType
    return observations.filter(status='PENDING').order_by('scheduled_start').first().id


@register.inclusion_tag('targeted_calibrations/partials/nres_targets_list.html')
def nres_targets_list():
    nres_targets = Target.objects.all()
    # determine "last" observation
    # determine "next" observation
    # annotate target with the observation
    # then, in the template extract these annotation for display in list
    context = {'nres_targets_data': [{
        'target': nres_target,
        'prev_obs': nres_target.observationrecord_set.filter(status='COMPLETED').order_by('-scheduled_end').first(),
        'next_obs': nres_target.observationrecord_set.filter(status='PENDING').order_by('-scheduled_end').first()
    } for nres_target in nres_targets]}
    return context


@register.inclusion_tag('targeted_calibrations/partials/nres_cadence_list.html')
def nres_cadence_list():
    # Annotate Dynamic Cadences with site and calibration type in order to sort by JSONField values
    nres_cadences = (DynamicCadence.objects.filter(cadence_strategy='NRESCadenceStrategy')
                     .annotate(site=Cast(KeyTextTransform('site', 'cadence_parameters'), models.TextField()))
                     .annotate(standard_type=Cast(KeyTextTransform('standard_type', 'cadence_parameters'),
                                                  models.TextField()))  # TODO: This should be the standard type
                     .order_by('-created')
                     .order_by('site'))
    return {'nres_cadences': nres_cadences}


@register.inclusion_tag('targeted_calibrations/partials/nres_submission_form.html')
def nres_submission_form():
    nres_cadence_form = NRESCalibrationSubmissionForm()
    return {'nres_cadence_form': nres_cadence_form}


@register.inclusion_tag('targeted_calibrations/partials/target_observation_list.html')
def target_observation_list(target):
    observation_records = ObservationRecord.objects.filter(target=target, status='COMPLETED')
    observations = []
    for obsr in observation_records:
        # TODO: how to handle multiple data products/datums?
        dp = obsr.dataproduct_set.first()
        if dp:
            rd = dp.reduceddatum_set.first()
            if rd:
                rd_value = json.loads(rd.value)
                observations.append({
                    'date': obsr.scheduled_start,
                    'rv': rd_value.get('radial_velocity'),
                    'rv_error': rd_value.get('rv_error')
                })

    return {'observations': observations}


@register.inclusion_tag('targeted_calibrations/partials/rv_plot.html')
def rv_plot(target):
    # TODO: Ensure that this works when there isn't data
    rv_data = [[], []]

    datums = ReducedDatum.objects.filter(target=target, data_type=settings.DATA_PRODUCT_TYPES['nres_rv'][0])

    for datum in datums:
        rv = json.loads(datum.value)
        rv_data[0].append(datum.timestamp)
        rv_data[1].append(rv['radial_velocity'])

    plot_data = go.Scatter(x=rv_data[0], y=rv_data[1], mode='markers')
    layout = go.Layout(xaxis={'title': 'Date'}, yaxis={'title': 'RV (m/s)'})
    return {'rv_plot': offline.plot(go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False)}


@register.simple_tag
def rv_average(target):
    rd_values = [json.loads(rd.value)['radial_velocity'] for rd in ReducedDatum.objects.filter(target=target)]
    if len(rd_values) > 0:
        return f'{truncate_number(statistics.mean(rd_values))} m/s'
    else:
        return 'No data yet'


@register.inclusion_tag('targeted_calibrations/partials/scalar_timeseries_for_target.html', takes_context=True)
def scalar_timeseries_for_target(context, target):
    """
    TODO: re-write documentation from copy-paste
    Renders a photometric plot for a target.

    This templatetag requires all ``ReducedDatum`` objects with a data_type of ``photometry`` to be structured with the
    following keys in the JSON representation: magnitude, error, filter
    """
    # TODO: re-write implementation from copy-paste
    # extract the data for each datum from ReducedDatum table
    if settings.TARGET_PERMISSIONS_ONLY:
        datums = ReducedDatum.objects.filter(target=target, data_type=settings.DATA_PRODUCT_TYPES['photometry'][0])
    else:
        datums = get_objects_for_user(context['request'].user, 'tom_dataproducts.view_reduceddatum',
                                      klass=ReducedDatum.objects.filter(
                                          target=target,
                                          data_type=settings.DATA_PRODUCT_TYPES['photometry'][0]))

    # construct photometry_data ot feed go.Scatter plot
    photometry_data = {}
    for datum in datums:
        values = json.loads(datum.value)
        photometry_data.setdefault(values['filter'], {})
        photometry_data[values['filter']].setdefault('time', []).append(datum.timestamp)
        photometry_data[values['filter']].setdefault('magnitude', []).append(values.get('magnitude'))
        photometry_data[values['filter']].setdefault('error', []).append(values.get('error'))

    plot_data = [
        go.Scatter(
            x=filter_values['time'],
            y=filter_values['magnitude'], mode='markers',
            name=filter_name,
            error_y=dict(
                type='data',
                array=filter_values['error'],
                visible=True
            )
        ) for filter_name, filter_values in photometry_data.items()]
    layout = go.Layout(
        yaxis=dict(autorange='reversed'),
        height=600,
        width=700
    )
    return {
        'target': target,
        'plot': offline.plot(go.Figure(data=plot_data, layout=layout), output_type='div', show_link=False)
    }
