from django.urls import path

from nres_calibrations.views import NRESCalibrationsIndex

urlpatterns = [
    path('', NRESCalibrationsIndex.as_view(), name='nres_calibrations_index'),
]
