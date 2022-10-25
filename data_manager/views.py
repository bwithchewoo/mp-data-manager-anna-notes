# Create your views here.

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from .models import *
from .serializers import BriefLayerSerializer
from rest_framework import viewsets

import json, requests

class LayerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A simple ViewSet for layers.
    """
    queryset = Layer.all_objects.all()
    serializer_class = BriefLayerSerializer

def get_themes(request):
    data = {
        "themes": [theme.getInitDict() for theme in Theme.objects.all().order_by('order')],
    }
    return JsonResponse(data)

def get_layer_search_data(request):
    search_dict = {}
    for theme in Theme.all_objects.filter(visible=True):
        for layer in theme.layer_set.all():
            if not layer.is_sublayer:
                search_dict[layer.name] = {
                    'layer': {
                        'id': layer.id,
                        'name': layer.name,
                        'has_sublayers': layer.sublayers.all().count() > 0,
                        'sublayers': [{'name': x.name, 'id': x.id} for x in layer.sublayers.filter(is_sublayer=True).order_by('order')]
                    },
                    'theme': {
                        'id': theme.id,
                        'name': theme.display_name,
                        'description': theme.description
                    }
                }
    return JsonResponse(search_dict)

def get_json(request):
    from django.core.cache import cache
    from django.contrib.sites import shortcuts
    if request.META['HTTP_HOST'] in ['localhost:8000', 'portal.midatlanticocean.org', 'midatlantic.webfactional.com']:
        current_site_pk = 1
    else:
        current_site_pk = shortcuts.get_current_site(request).pk
    data = cache.get('data_manager_json_site_%d' % current_site_pk)
    if not data:
        data = {
            "state": { "activeLayers": [] },
            "layers": [layer.dictCache(current_site_pk) for layer in Layer.all_objects.filter(is_sublayer=False).exclude(layer_type='placeholder').order_by('order')],
            "themes": [theme.dictCache(current_site_pk) for theme in Theme.all_objects.all().order_by('order')],
            "success": True
        }
        # Cache for 1 week, will be reset if layer data changes
        cache.set('data_manager_json_site_%d' % current_site_pk, data, 60*60*24*7)
    return JsonResponse(data)

def get_layers_for_theme(request, themeID):
    theme = Theme.objects.get(pk=themeID)
    layer_list = []
    for layer in theme.layer_set.filter(is_sublayer=False).exclude(layer_type='placeholder').order_by('order','name'):
        layer_list.append({
            'id': layer.id,
            'name': layer.name,
            'type': layer.layer_type,
            'has_sublayers': len(layer.sublayers.all()) > 0,
            'subLayers': [{'id': x.id, 'name': x.name, 'slug_name': x.slug_name} for x in layer.sublayers.order_by('order','name')],
        })
    return JsonResponse({'layers': layer_list})

def get_layer_details(request, layerID):
    try:
        layer = Layer.all_objects.get(pk=layerID)
        return JsonResponse(layer.toDict)
    except ObjectDoesNotExist as e:
        return JsonResponse({'error': "Layers with ID %s does not exist." % layerID})

def get_layer_catalog_content(request, layerID):
    layer = Layer.all_objects.get(pk=layerID)
    return JsonResponse({'html': layer.catalog_html})

def create_layer(request):
    if request.POST:
        try:
            url, name, type, themes = get_layer_components(request.POST)
            layer = Layer(
                url = url,
                name = name,
                layer_type = type
            )
            layer.save()

            for theme_id in themes:
                theme = Theme.all_objects.get(id=theme_id)
                layer.themes.add(theme)
            layer.save()

        except Exception as e:
            return HttpResponse(e.message, status=500)

        result = layer_result(layer, message="Saved Successfully")
        return JsonResponse(result)


def update_layer(request, layer_id):
    if request.POST:
        layer = get_object_or_404(Layer, id=layer_id)

        try:
            url, name, type, themes = get_layer_components(request.POST)
            layer.url = url
            layer.name = name
            layer.save()

            for theme in layer.themes.all():
                layer.themes.remove(theme)
            for theme_id in themes:
                theme = Theme.all_objects.get(id=theme_id)
                layer.themes.add(theme)
            layer.save()

        except Exception as e:
            return HttpResponse(e.message, status=500)

        result = layer_result(layer, message="Edited Successfully")


        return JsonResponse(result)
def get_layer_components(request_dict, url='', name='', type='XYZ', themes=[]):
    if 'url' in request_dict:
        url = request_dict['url']
    if 'name' in request_dict:
        name = request_dict['name']
    if 'type' in request_dict:
        type = request_dict['type']
    if 'themes' in request_dict:
        themes = request_dict.getlist('themes')
    return url, name, type, themes


def layer_result(layer, status_code=1, success=True, message="Success"):
    from django.contrib.sites import shortcuts
    current_site = shortcuts.get_current_site(request)
    result = {
        "status_code":status_code,
        "success":success,
        "message":message,
        "layer": layer.toDict(current_site.pk),
        "themes": [theme.id for theme in layer.themes.all()]
    }
    return result

def recurse_layers(sublayer, current_layer_dict, layers):
    if sublayer.find('Name') is not None:
        layers[sublayer.find('Name').text] = current_layer_dict
    if len(sublayer.findall('Layer')) > 0:
        for sub_sublayer in sublayer.findall('Layer'):
            layers = recurse_layers(sub_sublayer, current_layer_dict, layers)
    return layers

def wms_get_capabilities(url):
    from datetime import datetime
    from owslib.wms import WebMapService

    if url[-1] == '?':
      url = url[0:-1]

    wms = WebMapService(url)
    layers = {}
    for layer in list(wms.contents): #TODO: create dict
        layers[layer] = {'dimensions':{}}
    styles = {}
    srs_opts = {}
    queryable = []
    times = {}
    import xml.etree.ElementTree as ET
    root = ET.fromstring(wms.getServiceXML())
    # get time dimensions from XML directly, in case OWSLIB fails to set it appropriately
    try:
        layer_group = root.find('Capability').findall('Layer')[0]
        current_layer = {
            'dimensions': {}
        }
        for layer in layer_group.findall('Layer'):
            if len(layer.findall('Dimension')) > 0:
                for dimension in layer.findall('Dimension'):
                    if dimension.get('name'):
                        current_layer['dimensions'][dimension.get('name')] = None
            if len(layer.findall('Extent')) > 0:
                for extent in layer.findall('Extent'):
                    if extent.get('name'):
                        current_layer['dimensions'][extent.get('name')] = {}
                        for key in extent.keys():
                            current_layer['dimensions'][extent.get('name')][key] = extent.get(key)
                        try:
                            positions = extent.text.split(',')
                            if len(positions) > 4:
                                current_layer['dimensions'][extent.get('name')]['positions'] = positions[0:2] + ['...'] + positions[-3:-1]
                            else:
                                current_layer['dimensions'][extent.get('name')]['positions'] = positions
                        except:
                            pass
                new_layer_dict = recurse_layers(layer, current_layer, {})
                for key in layers.keys():
                    if key in new_layer_dict.keys():
                        layers[key] = new_layer_dict[key]

        available_formats = []
        if root.find('Capability') and root.find('Capability').find('Request'):
            getFeatureInfo = root.find('Capability').find('Request').find('GetFeatureInfo')
            if getFeatureInfo:
                accepted_formats = [
                    'text/plain',
                    'text/html',
                    'text/xml',
                    'image/png',
                    'application/json',
                    'text/javascript',  #JSONP
                    'application/vnd.ogc.gml',
                ]
                for format_type in getFeatureInfo.findall('Format'):
                    if format_type.text in accepted_formats:
                        available_formats.append(format_type.text)


    except:
        # trouble parsing raw xml
        print('trouble parsing raw xml')
        pass

    for layer in layers.keys():
        styles[layer] = wms[layer].styles
        srs_opts[layer] = wms[layer].crsOptions
        try:
            if bool(wms[layer].queryable):
                queryable.append(layer)
        except Exception as e:
            print(e)
            pass

        dimensions = layers[layer]['dimensions']
        timefield = None
        if len(dimensions.keys()) == 1:
            timefield = dimensions.keys()[0]
        else:
            # there is no explicit way to know what time field is. This makes educated guesses.
            for dimension in dimensions.keys():
                if 'time' in dimension.lower():
                    timefield = dimension
                    break

        if timefield:
            layer_obj = layers[layer]['dimensions'][timefield]
        else:
            layer_obj = {}

        if wms[layer].timepositions:
            positions = wms[layer].timepositions
        elif 'positions' in layer_obj.keys():
            positions = layer_obj['positions']
        else:
            positions = None
        if wms[layer].defaulttimeposition:
            defaulttimeposition = wms[layer].defaulttimeposition
        elif 'default' in layer_obj.keys():
            defaulttimeposition = layer_obj['default']
        else:
            defaulttimeposition = None


        times[layer] = {
            'positions': positions,
            'default': defaulttimeposition,
            'field': timefield
        }

    capabilities = {}
    if available_formats and len(available_formats) > 0:
        capabilities['featureInfo'] = {
            'available': True,
            'formats': available_formats
        }

    result = {
        'layers': list(layers.keys()),
        'formats': wms.getOperationByName('GetMap').formatOptions,
        'version': wms.version,
        'styles':  styles,
        'srs': srs_opts,
        'queryable': queryable,
        'time': times,
        'capabilities': capabilities,
    }

    return result

def wms_request_capabilities(request):
    from requests.exceptions import SSLError

    url = request.GET.get('url')
    try:
        result = wms_get_capabilities(url)
    except SSLError as e:
        # Sometimes SSL certs aren't right - if we trust the user hitting this endpoint,
        #       Then we should be safe trying to get the data w/o HTTPS.
        if request.user.is_staff and 'https://' in url.lower():
            result = wms_get_capabilities(url.lower().replace('https://','http://'))
        else:
            # leave the error alone until we have a better solution
            result = wms_get_capabilities(url)

    return JsonResponse(result)

def get_catalog_records(request):
    data = {}
    if settings.CATALOG_TECHNOLOGY == "GeoPortal2":
        from elasticsearch import Elasticsearch
        from elasticsearch_dsl import Search
        es = Elasticsearch()
        index = settings.ELASTICSEARCH_INDEX
        url = settings.CATALOG_SOURCE
        if url:
            es = es = Elasticsearch(url)
        else:
            es = es = Elasticsearch()

        search = Search(using=es, index=index).query("match", sys_approval_status_s="approved")

        search_fields = settings.ELASTICSEARCH_SEARCH_FIELDS

        records = search.source(search_fields)

        records_dict = {}
        # record_ids = []
        record_names = []
        record_name_lookup = {}

        for record in records.scan():
            # record_ids.append(record.meta.id)
            record_dict = {}
            for index, field in enumerate(['id'] + search_fields):
                if index == 0:
                    record_dict['id'] = record.meta.id
                else:
                    if field == settings.DATA_CATALOG_NAME_FIELD:
                        if not record[field] in record_name_lookup.keys():
                            record_name_lookup[record[field]] = []
                        record_name_lookup[record[field]].append(record.meta.id)
                    record_dict[field] = record[field]
            records_dict[record.meta.id] = record_dict

        # data['ids'] = record_ids
        data['records'] = records_dict
        data['record_name_lookup'] = record_name_lookup
        data['ELASTICSEARCH_INDEX'] = settings.ELASTICSEARCH_INDEX
        data['CATALOG_TECHNOLOGY'] = settings.CATALOG_TECHNOLOGY
        # data['hits'] = len(record_ids)

    return JsonResponse(data)


######################################################
#           MIGRATION API/Logic                      #
######################################################

def layer_status(request):
    data = {
        'themes': {},
        'layers': {}    
    }

    for theme in Theme.all_objects.all().order_by('order', 'name', 'uuid'):
        theme_dict = theme.dictCache(site_id=request.site.id)
        if theme_dict == None:
            for site in Site.objects.all():
                theme_dict = theme.dictCache(site_id=site.id)
                if not theme_dict == None:
                    continue
            
        data['themes'][str(theme.uuid)] = {
            'name': theme.name,
            'uuid': theme.uuid,
            'date_modified': theme.date_modified,
            'layers': []
        }
        if theme_dict:
            for layer_id in theme_dict['layers']:
                try:
                    layer = Layer.all_objects.get(pk=layer_id)
                except Exception as e:
                    print('This is the result of shared caches between projects and should not appear during production.')
                    pass
                layer_data = {
                    'uuid': str(layer.uuid), 
                    'name': layer.name,
                    'date_modified': layer.date_modified,
                    'sublayers': []
                }
                for sublayer in layer.sublayers.all().order_by('order', 'name'):
                    layer_data['sublayers'].append({
                        'uuid': str(sublayer.uuid),
                        'name': sublayer.name,
                        'date_modified': sublayer.date_modified
                    })
                
                data['themes'][str(theme.uuid)]['layers'].append(layer_data)

    for layer in Layer.all_objects.all().order_by('uuid'):
        data['layers'][str(layer.uuid)] = {
            'name': layer.name,
            'date_modified': layer.date_modified
        }
    return JsonResponse(data)

def compare_remote_layers(remote_layer_dict):
    from datetime import datetime
    comparison_dict = {
        'themes': {},
        'layers': {}
    }
    # Populate Dict with lists of Themes and Layers
    # New field "source" for 'local', 'remote', or 'match'
    # New field "modified": Null, True, or False  (Null if not a 'match' entry)
    # New field "newer": Null, 'Local', or 'Remote' (Null if not a 'match' entry)
    for remote_theme_key in remote_layer_dict['themes'].keys():
        theme = remote_layer_dict['themes'][remote_theme_key]
        comparison_dict['themes'][remote_theme_key] = {
            'id': remote_theme_key,
            'source': 'remote',
            'modified': False,
            'remote_name': theme['name'],
            'remote_modified': datetime.strptime("{}+0000".format(theme['date_modified']), '%Y-%m-%dT%H:%M:%S.%fZ%z'),
            'local_name': None,
            'local_pk': None,
            'local_modified': None,
            'newest': None,
        }
    for theme in Theme.all_objects.all():
        key = str(theme.uuid)
        if not key in comparison_dict['themes'].keys():
            comparison_dict['themes'][key] = {
                'id': key,
                'source': 'local',
                'modified': False,
                'remote_name': None,
                'remote_modified': None,
                'newest': None,
            } 
        else:
            comparison_dict['themes'][key]['source'] = 'match'

        comparison_entry = comparison_dict['themes'][key]

        comparison_entry['local_name'] = theme.name
        comparison_entry['local_pk'] = theme.pk
        comparison_entry['local_modified'] = theme.date_modified

        if comparison_entry['source'] == 'match':
            if not comparison_entry['local_name'] == comparison_entry['remote_name']:
                comparison_entry['modified'] = True
            if not comparison_entry['local_modified'] == comparison_entry['remote_modified']:
                comparison_entry['modified'] = True
                if comparison_entry['local_modified'] > comparison_entry['remote_modified']:
                    comparison_entry['newest'] = 'local'
                elif comparison_entry['local_modified'] < comparison_entry['remote_modified']:
                    comparison_entry['newest'] = 'remote'

    for remote_layer_key in remote_layer_dict['layers'].keys():
        layer = remote_layer_dict['layers'][remote_layer_key]
        comparison_dict['layers'][remote_layer_key] = {
            'id': remote_layer_key,
            'source': 'remote',
            'modified': False,
            'remote_name': layer['name'],
            'remote_modified': datetime.strptime("{}+0000".format(layer['date_modified']), '%Y-%m-%dT%H:%M:%S.%fZ%z'),
            'local_name': None,
            'local_pk': None,
            'local_modified': None,
            'newest': None,
        }
    for layer in Layer.all_objects.all():
        key = str(layer.uuid)
        if not key in comparison_dict['layers'].keys():
            comparison_dict['layers'][key] = {
                'id': key,
                'source': 'local',
                'modified': False,
                'remote_name': None,
                'remote_modified': None,
                'newest': None,
            } 
        else:
            comparison_dict['layers'][key]['source'] = 'match'

        comparison_entry = comparison_dict['layers'][key]

        comparison_entry['local_name'] = layer.name
        comparison_entry['local_pk'] = layer.pk
        comparison_entry['local_modified'] = layer.date_modified

        if comparison_entry['source'] == 'match':
            if not comparison_entry['local_name'] == comparison_entry['remote_name']:
                comparison_entry['modified'] = True
            if not comparison_entry['local_modified'] == comparison_entry['remote_modified']:
                comparison_entry['modified'] = True
                if comparison_entry['local_modified'] > comparison_entry['remote_modified']:
                    comparison_entry['newest'] = 'local'
                elif comparison_entry['local_modified'] < comparison_entry['remote_modified']:
                    comparison_entry['newest'] = 'remote'

    
    return comparison_dict

def migration_layer_details(request, uuid=None):
    data = {
        'status': 'Unknown', 
        'message': 'Unknown',
        'themes': {},
        'layers': {},
    }
    if request.POST:
        try:
            layer_ids = request.POST.getlist('layers')
            for layer_key in layer_ids:
                layer = Layer.all_objects.get(uuid=layer_key)
                data['layers'][layer_key] = layer.toDict
            data['status'] = 'Success'
            data['message'] = 'layer(s) details retrieved'
            
        except Exception as e:
            data['status'] = 'Error'
            data['message'] = str(e)
            pass
    elif not uuid == None:
        try:
            layer = Layer.all_objects.get(uuid=uuid)
            data['layers'][uuid] = layer.toDict
            data['status'] = 'Success'
            data['message'] = 'layer details retrieved'
        except Exception as e:
            data['status'] = 'Error'
            data['message'] = str(e)
            pass

    return JsonResponse(data)

def migration_merge_layer(local_id, remote_dict, sites=[]):
    data = {
        'status': 'Unknown', 
        'message': 'Unknown',
        'local_id': local_id,
        'remote_name': remote_dict['name'],
        'uuid': remote_dict['uuid']
    }
    remote_dict.pop('id')
    if local_id:
        local_layer = Layer.objects.get(id=local_id)
    else:
        local_layer = Layer.objects.create(uuid=remote_dict['uuid'])

    #   Address 'sites'
    if not sites or len(sites) == 0 or sites == [None,]:
        sites = [x for x in Site.objects.all()]
    for site in sites:
        local_layer.site.add(site)

    #   Address 'sublayers'
    remote_dict.pop('subLayers')

    #   Address 'companion layers'
    remote_dict.pop('companion_layers')
    remote_dict.pop('has_companion')

    #   Address 'Themes'
    #       Weird: themes aren't included in a layer's 'dump' details. A bizarre omission!
    # remote_dict.pop('themes')

    #   Address 'parent'
    remote_dict.pop('parent')

    #   Address 'sliders'
    remote_dict.pop('is_multilayer')
    remote_dict.pop('is_multilayer_parent')
    remote_dict.pop('associated_multilayers')
    remote_dict.pop('dimensions')

    #   Address 'attribute info'
    remote_dict.pop('attributes')

    #   Address 'lookup info'
    remote_dict.pop('lookups')

    #   Sync dict keys with field names:
    remote_dict['layer_type'] = remote_dict.pop('type')
    remote_dict['search_query'] = remote_dict.pop('queryable')
    remote_dict['data_overview'] = remote_dict.pop('overview')
    remote_dict['data_download_link'] = remote_dict.pop('data_download')
    remote_dict['metadata_link'] = remote_dict.pop('metadata')
    remote_dict['source_link'] = remote_dict.pop('source')
    remote_dict['tiles_link'] = remote_dict.pop('tiles')
    remote_dict['vector_outline_color'] = remote_dict.pop('outline_color')
    remote_dict['vector_outline_opacity'] = remote_dict.pop('outline_opacity')
    remote_dict['vector_outline_width'] = remote_dict.pop('outline_width')
    remote_dict['vector_color'] = remote_dict.pop('color')
    remote_dict['vector_fill'] = remote_dict.pop('fill_opacity')
    remote_dict['vector_graphic'] = remote_dict.pop('graphic')
    remote_dict['vector_graphic_scale'] = remote_dict.pop('graphic_scale')
    remote_dict['is_annotated'] = remote_dict.pop('annotated')
    

    try:
        local_layer.__dict__.update(remote_dict)
        local_layer.save()
        modified_date = remote_dict['date_modified']
        sql_command = "UPDATE data_manager_layer set date_modified = '{}' WHERE id = {};".format(modified_date, local_layer.id)
        with connection.cursor() as cursor:
            cursor.execute(sql_command)
        data['status'] = 'Success'
        data['message'] = 'Layer updated successfully'
    except Exception as e:
        data['status'] = 'Error'
        data['message'] = str(e)
    return JsonResponse(data)

def migration_merge_layer_request(request):
    if request.POST:
        portal_id = request.POST.get('portal_id')
        local_id = request.POST.get('local_id')
        remote_uuid = request.POST.get('remote_uuid')
        portal = ExternalPortal.objects.get(pk=int(portal_id))
        # local_layer = Layer.objects.get(pk=int(local_id))

        remote_layers_response = requests.get(f"{portal.get_layer_detail_endpoint}{remote_uuid}/")
        
        remote_layer_dict = remote_layers_response.json()['layers'][remote_uuid]
        if not (type(request.site) == Site):
            try:
                site = Site.objects.get(domain=request.get_host())
                request.site = site
            except Exception as e:
                request.site = None
        merge_json_response = migration_merge_layer(local_id, remote_layer_dict, sites=[request.site,])
        return merge_json_response