from django.contrib import admin
from .models import Filter, Instrument, InstrumentFilter

# Register your models here
admin.site.register(Filter)
admin.site.register(Instrument)
admin.site.register(InstrumentFilter)