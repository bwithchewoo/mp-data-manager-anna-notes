from rest_framework import serializers
from .models import Layer

class BriefLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ('id', 'name', 'layer_type', 'url')
