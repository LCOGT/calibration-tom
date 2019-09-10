from django.db import models
from .base import BaseModel
from .site import Site


class Enclosure(BaseModel):
    code = models.CharField(max_length=200)
    name = models.CharField(default='', blank=True, max_length=200)
    site = models.ForeignKey(Site, on_delete=models.PROTECT)

    def __str__(self) -> str:
        return '{0}.{1}'.format(self.site, self.code)
