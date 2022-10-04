from django.test import TestCase
from django.urls import reverse
import json

from data_manager.models import Layer

class get_layer_details_test(TestCase):
    @classmethod
    def setUpTestData(cls):
        congress_layer_url="https://coast.noaa.gov/arcgis/rest/services/OceanReports/USCongressionalDistricts/MapServer/export"
        Layer.objects.create(pk=1, name='arcrest_layer', layer_type='ArcRest', url=congress_layer_url, arcgis_layers="0", maxZoom=14, minZoom=6)

    def test_view_api_returns_zoom_limits(self):
        response = self.client.get('/data_manager/get_layer_details/1')
        self.assertEqual(response.status_code, 200)
        # import ipdb; ipdb.set_trace()
        result = json.loads(response.getvalue())
        self.assertTrue('name' in result.keys())
        self.assertEqual(result['name'], 'arcrest_layer')
        self.assertTrue('minZoom' in result.keys())
        self.assertTrue('maxZoom' in result.keys())
        self.assertEqual(result['minZoom'], 6)
        self.assertEqual(result['maxZoom'], 14)