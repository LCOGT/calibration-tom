from datetime import datetime

from django import template
from django.conf import settings

from configdb.configdb_connections import ConfigDBInterface

register = template.Library()


def rv_plot(target):
    pass