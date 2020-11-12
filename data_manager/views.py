from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page
from .models import *
from .serializers import BriefLayerSerializer
from rest_framework import viewsets

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
    layer = Layer.all_objects.get(pk=layerID)
    return JsonResponse(layer.toDict)

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

    url = request.GET.get('url')
    result = wms_get_capabilities(url)

    return JsonResponse(result)
