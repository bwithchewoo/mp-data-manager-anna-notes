from django.core.management.base import BaseCommand
import sys

# Ignore the nasty SNIMissingWarning and the InsecurePlatformWarning
import urllib3
urllib3.disable_warnings()

class Command(BaseCommand):

    help = "Generate staging layers for MDAT V2"

    def handle(self, *args, **options):
        import requests
        from django.forms.models import model_to_dict
        from datetime import date
        from django.contrib.sites.models import Site
        from data_manager.models import Layer, Theme

        if not len(args) == 0:
            print('Usage: manage.py import_era (no arguments allowed)')
            sys.exit()

        django_prod_site = Site.objects.get(pk=1)
        django_stage_site = Site.objects.get(pk=2)

        try:
            parent_theme = Theme.objects.get(name='conservation')
        except:
            print("Parent Theme 'conservation' not found. Please set parent_theme.")
            import ipdb; ipdb.set_trace()

        data_source = 'Marine Life Data and Analysis Team V2'
        source_site = 'http://seamap.env.duke.edu/models/mdat/'

        mdat_prod_base = 'https://mgelmaps.env.duke.edu/mdat/rest/services/MDAT/'
        mdat_stage_base = 'https://mgelmaps.env.duke.edu/mdat_new/rest/services/MDAT_Staging/'
        avian_v1_service = 'AvianModels_SyntheticProducts'
        avian_v2_service = 'Avian_SummaryProducts'
        mammal_v1_service = 'Mammal_SyntheticProducts'
        mammal_v2_service = 'Mammal_SummaryProducts'
        fish_v1_service = 'Fish_NEFSC_SyntheticProducts'
        fish_v2_service = 'Fish_SummaryProducts_NEFSC'

        services = ['avian', 'mammal', 'fish']

        avian_v1_parent = Layer.all_objects.get(url='', name='Birds - DRAFT')
        avian_parent_dict =  model_to_dict(avian_v1_parent)
        mammal_v1_parent = Layer.all_objects.get(url='', name='Marine Mammals - DRAFT')
        mammal_parent_dict =  model_to_dict(avian_v1_parent)
        fish_v1_parent = Layer.all_objects.get(url='', name='Fish - DRAFT')
        fish_parent_dict =  model_to_dict(avian_v1_parent)

        for parent_dict in [avian_parent_dict, mammal_parent_dict, fish_parent_dict]:
            parent_dict['data_source'] = data_source
            parent_dict['source'] = source_site

            for key in ['pk','id','name','slug_name','attribute_fields','connect_companion_layers_to','lookup_table','site','sublayers','themes','bookmark']:
                try:
                    del parent_dict[key]
                except:
                    pass

        # Set metadata links
        avian_parent_dict['metadata'] = 'http://seamap.env.duke.edu/models/mdat/Avian/MDAT_v2_Avian_Summary_of_Changes.PDF'
        mammal_parent_dict['metadata'] = 'http://seamap.env.duke.edu/models/mdat/Mammal/MDAT_v2_Mammal_Summary_of_Changes.PDF'
        fish_parent_dict['metadata'] = 'http://seamap.env.duke.edu/models/mdat/Fish/MDAT_v2_Fish_Summary_of_Changes.PDF'

        # create 2 parent layers for each service:
        #       one to point at dev server
        #       one to point at anticipated live server
        (avian_stage_parent, created) = Layer.all_objects.get_or_create(name='Birds - Stage V2')
        if created:
            for key in avian_parent_dict.keys():
                setattr(avian_stage_parent, key, avian_parent_dict[key])
        (avian_prod_parent, created) = Layer.all_objects.get_or_create(name='Birds - Prod V2')
        if created:
            for key in avian_parent_dict.keys():
                setattr(avian_prod_parent, key, avian_parent_dict[key])
        (mammal_stage_parent, created) = Layer.all_objects.get_or_create(name='Marine Mammals - Stage V2')
        if created:
            for key in mammal_parent_dict.keys():
                setattr(mammal_stage_parent, key, mammal_parent_dict[key])
        (mammal_prod_parent, created) = Layer.all_objects.get_or_create(name='Marine Mammals - Prod V2')
        if created:
            for key in mammal_parent_dict.keys():
                setattr(mammal_prod_parent, key, mammal_parent_dict[key])
        (fish_stage_parent, created) = Layer.all_objects.get_or_create(name='Fish - Stage V2')
        if created:
            for key in fish_parent_dict.keys():
                setattr(fish_stage_parent, key, fish_parent_dict[key])
        (fish_prod_parent, created) = Layer.all_objects.get_or_create(name='Fish - Prod V2')
        if created:
            for key in fish_parent_dict.keys():
                setattr(fish_prod_parent, key, fish_parent_dict[key])

        parent_layers = [
            avian_stage_parent,
            avian_prod_parent,
            mammal_stage_parent,
            mammal_prod_parent,
            fish_stage_parent,
            fish_prod_parent,
        ]

        for parent_layer in parent_layers:
            parent_layer.site.add(django_stage_site)
            parent_layer.themes.add(parent_theme)
            parent_layer.save()

        service_value_lookup = {
            'avian': {
                'url': {
                    'v1': '%s%s/MapServer' % (mdat_prod_base, avian_v1_service),
                    'staging': '%s%s/MapServer' % (mdat_stage_base, avian_v2_service),
                    'prod': '%s%s/MapServer' % (mdat_prod_base, avian_v2_service),
                },
                'parent_layer': {
                    'staging': avian_stage_parent,
                    'prod': avian_prod_parent
                },
                'exclude_words': [
                    'Diversity',
                    'Northeast'
                ]
            },
            'mammal': {
                'url': {
                    'v1': '%s%s/MapServer' % (mdat_prod_base, mammal_v1_service),
                    'staging': '%s%s/MapServer' % (mdat_stage_base, mammal_v2_service),
                    'prod': '%s%s/MapServer' % (mdat_prod_base, mammal_v2_service),
                },
                'parent_layer': {
                    'staging': mammal_stage_parent,
                    'prod': mammal_prod_parent
                },
                'exclude_words': [
                    'Diversity',
                    'Northeast'
                ]
            },
            'fish': {
                'url': {
                    'v1': '%s%s/MapServer' % (mdat_prod_base, fish_v1_service),
                    'staging': '%s%s/MapServer' % (mdat_stage_base, fish_v2_service),
                    'prod': '%s%s/MapServer' % (mdat_prod_base, fish_v2_service),
                },
                'parent_layer': {
                    'staging': fish_stage_parent,
                    'prod': fish_prod_parent
                },
                'exclude_words': [
                    'Diversity',
                    'Northeast'
                ]
            },
        }

        all_layer_dict = {
            'data_publish_date': date(2018,8,8),
            'data_source': data_source,
            'source': source_site,
            'layer_type': 'ArcRest',
            'is_sublayer': True,
        }

        for service in services:
            # query v1.1 prod for layernames (to be used to lookup and modify fields as needed to preserve work)
            v1_json_url = '%s/?f=pjson' % (service_value_lookup[service]['url']['v1'])
            v1_json = requests.get(v1_json_url)
            v1_layers = v1_json.json()['layers']

            for server in ['staging', 'prod']:
                all_service_dict = {
                    'url': "%s/export" % service_value_lookup[service]['url'][server],
                    'metadata': service_value_lookup[service]['parent_layer'][server].metadata
                }
                all_service_dict.update(all_layer_dict)

                layer_name_lookup = {}
                for layer in v1_layers:
                    if (not layer['subLayerIds'] or len(layer['subLayerIds']) == 0) and not any(x in layer['name'] for x in service_value_lookup[service]['exclude_words']):
                        v1_matches = Layer.all_objects.filter(url="%s/export" % service_value_lookup[service]['url']['v1'], arcgis_layers=str(layer['id']))
                        # #   if layer exists for v1.1 in db
                        if v1_matches.count() == 1:
                            # current_layer = v1_matches[0]
                            # print('======== MATCH FOUND: %s + %s========' % (current_layer.name, layer['name']))
                            layer_name_lookup[layer['name']] = v1_matches[0]
                        elif v1_matches.count() > 0:
                            print('Multiple matches for %s. Please pick the match you want from v1_matches for the layer_name_lookup, or set to None to skip' % layer['name'])
                            layer_name_lookup[layer['name']] = v1_matches[0]
                            import ipdb; ipdb.set_trace()
                        # else:
                        #     # print('No matches returned for %s. Creating new layer' % layer['name'])
                        #     current_layer = False
                        #     # (new_layer, created) = Layer.all_objects.get_or_create(arcgis_layers=str(layer['id']),url=all_service_dict['url'],name=layer['name'],order=layer['id'])
                # Get Layer info from staging
                v2_json_url = '%s/?f=pjson' % (service_value_lookup[service]['url']['staging'])
                v2_json = requests.get(v2_json_url)
                v2_layers = v2_json.json()['layers']
                for layer in v2_layers:
                    current_layer = False
                    new_layer = False
                    db_clones = False
                    if layer['name'] in layer_name_lookup.keys():
                        print('Match found, new layer name SHOULD be "%s"' % layer_name_lookup[layer['name']])
                        # existing_matches = Layer.all_objects.filter(arcgis_layers=str(layer['id']),url=all_service_dict['url'],name=current_layer.name,order=current_layer.order)
                        current_layer = layer_name_lookup[layer['name']]
                        existing_matches = Layer.all_objects.filter(id=current_layer.id)
                        db_clones = Layer.all_objects.filter(name=current_layer.name)
                    else:
                        existing_matches = Layer.all_objects.filter(arcgis_layers=str(layer['id']),url=all_service_dict['url'],name=layer['name'],order=layer['id'])
                    if existing_matches.count() == 0:
                        (new_layer, created) = Layer.all_objects.get_or_create(arcgis_layers=str(layer['id']),url=all_service_dict['url'],name=layer['name'],order=layer['id'])
                        # new_layer.save();
                    elif existing_matches.count() == 1:
                        new_layer = existing_matches[0]
                    else:
                        print('multiple matches for new layer found. Please select 1 from existing_matches')
                        new_layer = existing_matches[0]
                        import ipdb; ipdb.set_trace()
                    # Check if record already created
                    if existing_matches.count() > 0:
                        if db_clones and db_clones.count() > 0:
                            if db_clones.count() == 1:
                                # record already created
                                new_layer = False
                            else:
                                new_layer = False
                                print('multiple candidate of db_clones. Please pick one or set new_layer = True')
                                # (new_layer, created) = Layer.all_objects.get_or_create(arcgis_layers=str(layer['id']),url=all_service_dict['url'],name=layer['name'],order=layer['id'])
                                import ipdb; ipdb.set_trace()
                        else:
                            # create clone
                            for key in ['pk','id','name','slug_name','attribute_fields','connect_companion_layers_to','lookup_table','site','sublayers','themes','bookmark']:
                                try:
                                    del new_layer[key]
                                except:
                                    pass

                    if new_layer:
                        for key in all_service_dict.keys():
                            setattr(new_layer, key, all_service_dict[key])
                        new_layer.site.add(django_prod_site)
                        new_layer.site.add(django_stage_site)
                        new_layer.themes.add(parent_theme)
                        new_layer.sublayers.add(service_value_lookup[service]['parent_layer'][server])
                        new_layer.save()
                        print('++++++++++++ Saved new layer "%s"' % new_layer.name)
                        # service_value_lookup[service]['parent_layer'][server].sublayers.add(new_layer)
                service_value_lookup[service]['parent_layer'][server].save()
