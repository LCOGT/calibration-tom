from django.urls import path

from targeted_calibrations.views import InstrumentTypeListView
from targeted_calibrations.views import InstrumentListView
from targeted_calibrations.views import InstrumentTargetListView
from targeted_calibrations.views import InstrumentTargetDetailView

# app_name is required in order to specify a namespace in include()
app_name = 'targeted_calibrations'

urlpatterns = [
    path('', InstrumentTypeListView.as_view(), name='instrument_type_list'),
    path('<str:instrument_type>/', InstrumentListView.as_view(), name='instrument_list'),
    path('<str:instrument_type>/<str:instrument_code>/', InstrumentTargetListView.as_view(),
         name='instrument_target_list'),
    path('<str:instrument_type>/<str:instrument_code>/<int:pk>/', InstrumentTargetDetailView.as_view(),
         name='instrument_target_detail'),
]
