from django.urls import path

from photometric_standards.views import PhotometricStandardsCadenceView, PhotometricStandardsCadenceSiteView, PhotometricStandardsCalibrationsView, PhotometricStandardsCalibrationsForm, PhotometricStandardsCalibrationsTargets

app_name = 'photometric_standards'

urlpatterns = [
    path('cadences/', PhotometricStandardsCadenceView.as_view(), name='photometric_standards_cadences'),
    path('form/', PhotometricStandardsForm.as_view(), name='photometric_standards_form'),
    path('targets/', PhotometricStandardsTargets.as_view(), name='photometric_standards_targets'),
    path('site/<str:site>/', PhotometricStandardsCadenceSiteView.as_view(), name='site_detail')
]
