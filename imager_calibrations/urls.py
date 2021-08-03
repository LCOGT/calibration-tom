from django.urls import path

from imager_calibrations.views import ImagerCadenceView, ImagerCadenceSiteView

app_name = 'imager_calibrations'

urlpatterns = [
    path('list/', ImagerCadenceView.as_view(), name='imager_home'),
    path('site/<str:site>/', ImagerCadenceSiteView.as_view(), name='site_detail')
]