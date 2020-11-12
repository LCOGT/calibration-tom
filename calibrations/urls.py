from django.urls import path
from django.views.generic import TemplateView
from calibrations.views import CalibrationSubmissionView

app_name = 'calibrations'

urlpatterns = [
    path('', CalibrationSubmissionView.as_view(), name='calibrations_index'),
    path('bias/', TemplateView.as_view(template_name="calibrations/bias_stub.html"), name='bias_home'),
    path('dark/', TemplateView.as_view(template_name="calibrations/dark_stub.html"), name='dark_home'),
    path('flat/', TemplateView.as_view(template_name="calibrations/flat_stub.html"), name='flat_home'),
]
