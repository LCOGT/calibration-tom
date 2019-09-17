from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='calibrations_index'),
    path('floyds_ogg', views.floyds_ogg, name='floyds_ogg'),
    path('floyds_coj', views.floyds_coj, name='floyds_coj')
]
