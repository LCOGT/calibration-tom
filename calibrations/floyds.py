from django import forms
from django.db.models.query import QuerySet
from tom_observations.facilities.lco import LCOFacility, LCOBaseObservationForm, LCOSpectroscopyObservationForm
from tom_targets.models import Target
from datetime import datetime, timedelta
import ephem
import numpy as np
import copy
from typing import Dict, Tuple, List

FLOYDS_SITES = {'ogg': {'latitude': 20.706,
                        'longitude': -156.258,
                        'elevation': 3065},
                'coj': {'latitude': -31.272,
                        'longitude': 149.07,
                        'elevation': 1116}}


class FloydsStandardObservationForm(LCOSpectroscopyObservationForm):
    acquire_radius = forms.FloatField()

    def _build_configuration(self):
        return {
            'type': self.instrument_to_type(self.cleaned_data['instrument_type']),
            'instrument_type': self.cleaned_data['instrument_type'],
            'target': self._build_target_fields(),
            'instrument_configs': [self._build_instrument_config()],
            'acquisition_config': {
                'mode': 'BRIGHTEST', #TODO: de-hardcode this
                'extra_params': {
                    'acquire_radius': self.cleaned_data['acquire_radius']
                }
            },
            'guiding_config': {},
            'constraints': {
                'max_airmass': self.cleaned_data['max_airmass']
            }
        }
    #TODO: Clean this up to look more like the LCOBaseObservationForm's observation_payload() method
    def observation_payload(self) -> Dict:
        payload = super().observation_payload()
        base_configuration = self._build_configuration()
        payload['requests'][0]['configurations'] = [base_configuration]

        spectrum_configuration = copy.deepcopy(base_configuration)
        lamp_flat_configuration = copy.deepcopy(base_configuration)
        arc_configuration = copy.deepcopy(base_configuration)

        spectrum_configuration['type'] = 'SPECTRUM'
        spectrum_configuration['instrument_configs'][0]['exposure_time'] = 300
        lamp_flat_configuration['type'] = 'LAMP_FLAT'
        lamp_flat_configuration['instrument_configs'][0]['exposure_time'] = 80
        arc_configuration['type'] = 'ARC'
        arc_configuration['instrument_configs'][0]['exposure_time'] = 40

        payload['requests'][0]['configurations'].append(spectrum_configuration)
        payload['requests'][0]['configurations'].append(lamp_flat_configuration)
        payload['requests'][0]['configurations'].append(arc_configuration)

        return payload



def get_floyds_targets(site, date) -> QuerySet:
    floyds_targets = Target.objects.filter(targetextra__key__exact='site', targetextra__value__exact=site) \
                                   .filter(targetextra__key__exact='seasonal_start', targetextra__value__lte=date) \
                                   .filter(targetextra__key__exact='seasonal_end', targetextra__value__gte=date)

    return floyds_targets


def submit_calibrations(site, date=datetime.utcnow()) -> List[str]:
    for target in get_floyds_targets(site, date):
        form = get_form_for_target(target)
        if form.is_valid():
            return LCOFacility().submit_observation(form.observation_payload())
        else:
            print("Invalid observation form!")
            return []


def get_form_for_target(target) -> FloydsStandardObservationForm:
    site_code = target.extra_fields['site']
    #TODO: Do this better!
    site_latitude = FLOYDS_SITES[site_code]['latitude']
    site_longitude = FLOYDS_SITES[site_code]['longitude']
    window_start, midnight, window_end = get_next_sunset_midnight_sunrise(site_latitude, site_longitude)
    if window_start > window_end:
        today = datetime.utcnow() - timedelta(hours=12)
        window_start, midnight, window_end = get_next_sunset_midnight_sunrise(site_latitude, site_longitude, today=today)

    observation_form = FloydsStandardObservationForm({
        'name': 'FLOYDS Spectral Calibration',
        'proposal': f'{site_code.upper()}_calib',
        'ipp_value': 1,
        'acquire_radius': 5.0,
        'start': window_start,
        'end': window_end,
        'filter': 'slit_2.0as', #this is a smell
        'instrument_type': '2M0-FLOYDS-SCICAM',
        'exposure_count': 1,
        'exposure_time': 300,
        'max_airmass': 1.6,
        'target_id': target.id,
        'observation_mode': 'NORMAL',
        'rotator_angle': '0', #TODO: Figure out a reasonable default for this!
        'facility': 'LCO'
    })

    return observation_form


def get_next_sunset_midnight_sunrise(latitude, longitude, horizon=-12, today=None, hoursbefore = 0) -> Tuple[datetime, datetime, datetime]:
    """Return the start of dark time, midnight, end of dark time in UTC for a given site, from now.
        TODO: Sanity checks.
        TODO: Allow for user-defined day instead of relying only on  datetime.now() .
    """
    site = ephem.Observer()
    site.lat = np.radians(latitude)
    site.lon = np.radians(longitude)

    if today is not None:
        site.date = today
    #
    site.date = site.date - hoursbefore * ephem.hour

    sun = ephem.Sun()
    next_midnight = strip_msec(site.next_antitransit(sun).datetime())

    # fake the horizon to get true dark time
    sun_alt_at_twilight_start_degrees = str(horizon)
    site.horizon = sun_alt_at_twilight_start_degrees

    next_sunset = strip_msec(site.next_setting(sun, use_center=True).datetime())
    next_sunrise = strip_msec(site.next_rising(sun, use_center=True).datetime())

    print(
        "\n\tNight info for site %s\n\tNext End of twilight:\t %s \n\tNext Midnight:\t\t\t %s\n\tNext start of twilight:\t %s" % (
            site, next_sunset, next_midnight, next_sunrise))

    return next_sunset, next_midnight, next_sunrise


#TODO: junk this
def strip_msec(when):
    return when - timedelta(microseconds=when.microsecond)
