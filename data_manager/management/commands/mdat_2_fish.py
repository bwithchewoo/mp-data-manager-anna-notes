from django.core.management.base import BaseCommand
import sys

# Ignore the nasty SNIMissingWarning and the InsecurePlatformWarning
import urllib3
urllib3.disable_warnings()

class Command(BaseCommand):

    help = "Generate staging layers for MDAT Fish Summary (V2.1)"

    def handle(self, *args, **options):
        ##############################################
        # DEPENDENCIES
        ##############################################
        import requests
        from django.forms.models import model_to_dict
        from datetime import date
        from django.contrib.sites.models import Site
        from data_manager.models import Layer, Theme

        ##############################################
        # SETTINGS
        ##############################################
        #---------------------------------------------
        #- new server/layers settings
        #---------------------------------------------
        # mdat_base = 'https://mgelmaps.env.duke.edu/mdat/rest/services/MDAT/'
        mdat_base = 'https://mgelmaps.env.duke.edu/mdat/rest/services/MDAT_Staging/'
        data_source = 'Marine-Life Data and Analysis Team (V2.1)'
        publish_date = date(2019,6,24)
        source_site = 'http://seamap.env.duke.edu/models/mdat/'
        source_metadata = 'http://seamap.env.duke.edu/models/mdat/Fish/MDAT_NEFSC_Fish_Summary_Products_Metadata.pdf'
        # RDH 2019-06-03: Are we worried about other services?
        services = ['fish']
        fish_service = 'Fish_SummaryProducts_NEFSC'

        #---------------------------------------------
        #- old layer settings
        #---------------------------------------------
        old_layer_name = 'Fish'
        old_layer_type = 'checkbox'
        old_theme_name = 'conservation'
        old_data_source = 'Marine Life Data and Analysis Team V2'
        parent_theme = Theme.all_objects.get(name='conservation')
        try:
            fish_parent = Layer.all_objects.get(name__iexact=old_layer_name, layer_type=old_layer_type, themes=parent_theme, data_source=old_data_source)
        except Exception as e:
            parent_layer_dict = {
              'data_source': u'Marine Life Data and Analysis Team V2',
              'layer_type': u'checkbox',
              'metadata': u'http://seamap.env.duke.edu/models/mdat/Fish/MDAT_NEFSC_Fish_Summary_Products_Metadata.pdf',
              'name': u'Fish',
              'order': 10,
              'source': u'http://seamap.env.duke.edu/models/mdat/',
            }
            fish_parent = Layer.all_objects.create(**parent_layer_dict)

        ##############################################
        # VALIDATE USAGE
        ##############################################
        if not len(args) == 0:
            print('Usage: manage.py mdat_2_fish (no arguments allowed)')
            sys.exit()

        ##############################################
        # PREPARE FOR IMPORT
        ##############################################
        # Site management: Prod vs Stage
        django_prod_site = Site.objects.get(pk=1)
        django_stage_site = Site.objects.get(pk=2)

        try:
            parent_theme = Theme.all_objects.get(name='conservation')
        except:
            print("Parent Theme 'conservation' not found. Please set parent_theme.")
            import ipdb; ipdb.set_trace()

        # Delete previously imported layers
        previous_imports = Layer.all_objects.filter(data_source=data_source,is_sublayer=True,data_publish_date=publish_date)
        print("Deleting %d previously imported MDAT V2.1 layers" % previous_imports.count())
        previous_imports.delete()

        # Get existing parent layer
        # fish_parent = Layer.all_objects.get(url='', name='Fish', layer_type='checkbox')

        # Update existing parent layer
        fish_parent_dict =  model_to_dict(fish_parent)
        fish_parent_dict['data_source'] = "%s (updated)" % data_source
        fish_parent_dict['source'] = source_site
        fish_parent_dict['metadata'] = source_metadata
        for key in ['pk','id','name','slug_name','attribute_fields','connect_companion_layers_to','lookup_table','site','sublayers','themes','bookmark']:
            try:
                del fish_parent_dict[key]
            except:
                pass

        ##############################################
        # GET OR CREATE NEW PARENT LAYERS (SPRING AND FALL)
        ##############################################
        # Make Fish - spring & fish - fall
        (new_fish_parent_spring, created) = Layer.all_objects.get_or_create(name='Fish - Spring 2010-2017')
        if created:
            for key in fish_parent_dict.keys():
                setattr(new_fish_parent_spring, key, fish_parent_dict[key])
        else:
            for key in ['metadata', 'data_source', 'source']:
                setattr(new_fish_parent_spring, key, fish_parent_dict[key])
        new_fish_parent_spring.site.add(django_stage_site)
        new_fish_parent_spring.themes.add(parent_theme)
        new_fish_parent_spring.save(recache=False)

        (new_fish_parent_fall, created) = Layer.all_objects.get_or_create(name='Fish - Fall 2010-2016')
        if created:
            for key in fish_parent_dict.keys():
                setattr(new_fish_parent_fall, key, fish_parent_dict[key])
        else:
            for key in ['metadata', 'data_source', 'source']:
                setattr(new_fish_parent_fall, key, fish_parent_dict[key])
        new_fish_parent_fall.site.add(django_stage_site)
        new_fish_parent_fall.themes.add(parent_theme)
        new_fish_parent_fall.save(recache=False)


        ##############################################
        # MAP OUT IMPORT PATTERNS
        ##############################################
        service_value_lookup = {
            'fish': {
                'url': {
                    # 'v1': '%s%s/MapServer' % (mdat_prod_base, fish_v1_service),
                    # 'staging': '%s%s/MapServer' % (mdat_stage_base, fish_v2_service),
                    'prod': '%s%s/MapServer' % (mdat_base, fish_service),
                },
                'parent_layer': {
                    # 'staging': fish_stage_parent,
                    'prod': fish_parent
                },
                'exclude_words': [
                    'diversity',
                    'northeast',
                    ' - atlantic scale'
                ]
            },
        }

        all_layer_dict = {
            'data_publish_date': publish_date,
            'data_source': data_source,
            'source': source_site,
            'layer_type': 'ArcRest',
            'is_sublayer': True,
        }
        parent_layer_map = {
            'All': 'All Fish Species',
            'Diadromous': 'Diadromous Fish',
            'Forage': 'Forage Fish',
            'Demersal': 'Demersal Fish',
            'NEFMC multispecies': 'NEFMC multispecies',
            'NEFMC small mesh multispecies': 'NEFMC small mesh multispecies',
            'NEFMC Skates': 'NEFMC Skates',
            'MAFMC FMPs': 'MAFMC FMPs',
            'ASMFC FMPs': 'ASMFC FMPs',
            'EFH Species': 'EFH Species',
            'Highly Migratory Species': 'Highly Migratory Species',
            'Abundance Vulnerable to Climate Changes': 'Abundance Vulnerable to Climate Changes',
            'Distribution Vulnerable to Climate Changes': 'Distribution Vulnerable to Climate Changes',
        }
        topic_layer_map = {
            'Biomass': 'Biomass',
            'Species Richness': 'Species Richness',
            'Shannon Diversity': None,
            'Simpson Diversity': None,
            'Core Biomass Area - Northeast scale': None,
            'Core Biomass Area - Mid-Atlantic scale': 'Core Biomass Area - Mid-Atlantic scale',
            'Core Biomass Area - Northeast Shelf scale': None,

        }

        for service in services:    # For the fish import, this is just 'fish'
            layer_name_lookup = {}
            for parent_mapping in parent_layer_map.keys():
                for topic_mapping in topic_layer_map.keys():
                    if topic_layer_map[topic_mapping]:
                        layer_name_lookup['%s, %s' % (parent_mapping, topic_mapping)] = "%s: %s" % (parent_layer_map[parent_mapping], topic_layer_map[topic_mapping])
            for server in ['prod']:
                all_service_dict = {
                    'url': "%s/export" % service_value_lookup[service]['url'][server],
                    'metadata': service_value_lookup[service]['parent_layer'][server].metadata
                }
                all_service_dict.update(all_layer_dict)

                # Get Layer info from staging
                print("Getting V2.1 layers for %s on %s server" % (service, server))
                v2_json_url = '%s/?f=pjson' % (service_value_lookup[service]['url'][server])
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
                        # break new layer name by comma and grab 1st 2 to make layer_name_lookup id.
                        try:
                            layer_name_parts = layer['name'].split(',')
                            parent_value = layer_name_parts[0].strip(' ')
                            topic_value = layer_name_parts[1].strip(' ')
                            time_value = layer_name_parts[2].strip(' ')
                            if topic_value in topic_layer_map.keys() and topic_layer_map[topic_value]:
                                existing_layer_name = "%s: %s" % (parent_layer_map[parent_value], topic_layer_map[topic_value])
                                new_layer = Layer.all_objects.get(name__iexact=existing_layer_name, data_source=old_data_source, sublayers=fish_parent)
                        except Exception as e:
                            pass
                        if time_value:
                            if time_value.lower() == 'Spring 2010-2017'.lower():
                                parent = new_fish_parent_spring
                                name_suffix = " (spring)"
                            else:
                                parent = new_fish_parent_fall
                                name_suffix = " (fall)"
                        else:
                            import ipdb; ipdb.set_trace()

                        # import ipdb; ipdb.set_trace()
                        # exit()

                        if not new_layer:
                            if existing_layer_name:
                                new_layer_name = "%s%s" % (existing_layer_name, name_suffix)
                            else:
                                new_layer_name = "%s%s" % (layer['name'], name_suffix)
                            new_layer_dict = {
                              'layer_type': all_layer_dict['layer_type'],
                              'data_publish_date': all_layer_dict['data_publish_date'],
                              # 'site': [django_stage_site.pk],
                              # 'themes': [parent_theme.pk],
                              'is_sublayer': True,
                              'source': all_layer_dict['source'],
                              'metadata': all_service_dict['metadata'],
                              'description': u'We are currently updating this layer. Please come back later for a full description of this layer.',
                              'data_overview': u'We are currently updating this layer. Please come back later for a full overview of this layer.',
                              # 'slug_name': u'all-fish-species-biomass-v2-prod-1295',
                              'data_source': all_layer_dict['data_source'],
                              'name': new_layer_name,
                              'url': all_service_dict['url'],
                              'arcgis_layers': layer['id'],
                              'order': layer['id'],
                              'sublayers': [parent.pk],
                              'espis_region': u'Mid Atlantic',
                            }
                            new_layer = Layer.all_objects.create(**new_layer_dict)
                            new_layer.site.add(django_stage_site)
                            new_layer.site.add(django_prod_site)
                            new_layer.themes.add(parent_theme.pk)
                            new_layer.sublayers.add(parent.pk)
                            new_layer.save(recache=False)
                            new_layer.save(recache=False,slug_name="%s-v2.1-%s" % (new_layer.slug,server))

                        else:
                            # Create new spring/fall layers from existing layer
                            new_layer_dict = model_to_dict(new_layer)
                            new_layer_dict['name'] = "%s%s" % (new_layer_dict['name'], name_suffix)
                            new_layer_dict['data_publish_date'] = all_layer_dict['data_publish_date']
                            for attr in ['site','id','themes','connect_companion_layers_to','lookup_table','attribute_fields','slug_name','sublayers']:
                                new_layer_dict.pop(attr)
                            new_layer_dict['source']= all_layer_dict['source']
                            new_layer_dict['data_source'] = all_layer_dict['data_source']
                            new_layer_dict['arcgis_layers'] = layer['id']
                            new_layer_dict['order'] = layer['id']
                            for key in ['metadata', 'url']:
                                new_layer_dict[key] = all_service_dict[key]
                            new_layer = Layer.all_objects.create(**new_layer_dict)
                            new_layer.site.add(django_stage_site)
                            new_layer.site.add(django_prod_site)
                            new_layer.themes.add(parent_theme.pk)
                            new_layer.sublayers.add(parent.pk)
                            new_layer.save(recache=False,slug_name="%s-v2.1-%s" % (new_layer.slug,server))
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
