from django.contrib import admin

from .models import Site
from .models import Enclosure
from .models import Telescope
from .models import Camera
from .models import CameraType
from .models import FilterWheel
from .models import OpticalElementGroup
from .models import Instrument

admin.site.register(Site)
admin.site.register(Enclosure)
admin.site.register(Telescope)
admin.site.register(Camera)
admin.site.register(CameraType)
admin.site.register(FilterWheel)
admin.site.register(OpticalElementGroup)
admin.site.register(Instrument)



