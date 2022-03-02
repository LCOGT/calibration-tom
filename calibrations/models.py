from datetime import datetime, timezone

from django.db import models
from tom_observations.models import ObservationRecord
from tom_targets.models import Target


# this is an extension to tom_targets.models.Target class
#
def target_is_in_season(self, query_date: datetime = datetime.utcnow()):
    """"Returns True if query_date is between target's seasonal_start and seasonal_end
    Note: seasonal_start and seasonal_end are month numbers (1=January, etc).

    This method will be added to the Target class with setattr (that's why it has a self argument).
    """
    seasonal_start = int(self.targetextra_set.filter(key='seasonal_start').first().float_value)
    seasonal_end = int(self.targetextra_set.filter(key='seasonal_end').first().float_value)
    current_month = query_date.month

    # Adjust months in case of end of year roll-over
    if seasonal_start > seasonal_end:
        seasonal_end += 12
        if current_month < seasonal_start:
            current_month += 12

    return seasonal_start <= current_month <= seasonal_end
setattr(Target, 'target_is_in_season', target_is_in_season)  # noqa - add method to Target class


class Filter(models.Model):
    name = models.CharField(
        max_length=100, default='', verbose_name='Name', help_text='Name of the filter',
        unique=True
    )

    exposure_time = models.FloatField(
        verbose_name='Exposure Time', help_text='Exposure time, in seconds.'
    )

    exposure_count = models.IntegerField(
        verbose_name='Exposure Count', help_text='Number of exposures.'
    )

    def __str__(self):
        return f'{self.name} filter (default: {self.exposure_count} x {self.exposure_time} second exposures)'

    # Boilerplate fields
    created = models.DateTimeField(
        auto_now_add=True, verbose_name='Time Created',
        help_text='The time which this target was created in the TOM database.'
    )
    modified = models.DateTimeField(
        auto_now=True, verbose_name='Last Modified',
        help_text='The time which this target was changed in the TOM database.'
    )


class Instrument(models.Model):
    site = models.CharField(max_length=3)
    enclosure = models.CharField(max_length=20)
    telescope = models.CharField(max_length=20)
    code = models.CharField(max_length=20, unique=True)
    type = models.CharField(max_length=50, null=True, blank=True)

    def update_from_configdb(self):
        raise NotImplementedError  # TODO

    def __str__(self):
        return f'{self.site}.{self.enclosure}.{self.telescope}.{self.code}'


class InstrumentFilter(models.Model):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE)
    max_age = models.IntegerField(default=5)

    def get_last_calibration_age(self, observation_group=None):
        if not observation_group:
            records = ObservationRecord.objects.all()
        else:
            records = observation_group.observation_records.all()
        kwargs = {f'parameters__{self.filter.name}_selected': True,
                  'parameters__instrument': self.instrument.code,
                  'status': 'COMPLETED'}
        last_calibration = records.order_by('-created').filter(**kwargs).first()
        if last_calibration and last_calibration.scheduled_end:
            return (datetime.now(timezone.utc) - last_calibration.scheduled_end).days

    def __str__(self):
        return f'{self.instrument.code} - {self.filter.name}'
