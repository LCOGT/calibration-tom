from django.db import models
from .base import BaseModel
from .camera import Camera
from .telescope import Telescope


class Instrument(BaseModel):
    DISABLED = 0
    MANUAL = 10
    COMMISSIONING = 20
    STANDBY = 25
    SCHEDULABLE = 30
    STATE_CHOICES = (
        (DISABLED, 'DISABLED'),
        (MANUAL, 'MANUAL'),
        (COMMISSIONING, 'COMMISSIONING'),
        (STANDBY, 'STANDBY'),
        (SCHEDULABLE, 'SCHEDULABLE'),
    )
    AUTOGUIDER_TYPES = (
        ("InCamera", "InCamera"),
        ("OffAxis", "OffAxis"),
        ("SelfGuide", "SelfGuide")
    )

    code = models.CharField(max_length=200, default='', blank=True, help_text='Name of the instrument')
    state = models.IntegerField(choices=STATE_CHOICES, default=DISABLED)
    telescope = models.ForeignKey(Telescope, on_delete=models.PROTECT)
    science_camera = models.ForeignKey(Camera, on_delete=models.PROTECT)
    autoguider_camera = models.ForeignKey(Camera, related_name='autoguides_for', on_delete=models.PROTECT)
    autoguider_type = models.CharField(max_length=200, choices=AUTOGUIDER_TYPES, default="OffAxis")

    def __str__(self):
        return '{0}.{1}-{2}'.format(self.telescope, self.science_camera, self.autoguider_camera)
