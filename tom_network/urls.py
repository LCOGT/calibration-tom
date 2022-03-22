from django.urls import path

from .views import InstrumentListView, InstrumentGroupView, InstrumentDetailView
#from .views import InstrumentListView, InstrumentImportView, InstrumentDeleteView
#from .views import InstrumentCreateView, InstrumentUpdateView, InstrumentDetailView
#from .views import InstrumentGroupView, InstrumentGroupCreateView, InstrumentAddRemoveGroupView, InstrumentGroupDeleteView

from .api_views import InstrumentViewSet
from tom_common.api_router import SharedAPIRootRouter

router = SharedAPIRootRouter()
router.register(r'instruments', InstrumentViewSet, 'instruments')

app_name = 'tom_network'

urlpatterns = [
    path('instruments/', InstrumentListView.as_view(), name='instrument_list'),
    path('instrumentgroup/', InstrumentGroupView.as_view(), name='instrumentgroup'),
    path('<int:pk>/', InstrumentDetailView.as_view(), name='detail'),
]
#    path('create/', InstrumentCreateView.as_view(), name='create'),
#    path('import/', InstrumentImportView.as_view(), name='import'),
#    path('add-remove-group/', InstrumentAddRemoveGroupView.as_view(), name='add-remove-group'),
#    path('<int:pk>/update/', InstrumentUpdateView.as_view(), name='update'),
#    path('<int:pk>/delete/', InstrumentDeleteView.as_view(), name='delete'),
#    path('instrumentgroup/<int:pk>/delete/', InstrumentGroupDeleteView.as_view(), name='delete-group'),
#    path('instrumentgroup/create/', InstrumentGroupCreateView.as_view(), name='create-group')

