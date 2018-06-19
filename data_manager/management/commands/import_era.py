from django.core.management.base import BaseCommand
import sys

import requests

# Ignore the nasty SNIMissingWarning and the InsecurePlatformWarning
import urllib3
urllib3.disable_warnings()

# Identify and break up name and dimension/value dict
# Only deal with strings, finding and creating dimensions/associations done elsewhere
def parseLayerName(sublayer_name):
    name_lookup = {
        'allSp': 'all species',
        'nefsc': '(NEFSC)',
        'neamap': '(NEAMAP)',
        'chla': 'Chlorophyll-a',
    }
    value_lookup = {
        # TODO: determine if annual is dimension 'month' or 'season'
        'annual': {
            'dimension_type': 'time',
            'dimension': 'time',
            'dimension_label': 'month',
            'value': 'annual',
            'name': 'annual',
            'label': 'Yr',
            'order': 1
        },
        'month01': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '01',
              'name': 'january',
              'label': 'J',
              'order': 2
        },
        'month02': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '02',
              'name': 'february',
              'label': 'F',
              'order': 3
        },
        'month03': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '03',
              'name': 'march',
              'label': 'M',
              'order': 4
        },
        'month04': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '04',
              'name': 'april',
              'label': 'A',
              'order': 5
        },
        'month05': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '05',
              'name': 'may',
              'label': 'M',
              'order': 6
        },
        'month06': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '06',
              'name': 'june',
              'label': 'J',
              'order': 7
        },
        'month07': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '07',
              'name': 'july',
              'label': 'J',
              'order': 8
        },
        'month08': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '08',
              'name': 'august',
              'label': 'A',
              'order': 9
        },
        'month09': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '09',
              'name': 'september',
              'label': 'S',
              'order': 10
        },
        'month10': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '10',
              'name': 'october',
              'label': 'O',
              'order': 11
        },
        'month11': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '11',
              'name': 'november',
              'label': 'N',
              'order': 12
        },
        'month12': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'month',
              'value': '12',
              'name': 'december',
              'label': 'D',
              'order': 13
        },
        'season01': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'season',
              'value': '01',
              'name': 'winter',
              'label': "Win",
              'order': 2
        },
        'season02': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'season',
              'value': '02',
              'name': 'spring',
              'label': 'Spr',
              'order': 3
        },
        'season03': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'season',
              'value': '03',
              'name': 'summer',
              'label': 'Sum',
              'order': 4
        },
        'season04': {
              'dimension_type': 'time',
              'dimension': 'time',
              'dimension_label': 'season',
              'value': '04',
              'name': 'fall',
              'label': 'Fall',
              'order': 5
        },
        'original': {
              'dimension_type': 'threshold',
              'dimension': 'threshold',
              'dimension_label': 'threshold',
              'value': 'original',
              'name': 'all',
              'label': 'All',
              'order': 1
        },
        'top50pctl': {
              'dimension_type': 'threshold',
              'dimension': 'threshold',
              'dimension_label': 'threshold',
              'value': '50',
              'name': '50',
              'label': 'Top&nbsp50%',
              'order': 2
        },
        'top25pctl': {
              'dimension_type': 'threshold',
              'dimension': 'threshold',
              'dimension_label': 'threshold',
              'value': '25',
              'name': '25',
              'label': 'Top&nbsp25%',
              'order': 3
        },
        'top10pctl': {
              'dimension_type': 'threshold',
              'dimension': 'threshold',
              'dimension_label': 'threshold',
              'value': '10',
              'name': '10',
              'label': 'Top&nbsp10%',
              'order': 4
        },
    }

    # Parse Name
    name_parts = sublayer_name.split('_')
    name_parts_clean = []
    dimensions_dict = {}
    for part in name_parts:
        if part in name_lookup.keys():
            name_parts_clean.append(name_lookup[part])
        else:
            name_parts_clean.append(part)
        if part in value_lookup.keys():
            val_dict = value_lookup[part]
            dimensions_dict[val_dict['dimension_type']] = val_dict
    name = ' '.join([x.capitalize() for x in name_parts_clean])

    return {
        'name':name,
        'dimensions': dimensions_dict
    }

