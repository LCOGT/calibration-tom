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

class BiasTargetExtra(models.Model):
    """
    Class representing extra fields for bias target in a TOM.

    :param target: The ``Target`` object this ``TargetExtra`` is associated with.

    :param key: Denotation of the value represented by this ``TargetExtra`` object.
    :type key: str

    :param value: Value of the field stored in this object.
    :type value: str

    :param float_value: Float representation of the ``value`` field for this object, if applicable.
    :type float_value: float

    :param bool_value: Boolean representation of the ``value`` field for this object, if applicable.
    :type bool_value: bool

    :param time_value: Datetime representation of the ``value`` field for this object, if applicable.
    :type time_value: datetime
    """
    target = models.ForeignKey(BiasTarget, on_delete=models.CASCADE)
    key = models.CharField(max_length=200)
    value = models.TextField(blank=True, default='')
    float_value = models.FloatField(null=True, blank=True)
    bool_value = models.BooleanField(null=True, blank=True)
    time_value = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['target', 'key']

    def __str__(self):
        return f'{self.key}: {self.value}'

    def save(self, *args, **kwargs):
        """
        Saves BiasTargetExtra model data to the database. In the process, converts the string value of the ``BiasTargetExtra``
        to the appropriate type, and stores it in the corresponding field as well.
        """
        try:
            self.float_value = float(self.value)
        except (TypeError, ValueError, OverflowError):
            self.float_value = None
        try:
            self.bool_value = bool(self.value)
        except (TypeError, ValueError, OverflowError):
            self.bool_value = None
        try:
            if isinstance(self.value, datetime):
                self.time_value = self.value
            else:
                self.time_value = parse(self.value)
        except (TypeError, ValueError, OverflowError):
            self.time_value = None

        super().save(*args, **kwargs)

    def typed_value(self, type_val):
        """
        Returns the value of this ``BiasTargetExtra`` in the corresponding type provided by the caller. If the type is
        invalid, returns the string representation.

        :param type_val: Requested type of the ``BiasTargetExtra`` ``value`` field
        :type type_val: str

        :returns: Requested typed value field of this object
        :rtype: float, boolean, datetime, or str
        """
        if type_val == 'number':
            return self.float_value
        if type_val == 'boolean':
            return self.bool_value
        if type_val == 'datetime':
            return self.time_value

        return self.value


