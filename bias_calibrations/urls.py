from django.urls import path

from bias_calibrations.views import BiasCalibrationsView, BiasCalibrationsForm, BiasCalibrationsTargets
from bias_calibrations.views import BiasCalibrationsCadencesView, BiasCalibrationsCadencesSiteView, BiasCalibrationsCadencesList, BiasCalibrationsCadenceToggleView, BiasCalibrationsCadenceDeleteView

app_name = 'bias_calibrations'

urlpatterns = [
    path('cadences/', BiasCalibrationsCadencesView.as_view(), name='bias_calibrations_cadences'),
    path('cadence-toggle/<int:pk>/', BiasCalibrationsCadenceToggleView.as_view(), name='cadence_toggle'),
    path('cadence-delete/<int:pk>/', BiasCalibrationsCadenceDeleteView.as_view(), name='cadence_delete'),
    path('form/', BiasCalibrationsForm.as_view(), name='bias_calibrations_form'),
    path('targets/', BiasCalibrationsTargets.as_view(), name='bias_calibrations_targets'),
    path('site/<str:site>/', BiasCalibrationsCadencesSiteView.as_view(), name='site_detail')
]
