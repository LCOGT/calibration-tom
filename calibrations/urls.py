from django.urls import path

from calibrations.views import CalibrationSubmissionView

urlpatterns = [
    path('', CalibrationSubmissionView.as_view(), name='calibrations_index'),
    # path('floyds_ogg', floyds_ogg, name='floyds_ogg'),
    # path('floyds_coj', floyds_coj, name='floyds_coj')
]
