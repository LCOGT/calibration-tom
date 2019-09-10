from django.db import models
from .base import BaseModel


class CameraType(BaseModel):
    pass


class OpticalElementGroup(BaseModel):
    pass


class FilterWheel(BaseModel):
    pass


class Camera(BaseModel):
    camera_type = models.ForeignKey(CameraType, models.PROTECT)
    code = models.CharField(max_length=200)
    filter_wheel = models.ForeignKey(FilterWheel, models.PROTECT)
    optical_element_groups = models.ManyToManyField(OpticalElementGroup, blank=True)
    host = models.CharField(max_length=200, default='', blank=True,
                            help_text='The physical machine hostname that this camera is connected to')

    class Meta:
        ordering = ['code']

    @property
    def filters(self):
        return str(self.filter_wheel)

    @property
    def optical_elements(self):
        return {oeg.type: oeg.optical_element_codes() for oeg in self.optical_element_groups.all()}

    def __str__(self):
        return '{0}'.format(self.code)
