from django.db import models

from tom_common.hooks import run_hook

# Create your models here.

GLOBAL_TARGET_FIELDS = ['name', 'type']

HOUR_ANGLE_FIELDS = GLOBAL_TARGET_FIELDS + ['hour_angle', 'dec']

REQUIRED_HOUR_ANGLE_FIELDS = ['hour_angle', 'dec']

class BiasTarget(models.Model):
    """
    Class representing a fake target for a bias calibration.

    :param name: Historically, "No target". For Calibration-TOM, use "Bias target"
    :type name: str

    :param type: Historically, "HOUR_ANGLE"
    :type type: str

    :param hour_angle: Historically, 1
    :type hour_angle: float

    :param dec: Historically, 0
    :type dec: float
    """

    name = models.CharField(
        max_length=100, default='Bias target', verbose_name='Target Name', help_text='Even a bias observation needs a target, even if it is no target'
    )

    type = models.CharField(
        max_length=100, default='HOUR_ANGLE', verbose_name='Target Type', help_text='The No target has type HOUR_ANGLE'
    )
    hour_angle = models.FloatField(
        null=True, blank=True, default=1, verbose_name='Hour Angle', help_text='Hour Angle, in hours'
    )
    dec = models.FloatField(
        null=True, blank=True, default=0, verbose_name='Declination', help_text='Declination, in degrees'
    )

    def save(self, *args, **kwargs):
        """
        Saves BiasTarget model data to the database. After saving to the database, also runs the
        hook ``target_post_save``. The hook run is the one specified in ``settings.py``.

        """

        super().save(*args, **kwargs)

        run_hook('target_post_save', target=self, created=created)

    def __str__(self):
        return str(self.name)

