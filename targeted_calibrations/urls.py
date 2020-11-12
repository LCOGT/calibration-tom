from django.urls import path

#from targeted_calibrations.views import NRESCalibrationsIndex, NRESInstrumentClassListView, NRESInstrumentTargetListView, \
#    NRESInstrumentTargetDetailView, ExpertimentListView

from targeted_calibrations.views import InstrumentTypeListView
from targeted_calibrations.views import InstrumentListView
from targeted_calibrations.views import InstrumentTargetListView
from targeted_calibrations.views import InstrumentTargetDetailView

# app_name is required in order to specify a namespace in include()
app_name = 'targeted_calibrations'

# urlpatterns = [
#     path('', NRESCalibrationsIndex.as_view(), name='nres_index'),
#     path('', NRESCalibrationsIndex.as_view(), name='targeted_calibrations_index'),
#     path('imager/', NRESCalibrationsIndex.as_view(), name='imager_index'),
#     path('experiment/', ExpertimentListView.as_view(), name='experiment_list_view'),
#     path('instruments/', NRESInstrumentClassListView.as_view(), name='nres_instrument_list'),
#     path('instruments/', NRESInstrumentClassListView.as_view(), name='imager_instrument_list'),
#     path('instruments/<str:inst>/', NRESInstrumentTargetListView.as_view(), name='nres_instrument_targets'),
#     path('instruments/<str:inst>/<int:target_id>/', NRESInstrumentTargetDetailView.as_view(), name='nres_target_detail'),
# ]


urlpatterns = [
    path('', InstrumentTypeListView.as_view(), name='instrument_type_list'),
    path('<str:instrument_type>/', InstrumentListView.as_view(), name='instrument_list'),
    path('<str:instrument_type>/<str:instrument_code>', InstrumentTargetListView.as_view(), name='instrument_target_list'),
    path('<str:instrument_type>/<str:instrument_code>/<int:target_id>', InstrumentTargetDetailView.as_view(),
         name='instrument_target_detail'),
]