from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='calibrations_index'),
]
