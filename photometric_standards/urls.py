from django.urls import path

from photometric_standards.views import PhotometricStandardsView, PhotometricStandardsForm, PhotometricStandardsTargets
from photometric_standards.views import PhotometricStandardsCadencesView, PhotometricStandardsCadencesSiteView, PhotometricStandardsCadencesList, PhotometricStandardsCadenceToggleView, PhotometricStandardsCadenceDeleteView

app_name = 'photometric_standards'

urlpatterns = [
    path('cadences/', PhotometricStandardsCadencesView.as_view(), name='photometric_standards_cadences'),
    path('cadence-toggle/<int:pk>/', PhotometricStandardsCadenceToggleView.as_view(), name='cadence_toggle'),
    path('cadence-delete/<int:pk>/', PhotometricStandardsCadenceDeleteView.as_view(), name='cadence_delete'),
    path('form/', PhotometricStandardsForm.as_view(), name='photometric_standards_form'),
    path('targets/', PhotometricStandardsTargets.as_view(), name='photometric_standards_targets'),
    path('site/<str:site>/', PhotometricStandardsCadencesSiteView.as_view(), name='site_detail')
]