def createArcRestLayer(layer, url, layer_id, layer_source, theme, parent_layer=False):
    from django.contrib.sites.models import Site
    from data_manager.models import Layer, Theme

    parsed_layer_dict = parseLayerName(layer['name'])
    layer_name = parsed_layer_dict['name']
    is_sublayer = not(parent_layer == False)
    url_record_matches = Layer.objects.filter(url=url, arcgis_layers=str(layer_id), is_sublayer=is_sublayer, layer_type='ArcRest')
    if len(url_record_matches) == 1:
        layer_record = url_record_matches[0]
        layer_created = False
    else:
        (layer_record, layer_created) = Layer.objects.get_or_create(
            name=layer_name,
            layer_type='ArcRest',
            url=url,
            is_sublayer=is_sublayer,
            arcgis_layers=str(layer_id)
        )
    if not theme in layer_record.themes.all():
        layer_record.themes.add(theme)
    if is_sublayer and not parent_layer in layer_record.sublayers.all():
        layer_record.sublayers.add(parent_layer)
    if not layer_record.data_source == layer_source:
        layer_record.data_source = layer_source
    if layer_created:
        # Adds all sites to every layer record - we may want to limit this on Production
        for site in Site.objects.all():
            layer_record.site.add(site)
    layer_record.save()
    return {
        'layer_record': layer_record,
        'layer_record_name_dict': parsed_layer_dict
    }

def setAssociation(parent, dimensionValues, layer):
    from data_manager.models import Layer, Theme, MultilayerDimension, MultilayerAssociation, MultilayerDimensionValue

    # get list of associations for each dimension value
    association_list = []
    for i, value in enumerate(dimensionValues):
        # identify single association in all lists
        if i == 0:
            association_list = list(value.associations.all())
            # # TODO: TEST:
            # if not len(association_list) == len(parent.parent_layer.all()):
            #     import ipdb; ipdb.set_trace()
        else:
            new_association_list = []
            for association in association_list:
                if association in list(value.associations.all()):
                    new_association_list.append(association)
            association_list = new_association_list
    if len(association_list)> 1:
        import ipdb; ipdb.set_trace()
        sys.exit()
    elif len(association_list) == 1:
        association = association_list[0]
        # create name for association from name of each dimension value (join(' '))
        association.name = ' '.join([x.value.capitalize() for x in dimensionValues])
        # Assign layer to association
        association.layer = layer
        association.save()

