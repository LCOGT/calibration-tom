from django.urls import path

from imager_calibrations.views import ImagerCadenceView, ImagerCadenceSiteView, ImagerCalibrationsView, ImagerCalibrationsForm, ImagerCalibrationsTargets

app_name = 'imager_calibrations'

urlpatterns = [
    path('cadences/', ImagerCadenceView.as_view(), name='imager_cadences'),
    path('form/', ImagerCalibrationsForm.as_view(), name='imager_form'),
    path('targets/', ImagerCalibrationsTargets.as_view(), name='imager_targets'),
    path('site/<str:site>/', ImagerCadenceSiteView.as_view(), name='site_detail')
]
