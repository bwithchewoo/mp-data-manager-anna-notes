from rest_framework import serializers
from .models import Layer

class BriefLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ('id', 'layer_type', 'url')
