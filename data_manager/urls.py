from django.conf.urls import url, include, patterns
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'layers', views.LayerViewSet)

urlpatterns = patterns('',
    url(r'^api/', include(router.urls)),
    (r'^layer/([A-Za-z0-9_-]+)$', views.update_layer),
    (r'^layer$', views.create_layer),
    (r'^get_json$', views.get_json),
    (r'^wms_capabilities', views.wms_request_capabilities),
)
