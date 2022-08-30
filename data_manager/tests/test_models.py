from django.test import TestCase
from data_manager.models import Layer

# Create your tests here.
class DemoTest(TestCase):

    def test_demo(self):
        print('Assert True')
        self.assertTrue('a' == 'A'.lower())
        print('Assert Equal')
        self.assertEqual('a', 'A'.lower())


class LayerTest(TestCase):

    def create_layer(self, name='New Layer', layer_type='ArcRest', url=None, arcgis_layers=None):
        return Layer.objects.create(name=name, layer_type=layer_type, url=url, arcgis_layers=arcgis_layers)

    def test_arcrest_layer(self):
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        congress_layer = self.create_layer(name='arcrest_layer', layer_type='ArcRest', url=congress_layer_url, arcgis_layers="0")
        self.assertTrue(isinstance(congress_layer, Layer))
        self.assertTrue(hasattr(congress_layer, 'maxZoom'))
        self.assertTrue(hasattr(congress_layer, 'minZoom'))
