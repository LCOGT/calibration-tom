from django.urls import path

from imager_calibrations.views import ImagerCadenceView

app_name = 'imager_calibrations'

urlpatterns = [
    path('list', ImagerCadenceView.as_view(), name='imager_home'),
]