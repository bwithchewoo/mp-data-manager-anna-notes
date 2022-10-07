from importlib.util import source_hash
from django.conf import settings
from django.test import TestCase
from data_manager.models import Layer, Theme, AttributeInfo, LookupInfo, MultilayerAssociation, MultilayerDimension, MultilayerDimensionValue
from data_manager.views import compare_remote_layers
import json
import os.path


class MigrateAPIQueryTest(TestCase):
    TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
    FIXTURE_FILE = os.path.join(TEST_ROOT, 'fixtures', 'wcoa_data_manager_fixture.json')
    fixtures = [FIXTURE_FILE]

    def test_query_remote_layers(self):
        source_api_url = "/data_manager/migration/"
        get_layers_api = "{}layer_status/".format(source_api_url)

        response = self.client.get(get_layers_api)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['content-type'])
        data = json.loads(response.content)
        self.assertTrue('themes' in data.keys())
        self.assertEqual(len(data['themes'].keys()), 11)
        self.assertTrue('layers' in data.keys())
        self.assertEqual(len(data['layers'].keys()), 469)

    def test_query_migration_layer_details(self):
        self.assertTrue(True)
        source_api_url = "/data_manager/migration/"
        post_request_layer_details_api = "{}layer_details/".format(source_api_url)
        requested_layers = [4, 17, 157, 784]
        response = self.client.post(post_request_layer_details_api, {'layers': requested_layers})
        self.assertEqual(response.status_code, 200)
        self.assertTrue('application/json' in response['content-type'])
        data = json.loads(response.content)
        self.assertTrue('themes' in data.keys())
        self.assertTrue('layers' in data.keys())
        self.assertEqual(len(data['layers'].keys()), len(requested_layers))
        for key in requested_layers:
            self.assertTrue(str(key) in data['layers'].keys())


class MigrateMergeTest(TestCase):
    TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
    FIXTURE_FILE = os.path.join(TEST_ROOT, 'fixtures', 'orowind_data_manager_fixture.json')
    fixtures = [FIXTURE_FILE]

    def test_compare_remote_layers(self):
        # simulate input from API call to remote: JSON converted to a Dict
        TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(TEST_ROOT, 'fixtures', 'wcoa_layer_status_API_response.json'), encoding='utf-8') as wcoa_data_file:
            wcoa_dict = json.loads(wcoa_data_file.read())

        comparison_results = compare_remote_layers(wcoa_dict)
        self.assertTrue('themes' in comparison_results.keys())
        self.assertTrue('layers' in comparison_results.keys())
        # nearly identical theme
        self.assertEqual(comparison_results['themes']['4']['source'], 'match')
        self.assertTrue(comparison_results['themes']['4']['modified'])
        self.assertEqual(comparison_results['themes']['4']['newest'], 'local')
        # Theme that only exists on remote
        self.assertEqual(comparison_results['themes']['17']['source'], 'remote')
        self.assertEqual(comparison_results['themes']['17']['modified'], False)
        # unrelated layers that share an ID. Remote is ~2yrs newer.
        self.assertEqual(comparison_results['layers']['157']['source'], 'match')
        self.assertTrue(comparison_results['layers']['157']['modified'])
        self.assertEqual(comparison_results['layers']['157']['newest'], 'remote')
        # Layer ID that only exists locally
        self.assertEqual(comparison_results['layers']['485']['source'], 'local')
        self.assertEqual(comparison_results['layers']['485']['modified'], False)
        # Layer ID that only exists remotely
        self.assertEqual(comparison_results['layers']['784']['source'], 'remote')
        self.assertEqual(comparison_results['layers']['784']['modified'], False)

    def test_merge_migration_layers(self):
        self.assertTrue(True)