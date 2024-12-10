from django.contrib import admin
from .models import Filter, FilterSet, Instrument, InstrumentFilterSet

# Register your models here
admin.site.register(Filter)
admin.site.register(FilterSet)
admin.site.register(Instrument)
#admin.site.register(InstrumentFilter)
admin.site.register(InstrumentFilterSet)