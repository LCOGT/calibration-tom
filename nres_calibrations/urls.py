from django.urls import path

from nres_calibrations.views import NRESCalibrationsIndex, NRESInstrumentClassListView, NRESInstrumentTargetListView, \
    NRESInstrumentTargetDetailView

# app_name is required in order to specify a namespace in include()
app_name = 'nres_calibrations'

urlpatterns = [
    path('', NRESCalibrationsIndex.as_view(), name='nres_calibrations_index'),
    path('instruments/', NRESInstrumentClassListView.as_view(), name='nres_instrument_list'),
    path('instruments/<str:inst>/', NRESInstrumentTargetListView.as_view(), name='nres_instrument_targets'),
    path('instruments/<str:inst>/<int:target_id>/', NRESInstrumentTargetDetailView.as_view(), name='nres_target_detail'),
]
