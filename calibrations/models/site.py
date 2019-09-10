import datetime
from django.db import models
from .base import BaseModel


class Site(BaseModel):
    code = models.CharField(max_length=3)
    name = models.CharField(default='', blank=True, max_length=200)

    lat = models.FloatField(default=0.0)
    long = models.FloatField(default=0.0)
    elevation = models.IntegerField(help_text='meters')

    restart_time = models.TimeField(default=datetime.time(hour=0, minute=0, second=0))

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.code
