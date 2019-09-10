from django.db import models
from .base import BaseModel
from .enclosure import Enclosure


class Telescope(BaseModel):
    code = models.CharField(max_length=200)
    name = models.CharField(default='', blank=True, max_length=200)

    lat = models.FloatField()
    long = models.FloatField()
    horizon = models.FloatField()
    ha_limit_neg = models.FloatField()
    ha_limit_pos = models.FloatField()

    zenith_blind_spot = models.FloatField(
        default=0.0, help_text='For AltAz telescopes, radius of zenith blind spot in degrees')
    enclosure = models.ForeignKey(Enclosure, models.PROTECT)

    def __str__(self) -> str:
        return '{0}.{1}'.format(self.enclosure, self.code)
