"""django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', include('tom_common.urls')),
    path('targeted/', include('targeted_calibrations.urls', namespace='targeted_calibrations')),
    #path('nres/', include('nres_calibrations.urls', namespace='nres_calibrations')),
    path('calibrations/', include('calibrations.urls')),
    # admin comes from somewhere else
]

# this is to serve static file from a debug Dockerfile environment (performs a findstatic)
# (i.e. without this a local Dockerfile-deployed instance won't find the staticfiles from
# the other INSTALLED_APPS)
urlpatterns += staticfiles_urlpatterns()
