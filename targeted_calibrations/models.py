from datetime import datetime

from django.db import models

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

    return seasonal_start <= query_date.month <= seasonal_end
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
