# from django.conf.urls import url, include, patterns
from django.urls import re_path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'layers', views.LayerViewSet)

urlpatterns = [
    #'',
    re_path(r'^nested_admin/', include('nested_admin.urls')),
    re_path(r'^api/', include(router.urls)),
    re_path(r'^layer/([A-Za-z0-9_-]+)$', views.update_layer),
    re_path(r'^layer$', views.create_layer),
    re_path(r'^get_json$', views.get_json),
    re_path(r'^wms_capabilities', views.wms_request_capabilities),
]
