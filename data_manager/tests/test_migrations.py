from django.conf import settings
from django.test import TestCase
from data_manager.models import Layer, Theme, AttributeInfo, LookupInfo, MultilayerAssociation, MultilayerDimension, MultilayerDimensionValue
import json
import os.path


class MigrateAPIQueryTest(TestCase):
    TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
    FIXTURE_FILE = os.path.join(TEST_ROOT, 'fixtures', 'data_manager_fixture.json')
    fixtures = [FIXTURE_FILE]

    def setUp(self):
        self.factory = AsyncRequestFactory()

    def test_query_remote_layers(self):
        source_api_url = "/data_manager/migration/"
        get_layers_api = "{}layer_status/".format(source_api_url)

        response = self.client.get(get_layers_api)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['content-type'])
        data = json.loads(response.content)