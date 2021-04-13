from django.urls import path

from targeted_calibrations.views import ImagerCalibrationsView, ImagerCalibrationSubmissionView
from targeted_calibrations.views import NRESCalibrationsView, NRESCalibrationSubmissionView
from targeted_calibrations.views import InstrumentListView
from targeted_calibrations.views import InstrumentTargetDetailView
from targeted_calibrations.views import InstrumentTargetListView
from targeted_calibrations.views import InstrumentTypeListView
from targeted_calibrations.views import NRESCadenceToggleView, NRESCadenceDeleteView

# app_name is required in order to specify a namespace in include()
app_name = 'targeted_calibrations'

urlpatterns = [
    path('nres', NRESCalibrationsView.as_view(), name='nres_home'),
    path('imager', ImagerCalibrationsView.as_view(), name='imager_home'),
    # TODO: rename this path
    path('submit-cadence', NRESCalibrationSubmissionView.as_view(), name='nres_submission'),
    path('instruments', InstrumentTypeListView.as_view(), name='instrument_type_list'),
    path('instruments/<str:instrument_type>/', InstrumentListView.as_view(), name='instrument_list'),
    path('instruments/<str:instrument_type>/<str:instrument_code>/', InstrumentTargetListView.as_view(),
         name='instrument_target_list'),
    path('instruments/<str:instrument_type>/<str:instrument_code>/<int:pk>/', InstrumentTargetDetailView.as_view(),
         name='instrument_target_detail'),
    path('cadence-toggle/<int:pk>/', NRESCadenceToggleView.as_view(), name='cadence_toggle'),
    path('cadence-delete/<int:pk>/', NRESCadenceDeleteView.as_view(), name='cadence_delete')
]
