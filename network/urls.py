from django.urls import path

from .views import InstrumentListView, InstrumentGroupView, InstrumentDetailView

from .api_views import InstrumentViewSet
from tom_common.api_router import SharedAPIRootRouter

router = SharedAPIRootRouter()
router.register(r'instruments', InstrumentViewSet, 'instruments')

app_name = 'network'

urlpatterns = [
    path('instruments/', InstrumentListView.as_view(), name='instrument_list'),
    path('instrumentgroup/', InstrumentGroupView.as_view(), name='instrumentgroup'),
    path('<int:pk>/', InstrumentDetailView.as_view(), name='detail'),
]

