from datetime import datetime
from dateutil.parser import parse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.forms.models import model_to_dict
from django.urls import reverse

from tom_common.hooks import run_hook

INSTRUMENT_FIELDS = ['code', 'instrument', 'instrument_type', 'state']

INSTRUMENT_TYPES = (
    ('2M0-SCICAM-SPECTRAL', '2m0-SciCam-Spectral'),
    ('2M0-SCICAM-MUSCAT', '2m0-SciCam-MuSCAT'),
    ('2M0-FLOYDS-SCICAM', '2m0-FLOYDS-SciCam'),
    ('1M0-SCICAM-SINISTRO', '1m0-SciCam-Sinistro'),
    ('1M0-NRES-SCICAM', '1m0-NRES-SciCam'),
    ('0M4-SCICAM-SBIG', '0m4-SciCam-SBIG')
)

INSTRUMENT_STATES = (
    ('DISABLED', 'Disabled'),
    ('MANUAL', 'Manual'),
    ('COMMISSIONING', 'Commissioning'),
    ('STANDBY', 'Standby'),
    ('SCHEDULABLE', 'Schedulable')
)

class Instrument(models.Model):
    """
    Class representing an instrument in the Calibration-TOM

    :param code: The code identifying the instrument, e.g. kb95
    :type code: str

    :param instrument: The full site.enc.tel.inst designation of the instrument, e.g. coj.clma.0m4a.kb24
    :type code: str

    :param instrument_type: The type of instrument, e.g. 0m4-SciCam-SBIG.
    :type instrument_type: str

    :param state: The instrument state, e.g. SCHEDULABLE.
    :type state: str

    :param created: The time at which the instrument was created in the Calibration-TOM.
    :type created: datetime

    :param modified: The time at which the instrument was changed in the Calibration-TOM.
    :type modified: datetime

    :param lat: The latitude of the telescope that has the instrument installed, in degrees.
    :type lat: float

    :param lon: The longitude of the telescope that has the instrument installed, in degrees.
    :type lon: float

    """


    code = models.CharField(
        max_length=10, default='', verbose_name='Code', help_text='The code identifying the instrument e.g. kb95',
        unique=True
    )
    instrument = models.CharField(
        max_length=100, default='', verbose_name='Instrument', help_text='The full site.enclosure.telescope.code designation of the instrument e.g. coj.clma.0m4a.kb24',
        unique=True
    )
    instrument_type = models.CharField(
        max_length=100, choices=INSTRUMENT_TYPES, verbose_name='Instrument Type', help_text='The type of instrument, e.g. 1m0-SciCam-Sinistro.'
    )
    state = models.CharField(
        max_length=100, choices=INSTRUMENT_STATES, verbose_name='Instrument State', help_text='The instrument state, e.g. SCHEDULABLE.'
    )
    created = models.DateTimeField(
        auto_now_add=True, verbose_name='Time Created', help_text='The time at which the instrument was created in the Calibration-TOM.'
    )
    modified = models.DateTimeField(
        auto_now=True, verbose_name='Last Modified', help_text='The time at which the instrument was last updated in the Calibration-TOM.'
    )
    #telescope = models.CharField(
    #    max_length=100, default='', verbose_name='Telescope', help_text='The telescope on which the instrument is installed, e.g. coj.doma.1m0a.'
    #)
    #lat = models.FloatField(
    #    null=True, blank=True, verbose_name='Latitude', help_text='Latitude, in degrees.'
    #)
    #lon = models.FloatField(
    #    null=True, blank=True, verbose_name='Longitude', help_text='Longitude, in degrees.'
    #)

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Saves Instrument model data to the database. After saving to the database, also runs the
        hook ``instrument_post_save``. The hook run is the one specified in ``settings.py``.

        """

        created = False if self.id else True
        super().save(*args, **kwargs)

        if not created:
            run_hook('instrument_post_save', instrument=self, created=created)

    def __str__(self):
        return str(self.code)

    def get_absolute_url(self):
        return reverse('instruments:detail', kwargs={'pk': self.id})

    @property
    def future_observations(self):
        """
        Gets all observations scheduled for this ``Instrument``

        :returns: List of ``ObservationRecord`` objects without a terminal status
        :rtype: list
        """
        return [
            obs for obs in self.observationrecord_set.exclude(status='').order_by('scheduled_start') if not obs.terminal
        ]

    def as_dict(self):
        """
        Returns dictionary representation of attributes, excluding all attributes not associated with the ``type`` of
        this ``Instrument``.

        :returns: Dictionary of key/value pairs representing instrument attributes
        :rtype: dict
        """
        fields_for_type = INSTRUMENT_FIELDS

        return model_to_dict(self, fields=fields_for_type)


class InstrumentList(models.Model):
    """
    Class representing a list of instruments in the Calibration-TOM.

    :param name: The name of the instrument list
    :type name: str

    :param instruments: Set of ``Instrument`` objects associated with this ``InstrumentList``

    :param created: The time at which this instrument list was created.
    :type created: datetime

    :param modified: The time at which this instrument list was modified in the Calibration-TOM.
    :type modified: datetime
    """
    name = models.CharField(max_length=200, help_text='The name of the instrument list.')
    instruments = models.ManyToManyField(Instrument)
    created = models.DateTimeField(
        auto_now_add=True, help_text='The time which this instrument list was created in the Calibration-TOM.'
    )
    modified = models.DateTimeField(
        auto_now=True, verbose_name='Last Modified',
        help_text='The time which this instrument list was changed in the Calibration-TOM.'
    )

    class Meta:
        ordering = ('-created', 'name',)

    def __str__(self):
        return self.name
