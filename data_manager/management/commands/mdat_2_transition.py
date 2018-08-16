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

        # Delete previously imported layers
        # print("Deleting previously imported MDAT V2 layers")
        # Layer.objects.filter(data_source=data_source,is_sublayer=True,data_publish_date=date(2018,8,8)).delete()

        services = ['avian', 'mammal', 'fish']

        avian_v1_parent = Layer.all_objects.get(url='', name='Birds - V1', layer_type='checkbox')
        avian_parent_dict =  model_to_dict(avian_v1_parent)
        mammal_v1_parent = Layer.all_objects.get(url='', name='Marine Mammals - V1', layer_type='checkbox')
        mammal_parent_dict =  model_to_dict(avian_v1_parent)
        fish_v1_parent = Layer.all_objects.get(url='', name='Fish - V1', layer_type='checkbox')
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
        avian_parent_dict['metadata'] = 'http://seamap.env.duke.edu/models/mdat/Avian/MDAT_Avian_Summary_Products_Metadata.pdf'
        mammal_parent_dict['metadata'] = 'http://seamap.env.duke.edu/models/mdat/Mammal/MDAT_Mammal_Summary_Products_Metadata.pdf'
        fish_parent_dict['metadata'] = 'http://seamap.env.duke.edu/models/mdat/Fish/MDAT_NEFSC_Fish_Summary_Products_Metadata.pdf'

        # create 2 parent layers for each service:
        #       one to point at dev server
        #       one to point at anticipated live server
        (avian_stage_parent, created) = Layer.all_objects.get_or_create(name='Birds - Stage V2')
        if created:
            for key in avian_parent_dict.keys():
                setattr(avian_stage_parent, key, avian_parent_dict[key])
        else:
            for key in ['metadata']:
                setattr(avian_stage_parent, key, avian_parent_dict[key])
        (avian_prod_parent, created) = Layer.all_objects.get_or_create(name='Birds')
        if created:
            for key in avian_parent_dict.keys():
                setattr(avian_prod_parent, key, avian_parent_dict[key])
        else:
            for key in ['metadata']:
                setattr(avian_prod_parent, key, avian_parent_dict[key])
        (mammal_stage_parent, created) = Layer.all_objects.get_or_create(name='Marine Mammals - Stage V2')
        if created:
            for key in mammal_parent_dict.keys():
                setattr(mammal_stage_parent, key, mammal_parent_dict[key])
        else:
            for key in ['metadata']:
                setattr(mammal_stage_parent, key, mammal_parent_dict[key])
        (mammal_prod_parent, created) = Layer.all_objects.get_or_create(name='Marine Mammals')
        if created:
            for key in mammal_parent_dict.keys():
                setattr(mammal_prod_parent, key, mammal_parent_dict[key])
        else:
            for key in ['metadata']:
                setattr(mammal_prod_parent, key, mammal_parent_dict[key])
        (fish_stage_parent, created) = Layer.all_objects.get_or_create(name='Fish - Stage V2')
        if created:
            for key in fish_parent_dict.keys():
                setattr(fish_stage_parent, key, fish_parent_dict[key])
        else:
            for key in ['metadata']:
                setattr(fish_stage_parent, key, fish_parent_dict[key])
        (fish_prod_parent, created) = Layer.all_objects.get_or_create(name='Fish')
        if created:
            for key in fish_parent_dict.keys():
                setattr(fish_prod_parent, key, fish_parent_dict[key])
        else:
            for key in ['metadata']:
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
            parent_layer.save(recache=False)

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
                    'diversity',
                    'northeast',
                    ' - atlantic scale',
                    'breeding',
                    'feeding',
                    'resident',
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
                    'diversity',
                    'northeast',
                    ' - atlantic scale'
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
                    'diversity',
                    'northeast',
                    ' - atlantic scale'
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
            # RDH: V1 services are no longer available
            # print("Getting V1 layers for %s" % service)
            # # query v1.1 prod for layernames (to be used to lookup and modify fields as needed to preserve work)
            # v1_json_url = '%s/?f=pjson' % (service_value_lookup[service]['url']['v1'])
            # v1_json = requests.get(v1_json_url)
            # v1_layers = v1_json.json()['layers']
            # if not v1_layers or len(v1_layers) < 1:
            #     print('ERROR: Did not get layers for V1 %s' % service)
            #     import ipdb; ipdb.set_trace()
            #
            # # print('Found %d layers for V1 %s' % (len(v1_layers),service))
            #
            # layer_name_lookup = {}
            # for layer in v1_layers:
            #     v1_matches = Layer.all_objects.filter(url="%s/export" % service_value_lookup[service]['url']['v1'], arcgis_layers=str(layer['id']))
            #     # #   if layer exists for v1.1 in db
            #     if v1_matches.count() == 1:
            #         layer_name_lookup[layer['name']] = v1_matches[0]
            #     elif v1_matches.count() > 0:
            #         print('Multiple matches for %s. Please pick the match you want from v1_matches for the layer_name_lookup, or set to None to skip' % layer['name'])
            #         layer_name_lookup[layer['name']] = v1_matches[0]
            #         import ipdb; ipdb.set_trace()

            for server in ['staging', 'prod']:
                all_service_dict = {
                    'url': "%s/export" % service_value_lookup[service]['url'][server],
                    'metadata': service_value_lookup[service]['parent_layer'][server].metadata
                }
                all_service_dict.update(all_layer_dict)

                # Get Layer info from staging
                print("Getting V2 layers for %s on %s server" % (service, server))
                v2_json_url = '%s/?f=pjson' % (service_value_lookup[service]['url']['staging'])
                v2_json = requests.get(v2_json_url)
                v2_layers = v2_json.json()['layers']
                if not v2_layers or len(v2_layers) < 1:
                    print('ERROR: Did not get layers for V2 %s on %s server' % (service, server))
                    import ipdb; ipdb.set_trace()

                # print('Found %d layers for V2 %s on %s server' % (len(v2_layers),service, server))
                layers_saved = 0
                layers_skipped = 0
                for layer in v2_layers:
                    if (not layer['subLayerIds'] or len(layer['subLayerIds']) == 0) and not any(x.lower() in layer['name'].lower() for x in service_value_lookup[service]['exclude_words']):
                        current_layer = False
                        new_layer = False           # really bad var name for 'layer we wish to update'
                        existing_match = False      # 'a counterpart of this layer has been located from v1'
                        db_clones = False           # 'one or more nearly identical layers have already been created'
                        companion_layers = False    # v1 layer companion layers that need to be hooked up to new layer
                        attribute_fields = False    # v1 layer attribute fileds to copy over
                        lookup_table = False        # v1 layer lookup_table to copy over
                        created = True              # a new layer is being created
                        try:
                            new_layer = Layer.objects.get(arcgis_layers=str(layer['id']),url=all_service_dict['url'])
                            created = False
                        except:
                            pass
                        if not new_layer:
                            if layer['name'] in layer_name_lookup.keys():
                                # print('Match found, new layer name SHOULD be "%s"' % layer_name_lookup[layer['name']])
                                # existing_matches = Layer.all_objects.filter(arcgis_layers=str(layer['id']),url=all_service_dict['url'],name=current_layer.name,order=current_layer.order)
                                current_layer = layer_name_lookup[layer['name']]
                                # EXISTING_MATCHES should in this case be a queryset of a single existing v1 record - the match
                                existing_match = Layer.all_objects.get(id=current_layer.id)
                                # DB_CLONES are already created v2 layers matching old v1 layers
                                db_clones = Layer.all_objects.filter(name=current_layer.name,**all_service_dict)
                            if existing_match and not db_clones.count() > 0:
                                companion_layers = existing_match.connect_companion_layers_to.all()
                                attribute_fields = existing_match.attribute_fields.all()
                                lookup_table = existing_match.lookup_table.all()
                                new_layer = existing_match
                                new_layer.pk = None
                                new_layer.bookmark = None
                                new_layer.arcgis_layers=str(layer['id'])

                            else:
                                try:
                                    (new_layer, created) = Layer.all_objects.get_or_create(arcgis_layers=str(layer['id']),**all_service_dict)
                                    if created:
                                        new_layer.name = layer['name']
                                        new_layer.order = layer['id']
                                except:
                                    import ipdb; ipdb.set_trace()

                        if new_layer:
                            if created:
                                for key in all_service_dict.keys():
                                    setattr(new_layer, key, all_service_dict[key])
                                new_layer.save(recache=False)
                                new_layer.site.add(django_prod_site)
                                new_layer.site.add(django_stage_site)
                                new_layer.themes.add(parent_theme)
                                # new_layer.slug = "%s-v2-%s" % (new_layer.slug_name,server)
                                new_layer.sublayers.add(service_value_lookup[service]['parent_layer'][server])
                                if current_layer and not current_layer.name == new_layer.name:
                                    print("Name attribute did not copy from old to new layer. Investigate.")
                                    import ipdb; ipdb.set_trace()
                                if companion_layers and not new_layer.connect_companion_layers_to.all() == companion_layers:
                                    for companion_layer in companion_layers:
                                        new_layer.connect_companion_layers_to.add(companion_layer)
                                if attribute_fields and not new_layer.attribute_fields.all() == attribute_fields:
                                    for attribute_field in attribute_fields:
                                        new_layer.attribute_fields.add(attribute_field)
                                if lookup_table and not new_layer.lookup_table.all() == lookup_table:
                                    for lookup in lookup_table:
                                        new_layer.lookup_table.add(lookup)
                            else:
                                for key in ['metadata']:
                                    setattr(new_layer, key, all_service_dict[key])
                            new_layer.save(recache=False,slug_name="%s-v2-%s" % (new_layer.slug,server))
                            layers_saved += 1
                    else:
                        layers_skipped += 1

                service_value_lookup[service]['parent_layer'][server].save(recache=False)
                print('created %d layers for V2 %s on %s server' % (layers_saved, service, server))
                if len(v2_layers) > layers_saved + layers_skipped:
                    missed_layers = len(layers) - layers_saved - layers_skipped
                    print('Missed %d layers for V2 %s on %s server' % (missed_layers, service, server))
                    import ipdb; ipdb.set_trace()

        from django.core.cache import cache
        cache.clear()
