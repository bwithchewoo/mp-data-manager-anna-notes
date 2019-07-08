from django.core.management.base import BaseCommand
from data_manager.models import Layer, Theme

import requests

class Command(BaseCommand):
    help = "Run an update on MDAT layers"

    def handle(self, *args, **options):
        #theme object for mdat synthetic products - 'conservation'
        mdat = Theme.objects.all().filter(name='conservation')[0]
        mdat_id = mdat.pk

        #allows initial endpoint url to be updated via a faux layer
        mdat_rest_path = Layer.objects.all().filter(name='MDAT', layer_type="placeholder")[0].url

        #grab all parent service directories for enpoint
        r = requests.get(mdat_rest_path+'MDAT?f=json')

        if r.status_code != 200:
            return
        #request status is OK
        else:
            print("**** Request 200 - is OK *****")
            parent_json = r.json()
            mdat_dirs = parent_json['services']

            #loop through mdat service *parent* directory array
            for directory in mdat_dirs:
                print("***** Entering %s *****" % directory['name'])
                #defaults for parent directories
                parent_defaults = {
                    'name':directory['name'],
                    'layer_type':'checkbox',
                }

                synthetic_list = [
                    'MDAT/AvianModels_SyntheticProducts',
                    'MDAT/Fish_NEFSC_SyntheticProducts',
                    'MDAT/Mammal_SyntheticProducts'
                ]

                excluded_list = [
                    'Core Abundance Area - Northeast scale',
                    'Core Abundance Area - Atlantic scale',
                    'Diversity',
                    'Core Biomass Area - Northeast Shelf scale',
                    'Core Biomass Area - Northeast scale',
                    'Breeding: Abundance',
                    'Breeding: Species Richness',
                    'Breeding: Core Abundance Area - Mid-Atlantic scale',
                    'Nonbreeding: Abundance',
                    'Nonbreeding: Species Richness',
                    'Nonbreeding: Core Abundance Area - Mid-Atlantic scale',
                    'Resident: Abundance',
                    'Resident: Species Richness',
                    'Resident: Core Abundance Area - Mid-Atlantic scale'
                ]

                if directory['type'] != 'MapServer':
                    print("***** %s is not a MapServer Layer" % directory['name'])
                    return
                #continue on if it's a MapServer layer && a synthetic product
                elif directory['name'] in synthetic_list:
                    #does layer exist?
                    try:
                        obj = Layer.objects.get(themes=mdat, name=directory['name'])
                    #create parent layer/directory - if not
                    except Layer.DoesNotExist:
                        print("***** Adding %s *****" % directory['name'])
                        obj = Layer.objects.create(**parent_defaults)
                        obj.site = [1,2]
                        obj.themes = [mdat_id]
                        obj.save()

                    #get pk for current layer
                    layer_id = obj.pk

                    #set path
                    layer_path = mdat_rest_path+directory['name']+'/MapServer'

                    #grab all layers of parent endpoint in the loop
                    blob = requests.get(layer_path+'?f=json')
                    layer_json = blob.json()
                    mdat_layers = layer_json['layers']
                    layer_url = layer_path + '/export'

                    #loop through layers within parent directory array
                    for layer in mdat_layers:
                        print("***** Looping through %s *****" % layer['name'])
                        layer_defaults = {
                            'name':layer['name'],
                            'layer_type':'ArcRest',
                            'arcgis_layers':layer['id'],
                            'is_sublayer': 1,
                            'url':layer_url
                        }
                        #no aggregate layers or excluded layers
                        if layer['subLayerIds'] is None and not any(substring in layer['name'] for substring in excluded_list):
                            try:
                                lyr = Layer.objects.get(themes=mdat, arcgis_layers=layer['id'], url=layer_url)
                                #update name, just incase it changed
                                lyr.name = layer['name']
                                lyr.save()
                                print("***** Layer %s exists *****" % layer['name'])
                            #create layers of parent directory - if they don't exist
                            except Layer.DoesNotExist:
                                print("***** Adding %s *****" % layer['name'])
                                lyr = Layer.objects.create(**layer_defaults)
                                lyr.site = [1,2]
                                lyr.themes = [mdat_id]
                                lyr.sublayers = [layer_id]
                                lyr.save()

                                #sublayer fields need to be filled with pks for parent dir
                                obj.sublayers.add(lyr.pk)
                                obj.save()