class Command(BaseCommand):
    help = "Import ERA Data from Duke and create necessary slider records"

    def handle(self, *args, **options):
        if not len(args) == 0:
            print('Usage: manage.py import_era (no arguments allowed)')
            sys.exit()

        import json, requests
        from data_manager.models import Layer, Theme, MultilayerDimension, MultilayerAssociation, MultilayerDimensionValue
        from django.contrib.sites.models import Site

        ############
        # SETTINGS #
        ############
        LAYER_SOURCE = 'MDAT ERA IMPORT'
        ERA_CATEGORY_DISPLAY_NAME = 'Components of Ecological Richness'
        ENDPOINT = 'https://mgelmaps.env.duke.edu/mdat_new/rest/services/'
        SERVICE_ROOT = 'MDAT_Staging'
        SERVICE_PREFIX = 'CEI_ERA_'
        ERA_CATEGORIES = {
            'Abundance': {
                'name': 'Abundance',
                'order': 3,
                'type': 'checkbox'
            },
            'Biodiversity': {
                'name': 'Biodiversity',
                'order': 2,
                'type': 'radio'
            },
            'Habitat_Oceanographic': {
                'name': 'Habitat and Oceanographic Drivers',
                'order': 6,
                'type': 'radio'
            },
            'Productivity': {
                'name': 'Productivity',
                'order': 1,
                'type': 'checkbox'
            },
            'Rarity': {
                'name': 'Rarity',
                'order': 5,
                'type': 'radio'
            },
            'Vulnerability': {
                'name': 'Vulnerability',
                'order': 4,
                'type': 'radio'
            },
        }
        DIMENSION_SETTINGS = {
            'time': {
                'order': 1,
                'animated': True
            },
            'threshold': {
                'order': 2,
                'animated': False
            },
            'default': {
                'order': 10,
                'animated': False
            }
        }
        #############
        #############

        count = 0

        # Get companion theme (used to hide multilayer sublayers)
        companion_theme = Theme.objects.get(name='companion')

        # Ensure ERA Theme Exists
        (era_theme, theme_created) = Theme.objects.get_or_create(name='ERA', display_name=ERA_CATEGORY_DISPLAY_NAME)
        if theme_created:
            for site in Site.objects.all():
                era_theme.site.add(site)
        era_theme.save()

        service_categories = ['%s/%s%s' % (SERVICE_ROOT,SERVICE_PREFIX, x) for x in ERA_CATEGORIES.keys()]
        services_json = '%s%s/?f=pjson' % (ENDPOINT,SERVICE_ROOT)
        services_request = requests.get(services_json)
        services = services_request.json()['services']
        for service_count, service_dict in enumerate(services):
            service = service_dict['name']
            service_endpoint = '%s%s/MapServer' % (ENDPOINT, service)
            # test if service matches given ERA_CATEGORIES
            service_key_list = service.split('%s/%s' % (SERVICE_ROOT,SERVICE_PREFIX))
            if service in service_categories and len(service_key_list) == 2:
                service_key = service_key_list[1]
                category_dict = ERA_CATEGORIES[service_key]
                (category_layer, category_layer_created) = Layer.objects.get_or_create(
                    name=category_dict['name'],
                    order=category_dict['order'],
                    layer_type=category_dict['type']
                )
                category_layer.themes.add(era_theme)
                category_layer.data_source = LAYER_SOURCE
                if len(category_layer.site.all()) == 0:
                    for site in Site.objects.all():
                        category_layer.site.add(site)
                category_layer.save()

                service_json = '%s?f=pjson' % (service_endpoint)
                layers_request = requests.get(service_json)
                layers = layers_request.json()['layers']
                for layer_count, layer in enumerate(layers):
                    if layer['parentLayerId'] == -1:
                        # Parent Layer
                        if layer['subLayerIds'] == 0:
                            # Standalone Layer
                            url = '%s/export' % service_endpoint
                            createArcRestLayer(layer, url, layer['id'], LAYER_SOURCE, era_theme, category_layer)
                        else:
                            # ERA Category MultiLayer Parent
                            parsed_layer_dict = parseLayerName(layer['name'])
                            (multilayer_parent, multilayer_parent_created) = Layer.objects.get_or_create(
                                name=parsed_layer_dict['name'],
                                layer_type='Vector',
                                is_sublayer=True
                            )
                            multilayer_parent.themes.add(era_theme)
                            multilayer_parent.sublayers.add(category_layer)
                            if multilayer_parent_created or len(multilayer_parent.site.all()) == 0:
                                for site in Site.objects.all():
                                    multilayer_parent.site.add(site)
                            multilayer_parent.data_source = LAYER_SOURCE
                            multilayer_parent.save()
                            count += 1
                            print('Service: %d, Layer: %d, Total: %d' % (service_count, layer_count, count))
                            if layer['subLayerIds']:
                                for sublayer_count, sublayer_id in enumerate(layer['subLayerIds']):
                                    sublayer_json = '%s/%s/?f=pjson' % (service_endpoint, sublayer_id)
                                    sublayer_request = requests.get(sublayer_json)
                                    sublayer = sublayer_request.json()
                                    sublayer_url = '%s/export' % service_endpoint
                                    sublayer_record_dict = createArcRestLayer(sublayer, sublayer_url, sublayer['id'], LAYER_SOURCE, companion_theme, False)
                                    sublayer_record = sublayer_record_dict['layer_record']
                                    parsed_layer_dict = sublayer_record_dict['layer_record_name_dict']
                                    sublayerDimensionValues = []
                                    for dimension_value_dict_key in parsed_layer_dict['dimensions'].keys():
                                        if dimension_value_dict_key in DIMENSION_SETTINGS.keys():
                                            dimension_settings_dict = DIMENSION_SETTINGS[dimension_value_dict_key]
                                        else:
                                            dimension_settings_dict = DIMENSION_SETTINGS['default']

                                        dimension_value_dict = parsed_layer_dict['dimensions'][dimension_value_dict_key]
                                        (dimension, dimension_created) = MultilayerDimension.objects.get_or_create(
                                            name=dimension_value_dict['dimension'].capitalize(),
                                            label=dimension_value_dict['dimension'].capitalize(),
                                            layer=multilayer_parent,
                                            order=dimension_settings_dict['order'],
                                            animated=dimension_settings_dict['animated']
                                        )
                                        if dimension_created:
                                            # Save some time
                                            dimension.save()
                                        # Fix issue of old associations being duplicated
                                        # matching_dimension_values = MultilayerDimensionValue.objects.filter(dimension=dimension,value=dimension_value_dict['name'],order=dimension_value_dict['order'])
                                        matching_dimension_values = dimension.multilayerdimensionvalue_set.filter(value=dimension_value_dict['name'],order=dimension_value_dict['order'])
                                        cleanup_count = 0
                                        while len(matching_dimension_values) > 1:
                                            cleanup_count += 1
                                            #weird bug where many have no id yet
                                            matching_dimension_values[1].save()
                                            matching_dimension_values[1].delete()
                                            matching_dimension_values = dimension.multilayerdimensionvalue_set.filter(value=dimension_value_dict['name'],order=dimension_value_dict['order'])
                                            print('cleanup values count: %s' % cleanup_count)
                                        (dimensionValue, dimension_value_created) = MultilayerDimensionValue.objects.get_or_create(
                                            dimension=dimension,
                                            value=dimension_value_dict['name'],
                                            order=dimension_value_dict['order']
                                        )
                                        dimensionValue.label = dimension_value_dict['label']  # Capitalizing this creates dupes if not matching 'label' in value_lookup
                                        dimensionValue.save()
                                        sublayerDimensionValues.append(dimensionValue)
                                    # Create Association
                                    setAssociation(multilayer_parent, sublayerDimensionValues, sublayer_record)
                                    # set cache
                                    sublayer_record.data_source = LAYER_SOURCE
                                    sublayer_record.save()
                                    count += 1
                                    print('Service: %d, Layer: %d, Sublayer: %d, Total: %d' % (service_count, layer_count, sublayer_count, count))
                            multilayer_parent.save()
                            for site in Site.objects.all():
                                multilayer_parent.toDict(site.pk)
                    else:
                        # Child Layer
                        pass        # Handle this in loop of parent layer
                    # set Cache


# https://mgelmaps.env.duke.edu/mdat_new/rest/services/MDAT_Staging/CEI_ERA_Abundance/MapServer/19/export?LAYERS=show%3A0&SRS=EPSG%3A3857&TRANSPARENT=true&FORMAT=png&BBOX=-9079495.966562%2C4383204.949375%2C-8766409.89875%2C4696291.017188&SIZE=256%2C256&F=image&BBOXSR=3857&IMAGESR=3857
# https://mgelmaps.env.duke.edu/mdat_new/rest/services/MDAT_Staging/CEI_ERA_Abundance/MapServer/export?LAYERS=show%3A12&SRS=EPSG%3A3857&TRANSPARENT=true&FORMAT=png&BBOX=-7827151.695312%2C4539747.983281%2C-7670608.661406%2C4696291.017188&SIZE=256%2C256&F=image&BBOXSR=3857&IMAGESR=3857
