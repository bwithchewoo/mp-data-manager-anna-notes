from rest_framework import serializers
from .models import Layer

class BriefLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ('id', 'name', 'layer_type', 'url', 'opacity', 'vector_color', 'vector_fill', 'vector_outline_color', 'vector_outline_opacity', 'arcgis_layers')
