from django.contrib import admin
from .models import Instrument, InstrumentList

# Register your models here.
admin.site.register(Instrument)
admin.site.register(InstrumentList)
