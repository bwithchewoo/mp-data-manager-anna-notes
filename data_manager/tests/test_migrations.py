from importlib.util import source_hash
from django.conf import settings
from django.test import TestCase
from data_manager.models import Layer, Theme, AttributeInfo, LookupInfo, MultilayerAssociation, MultilayerDimension, MultilayerDimensionValue
from data_manager.views import compare_remote_layers, migration_merge_layer
from datetime import datetime
import json
import os.path
import time


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
        OCS_layer = '0229f63e-15ec-488a-b6ce-1dbe8c2955b9'
        limits_layer = 'f971c98f-7f0e-4d0a-a3d0-9362daceb905'
        pipeline_layer = '046721a4-4d29-4555-82b0-0874c6eefee1'
        requested_layers = [OCS_layer, limits_layer, pipeline_layer]
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
        human_theme_share = '2bd7f519-360f-4d3f-b6b4-9cf932501e26'
        biological_theme_remote = 'f31cafee-d517-4993-85d4-1dc3bcbb36d9'
        companion_theme_local = 'cdbf1ba5-6988-4af9-9495-e7cef298b69b'
        limits_layer_share = 'f971c98f-7f0e-4d0a-a3d0-9362daceb905'
        OCS_layer_remote = '0229f63e-15ec-488a-b6ce-1dbe8c2955b9'
        paleoshorelines_layer_local = 'b8af0f45-c0da-49ae-8f49-1745b406fdf4'
        # nearly identical theme
        self.assertEqual(comparison_results['themes'][human_theme_share]['source'], 'match')
        self.assertTrue(comparison_results['themes'][human_theme_share]['modified'])
        self.assertEqual(comparison_results['themes'][human_theme_share]['newest'], 'local')
        # Theme that only exists on remote
        self.assertEqual(comparison_results['themes'][biological_theme_remote]['source'], 'remote')
        self.assertEqual(comparison_results['themes'][biological_theme_remote]['modified'], False)
        # Theme that only exists locally
        self.assertEqual(comparison_results['themes'][companion_theme_local]['source'], 'local')
        self.assertEqual(comparison_results['themes'][companion_theme_local]['modified'], False)
        # unrelated layers that share an ID. Remote is ~2yrs newer.
        self.assertEqual(comparison_results['layers'][limits_layer_share]['source'], 'match')
        self.assertTrue(comparison_results['layers'][limits_layer_share]['modified'])
        self.assertEqual(comparison_results['layers'][limits_layer_share]['newest'], 'remote')
        # Layer ID that only exists locally
        self.assertEqual(comparison_results['layers'][paleoshorelines_layer_local]['source'], 'local')
        self.assertEqual(comparison_results['layers'][paleoshorelines_layer_local]['modified'], False)
        # Layer ID that only exists remotely
        self.assertEqual(comparison_results['layers'][OCS_layer_remote]['source'], 'remote')
        self.assertEqual(comparison_results['layers'][OCS_layer_remote]['modified'], False)

    def test_merge_migration_layers(self):
        '''
            What will the backend need to do this?
            * Endpoint URL
            * REMOTE UUIDs
            * REMOTE IDs
            * LOCAL UUIDs (if syncing DBs)
            * LOCAL IDs
            * Info to tie REMOTE ro LOCAL (ID?)
            * Authentication! 
        '''
        endpoint = '/'
        TEST_ROOT = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(TEST_ROOT, 'fixtures', 'wcoa_layer_status_API_response.json'), encoding='utf-8') as wcoa_data_file:
            wcoa_dict = json.loads(wcoa_data_file.read())
        human_theme_share = '2bd7f519-360f-4d3f-b6b4-9cf932501e26'
        theme_match_pair = {
            'local': {
                'id': 5,
                'uuid': human_theme_share
            },
            'remote': {
                'id': 5,
                'uuid': human_theme_share
            }
        }
        biological_theme_remote = 'f31cafee-d517-4993-85d4-1dc3bcbb36d9'
        companion_theme_local = 'cdbf1ba5-6988-4af9-9495-e7cef298b69b'
        limits_layer_share = 'f971c98f-7f0e-4d0a-a3d0-9362daceb905'
        layer_match_pair = {
            'local': {
                'id': 289,
                'uuid': limits_layer_share
            },
            'remote': {
                'id': 590,
                'uuid': limits_layer_share
            }
        }
        OCS_layer_remote = '0229f63e-15ec-488a-b6ce-1dbe8c2955b9'
        remote_only_pair = {
            'local': {
                'id': None,
                'uuid': None
            },
            'remote': {
                'id': 472,
                'uuid': OCS_layer_remote
            }
        }
        paleoshorelines_layer_local = 'b8af0f45-c0da-49ae-8f49-1745b406fdf4'
        remote_override_pair = {
            'local': {
                'id': 326,
                'uuid': "666b3f5a-d35c-4f6d-b3a3-50a6dfb7ea88"
            },
            'remote': {
                'id': 473,
                'uuid': "c43247b2-79b3-49f1-985c-efee43cf388a"
            }
        }

        SELECTED_IDS = [
            layer_match_pair,
            remote_only_pair,
            remote_override_pair
        ]

        for pair in SELECTED_IDS:
            # leave layer detail queries to Front End JS.
            with open(os.path.join(TEST_ROOT, 'fixtures', 'remote_layer_detail_response_{}.json'.format(pair['remote']['uuid'])), encoding='utf-8') as remote_layer_details:
                remote_layer_dict = json.loads(remote_layer_details.read())

            print("TESTING {}:{} <-- {}:{}".format(pair['local']['id'], pair['local']['uuid'],pair['remote']['id'], pair['remote']['uuid']))

            response = json.loads(migration_merge_layer(pair['local']['id'], remote_layer_dict).content)
            self.assertEqual(response['status'], 'Success')
            time.sleep(0.1)
            try:
                local_layer = Layer.all_objects.get(uuid=pair['remote']['uuid'])
            except Exception as e:
                print(e)
                print('Waiting...')
                time.sleep(10.0)
                local_layer = Layer.all_objects.get(uuid=pair['remote']['uuid'])
            self.assertEqual(str(local_layer.uuid), remote_layer_dict['uuid'])
            local_date_modified = local_layer.date_modified.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            local_date_modified = local_date_modified[:-4] + local_date_modified[-1:]
            self.assertEqual(local_date_modified, remote_layer_dict['date_modified'])

        self.assertTrue(True)