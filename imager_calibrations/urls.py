from django.urls import path

from imager_calibrations.views import ImagerCadenceView, ImagerCadenceSiteView, ImagerCalibrationsView

app_name = 'imager_calibrations'

urlpatterns = [
    path('cadences/', ImagerCadenceView.as_view(), name='imager_home'),
    path('targets/', ImagerCalibrationsView.as_view(), name='imager_home'),
    path('site/<str:site>/', ImagerCadenceSiteView.as_view(), name='site_detail')
]
