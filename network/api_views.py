from django_filters import rest_framework as drf_filters
from guardian.mixins import PermissionListMixin
from guardian.shortcuts import get_objects_for_user
from rest_framework.mixins import DestroyModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from network.serializers import InstrumentSerializer


permissions_map = {  # TODO: Use the built-in DRF mapping or just switch to DRF entirely.
        'GET': 'view_target',
        'OPTIONS': [],
        'HEAD': [],
        'POST': 'add_target',
        'PATCH': 'change_target',
        'PUT': 'change_target',
        'DELETE': 'delete_target'
    }


# Though DRF supports using django-guardian as a permission backend without explicitly using PermissionListMixin, we
# chose to use it because it removes the requirement that a user be granted both object- and model-level permissions,
# and a user that has object-level permissions is understood to also have model-level permissions.
# For whatever reason, get_queryset has to be explicitly defined, and can't be set as a property, else the API won't
# respect permissions.
#
# At present, create is not restricted at all. This seems to be a limitation of django-guardian and should be revisited.
class InstrumentViewSet(ModelViewSet, PermissionListMixin):
    """
    Viewset for Instrument objects. By default supports CRUD operations.
    See the docs on viewsets: https://www.django-rest-framework.org/api-guide/viewsets/

    To view supported query parameters, please use the ``OPTIONS`` endpoint, which can be accessed through the web UI.

    **Please note that ``groups`` are an accepted query parameters for the ``CREATE`` endpoint. The ``groups`` parameter
    will specify which ``groups`` can view the created Instrument. If no ``groups`` are specified, the ``Instrument`` will only
    be visible to the user that created the ``Instrument``. Make sure to check your ``groups``!!**

    """
    serializer_class = InstrumentSerializer
    filter_backends = (drf_filters.DjangoFilterBackend,)
    #filterset_class = InstrumentFilter

    def get_queryset(self):
        permission_required = permissions_map.get(self.request.method)
        return get_objects_for_user(self.request.user, f'network.{permission_required}')


