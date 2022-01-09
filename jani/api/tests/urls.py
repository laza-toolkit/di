import typing as t 
from django.urls import path, include
from jani.di import get_ioc_container
from ninja import NinjaAPI





ninja = NinjaAPI()

from .views import jani, drf






urlpatterns = [
    # path("jani/test/<p1>/<p2>", func.view), 
    # path('users/', UsersView.as_view({'get': 'list', 'put': 'create'})),
    # path('ninja/', njapi.urls),

    path('drf/', include(drf.router.urls)),
    path('jani/', include(jani.router.urls)),
    # path('api/drf/', include(router.urls)),
]