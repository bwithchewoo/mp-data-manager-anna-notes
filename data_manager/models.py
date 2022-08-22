from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.conf import settings
#from sorl.thumbnail import ImageField
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin.models import LogEntry
from colorfield.fields import ColorField
# From MARCO/utils.py
def get_domain(port=8010):
    try:
        #domain = Site.objects.all()[0].domain
        domain = Site.objects.get(id=SITE_ID).domain
        if 'localhost' in domain:
            domain = 'localhost:%s' %port
        domain = 'http://' + domain
    except:
        domain = '..'
    #print(domain)
    return domain

def reset_cache(sites):
    from django.core.cache import cache
    import requests
    from requests.exceptions import ConnectionError
    for site in sites:
        cache.delete('data_manager_json_site_%s' % site.pk)
        from marco.settings import DEBUG
        if DEBUG and ('localhost:' in site.domain or '127.0.0.1:' in site.domain):
            url = "http://%s:8000/data_manager/get_json" % site.domain[:site.domain.index(':')]
        else:
            url = "http://%s/data_manager/get_json" % site.domain
        try:
            requests.get(url)
        except ConnectionError:
            #sometimes testing overdoes this a bit and we get 'Max retries exceeded'
            print('recache error - either port isn\'t listening or you\'ve maxed out your retries')

class SiteFlags(object):#(models.Model):
    """Add-on class for displaying sites in the list_display
    in the admin.
    """
    def primary_site(self):
        return self.site.filter(id=1).exists()
    primary_site.boolean = True

    def preview_site(self):
        return self.site.filter(id=2).exists()
    preview_site.boolean = True

class Theme(models.Model, SiteFlags):
    site = models.ManyToManyField(Site)
    display_name = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(default=10, blank=True, null=True, help_text='input an integer to determine the priority/order of the layer being displayed (1 being the highest)')
    visible = models.BooleanField(default=True)
    header_image = models.CharField(max_length=255, blank=True, null=True)
    header_attrib = models.CharField(max_length=255, blank=True, null=True)
    overview = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.URLField(max_length=255, blank=True, null=True)

    factsheet_thumb = models.CharField(max_length=255, blank=True, null=True)
    factsheet_link = models.CharField(max_length=255, blank=True, null=True)

    # not really using these atm
    feature_image = models.CharField(max_length=255, blank=True, null=True)
    feature_excerpt = models.TextField(blank=True, null=True)
    feature_link = models.CharField(max_length=255, blank=True, null=True)

    # objects = models.Manager()
    objects = CurrentSiteManager('site')
    all_objects = models.Manager()

    def url(self):
        id = self.id
        return '/visualize/#x=-73.24&y=38.93&z=7&logo=true&controls=true&basemap=Ocean&themes[ids][]=%s&tab=data&legends=false&layers=true' % (id)

    def __unicode__(self):
        return unicode('%s' % (self.name))

    def __str__(self):
        return str(self.name)

    @property
    def learn_link(self):
        domain = get_domain(8000)
        return '%s/learn/%s' %(domain, self.name)

    def dictCache(self, site_id=None):
        from django.core.cache import cache
        themes_dict = None
        if site_id in [x.id for x in self.site.all()]:
            if site_id:
                themes_dict = cache.get('data_manager_theme_%d_%d' % (self.id, site_id))
            if not themes_dict:
                themes_dict = self.toDict
                themes_dict['layers'] = [layer.id for layer in Layer.all_objects.filter(site__in=[site_id],is_sublayer=False,themes__in=[self.id]).exclude(layer_type='placeholder')]
                if site_id:
                    # Cache for 1 week, will be reset if layer data changes
                    cache.set('data_manager_theme_%d_%d' % (self.id, site_id), themes_dict, 60*60*24*7)
                else:
                    for site in Site.objects.all():
                        cache.set('data_manager_theme_%d_%d' % (self.id, site.id), themes_dict, 60*60*24*7)
        return themes_dict


    @property
    def toDict(self):
        layers = [layer.id for layer in Layer.objects.filter(is_sublayer=False,sublayers__in=[self.id]).exclude(layer_type='placeholder')]
        themes_dict = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'learn_link': self.learn_link,
            'is_visible': self.visible,
            'layers': layers,
            'description': self.description
        }

        return themes_dict

    def getInitDict(self):
        theme_dict = {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'is_visible': self.visible,
        }

        return theme_dict

    def save(self, *args, **kwargs):
        from django.core.cache import cache
        for site in Site.objects.all():
            cache.delete('data_manager_json_site_%s' % site.pk)
            # 'data_manager_theme_%d_%d' % (self.id, site_id)
            if self.id:
                cache.delete('data_manager_theme_%d_%d' % (self.id, site.pk))
        super(Theme, self).save(*args, **kwargs)

class Layer(models.Model, SiteFlags):
    
    WMS_VERSION_CHOICES = (
        (None, ''),
        ('1.0.0', '1.0.0'),
        ('1.1.0', '1.1.0'),
        ('1.1.1', '1.1.1'),
        ('1.3.0', '1.3.0'),
    )
    COLOR_PALETTE = []

    COLOR_PALETTE.append(("#FFFFFF", 'white'))
    COLOR_PALETTE.append(("#888888", 'gray'))
    COLOR_PALETTE.append(("#000000", 'black'))
    COLOR_PALETTE.append(("#FF0000", 'red'))
    COLOR_PALETTE.append(("#FFFF00", 'yellow'))
    COLOR_PALETTE.append(("#00FF00", 'green'))
    COLOR_PALETTE.append(("#00FFFF", 'cyan'))
    COLOR_PALETTE.append(("#0000FF", 'blue'))
    COLOR_PALETTE.append(("#FF00FF", 'magenta'))

    site = models.ManyToManyField(Site)
    name = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(default=10, blank=True, null=True, help_text='input an integer to determine the priority/order of the layer being displayed (1 being the highest)')
    slug_name = models.CharField(max_length=200, blank=True, null=True)
    layer_type = models.CharField(max_length=50, choices=settings.LAYER_TYPE_CHOICES, help_text='use placeholder to temporarily remove layer from TOC')
    url = models.TextField(blank=True, null=True)
    shareable_url = models.BooleanField(default=True, help_text='Indicates whether the data layer (e.g. map tiles) can be shared with others (through the Map Tiles Link)')
    proxy_url = models.BooleanField(default=False, help_text="proxy layer url through marine planner")
    arcgis_layers = models.CharField(max_length=255, blank=True, null=True, help_text='comma separated list of arcgis layer IDs')
    query_by_point = models.BooleanField(default=False, help_text='Do not buffer selection clicks (not recommended for point or line data)')
    disable_arcgis_attributes = models.BooleanField(default=False, help_text='Click to disable clickable ArcRest layers')
    wms_help = models.BooleanField(default=False, help_text='Enable simple selection for WMS fields. Only supports WMS 1.1.1')
    wms_slug = models.CharField(max_length=255, blank=True, null=True, verbose_name='WMS Layer Name')
    wms_version = models.CharField(max_length=10, blank=True, null=True, default=None, choices=WMS_VERSION_CHOICES, help_text='WMS Versioning - usually either 1.1.1 or 1.3.0')
    wms_format = models.CharField(max_length=100, blank=True, null=True, default=None, help_text='most common: image/png. Only image types supported.', verbose_name='WMS Format')
    wms_srs = models.CharField(max_length=100, blank=True, null=True, default=None, help_text='If not EPSG:3857 WMS requests will be proxied', verbose_name='WMS SRS')
    wms_styles = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='pre-determined styles, if exist', verbose_name='WMS Styles')
    wms_timing = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='http://docs.geoserver.org/stable/en/user/services/wms/time.html#specifying-a-time', verbose_name='WMS Time')
    wms_time_item = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='Time Attribute Field, if different from "TIME". Proxy only.', verbose_name='WMS Time Field')
    wms_additional = models.TextField(blank=True, null=True, default=None, help_text='additional WMS key-value pairs: &key=value...', verbose_name='WMS Additional Fields')
    wms_info = models.BooleanField(default=False, help_text='enable Feature Info requests on click')
    wms_info_format = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='Available supported feature info formats')
    is_sublayer = models.BooleanField(default=False)
    sublayers = models.ManyToManyField('self', blank=True)
    themes = models.ManyToManyField("Theme", blank=True)
    search_query = models.BooleanField(default=False, help_text='Select when layers are queryable - e.g. MDAT and CAS')
    has_companion = models.BooleanField(default=False, help_text='Check if this layer has a companion layer')
    connect_companion_layers_to = models.ManyToManyField('self', blank=True, help_text='Select which main layer(s) you would like to use in conjuction with this companion layer.')
    is_disabled = models.BooleanField(default=False, help_text='when disabled, the layer will still appear in the TOC, only disabled')
    disabled_message = models.CharField(max_length=255, blank=True, null=True, default=None)
    legend = models.CharField(max_length=255, blank=True, null=True, help_text='URL or path to the legend image file')
    legend_title = models.CharField(max_length=255, blank=True, null=True, help_text='alternative to using the layer name')
    legend_subtitle = models.CharField(max_length=255, blank=True, null=True)
    show_legend = models.BooleanField(default=True, help_text='show the legend for this layer if available')
    utfurl = models.CharField(max_length=255, blank=True, null=True)

    # RDH: utfjsonp does not appear to be used.
    # utfjsonp = models.BooleanField(default=False)
    # RDH: summarize_to_grid does not appear to be used.
    # summarize_to_grid = models.BooleanField(default=False)
    # RDH: filterable is used in planner.html and filters.html, regarding visibility
    # TODO: need to identify how/why this is used and integrate into ocean_portal code base
    #       Filterable is used for 'beach cleanup' and 'derelict gear' layers.
    filterable = models.BooleanField(default=False)
    # RDH: geoportal_id is used in data_manager view 'geoportal_ids', which is never used
    geoportal_id = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="GeoPortal UUID")
    # RDH: proj does not appear to be used.
    # proj = models.CharField(max_length=255, blank=True, null=True, help_text="will be EPSG:3857, if unspecified")

    #tooltip
    description = models.TextField(blank=True, null=True)

    data_overview = models.TextField(blank=True, null=True)
    data_source = models.CharField(max_length=255, blank=True, null=True)
    data_notes = models.TextField(blank=True, null=True)
    data_publish_date = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True, default=None, verbose_name='Date published', help_text='YYYY-MM-DD')

    #data catalog links
    catalog_name = models.TextField(null=True, blank=True, help_text="name of associated record in catalog", verbose_name='Catalog Record Name')
    catalog_id = models.TextField(null=True, blank=True, help_text="unique ID of associated record in catalog", verbose_name='Catalog Record Id')
    bookmark = models.CharField(max_length=755, blank=True, null=True, help_text='link to view data layer in the planner')
    kml = models.CharField(max_length=255, blank=True, null=True, help_text='link to download the KML')
    data_download = models.CharField(max_length=255, blank=True, null=True, help_text='link to download the data')
    learn_more = models.CharField(max_length=255, blank=True, null=True, default=None, help_text='link to view description in the Learn section')
    metadata = models.CharField(max_length=255, blank=True, null=True, help_text='link to view/download the metadata')
    source = models.CharField(max_length=255, blank=True, null=True, help_text='link back to the data source')
    map_tiles = models.CharField(max_length=255, blank=True, null=True, help_text='internal link to a page that details how others might consume the data')
    thumbnail = models.URLField(max_length=255, blank=True, null=True, default=None, help_text='not sure we are using this any longer...')

    ### ATTRIBUTE REPORTING ###
    label_field = models.CharField(max_length=255, blank=True, null=True, help_text="Which field should be used for labels and feature identification in reports?")
    #geojson javascript attribution
    EVENT_CHOICES = (
        ('click', 'click'),
        ('mouseover', 'mouseover')
    )
    # RDH: Adds a 'title' to the serialize_attributes dict - not sure if that's used.
    # attribute_title = models.CharField(max_length=255, blank=True, null=True)
    attribute_fields = models.ManyToManyField('AttributeInfo', blank=True)
    compress_display = models.BooleanField(default=False)
    attribute_event = models.CharField(max_length=35, choices=EVENT_CHOICES, default='click')
    mouseover_field = models.CharField(max_length=75, blank=True, null=True, default=None, help_text='feature level attribute used in mouseover display')
    lookup_field = models.CharField(max_length=255, blank=True, null=True, help_text="To override the style based on specific attributes, provide the attribute name here and define your attributes in the Lookup table below.")
    lookup_table = models.ManyToManyField('LookupInfo', blank=True)
    is_annotated = models.BooleanField(default=False)

    CUSTOM_STYLE_CHOICES = (
        (None, '------'),
        ('color', 'color'),
        ('random', 'random'),
    )
    custom_style = models.CharField(
        max_length=255, 
        null=True, blank=True, default=None, 
        choices=CUSTOM_STYLE_CHOICES,
        help_text="Apply a custom styling rule: i.e. 'color' for Native-Land.ca layers, or 'random' to assign arbitary colors"
    )
    vector_outline_color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Vector Stroke Color",
        samples=COLOR_PALETTE,
    )
    # RDH 20191106 - This is not a thing.
    vector_outline_opacity = models.FloatField(blank=True, null=True, default=None, verbose_name="Vector Stroke Opacity")
    vector_outline_width = models.IntegerField(blank=True, null=True, default=None, verbose_name="Vector Stroke Width")
    vector_color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Vector Fill Color",
        samples=COLOR_PALETTE,
    )
    vector_fill = models.FloatField(blank=True, null=True, default=None, verbose_name="Vector Fill Opacity")
    vector_graphic = models.CharField(max_length=255, blank=True, null=True, default=None, verbose_name="Vector Graphic", help_text="address of image to use for point data")
    vector_graphic_scale = models.FloatField(blank=True, null=True, default=True, verbose_name="Vector Graphic Scale", help_text="Scale for the vector graphic from original size.")
    point_radius = models.IntegerField(blank=True, null=True, default=None, help_text='Used only for for Point layers (default is 2)')
    opacity = models.FloatField(default=.5, blank=True, null=True, verbose_name="Initial Opacity")

    objects = CurrentSiteManager('site')
    all_objects = models.Manager()

    #ESPIS Upgrade - RDH 7/23/2017
    ESPIS_REGION_CHOICES = (
        ('Mid Atlantic', 'Mid Atlantic'),
    )
    espis_enabled = models.BooleanField(default=False)
    espis_search = models.CharField(max_length=255, blank=True, null=True, default=None, help_text="keyphrase search for ESPIS Link")
    espis_region = models.CharField(max_length=100, blank=True, null=True, default=None, choices=ESPIS_REGION_CHOICES, help_text="Region to search within")

    date_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return unicode('%s' % (self.name))

    def __str__(self):
        return str(self.name)

    @property
    def is_parent(self):
        return self.sublayers.all().count() > 0 and not self.is_sublayer

    @property
    def parent(self):
        if self.is_sublayer:
            if self.sublayers.all().count() > 0:
                return self.sublayers.all()[0]
            else:
                return None
        return self

    @property
    def last_change(self):
        layer_ct = ContentType.objects.get(model='layer')
        logs = LogEntry.objects.filter(content_type=layer_ct, object_id=self.pk)
        if len(logs) > 0:
            last_log = logs.order_by('-action_time')[0]
            return last_log.action_time
        else:
            return None

    def get_absolute_url(self):
        if settings.DATA_CATALOG_ENABLED:
            theme = self.themes.filter(visible=True).first()
            if theme:
                theme_url = reverse('portal.data_catalog.views.theme', args=[theme.name])
                if theme_url:
                    return "{0}#layer-info-{1}".format(theme_url, self.slug_name)
        return None

    @property
    def slug(self):
        # RDH Hack for MDAT v2 transition 8/8/2018.
        # Slug just takes name, but if name is the same then multiple layers have same slug. Should slug include ID?
        if self.slug_name and ('-v2-prod' in self.slug_name or '-v2-staging' in self.slug_name):
            slug_string = "%s-v2%s" % (slugify(self.name),self.slug_name.split('v2')[1])
            return slug_string
        return slugify(self.name)

    @property
    def data_overview_text(self):
        if not self.data_overview and self.is_sublayer and self.parent:
            return self.parent.data_overview
        else:
            return self.data_overview

    @property
    def data_source_text(self):
        if not self.data_source and self.is_sublayer:
            return self.parent.data_source
        else:
            return self.data_source

    @property
    def data_notes_text(self):
        if not self.data_notes and self.is_sublayer:
            return self.parent.data_notes
        else:
            return self.data_notes

    @property
    def bookmark_link(self):
        if self.bookmark and "%%5D=%d&" % self.id in self.bookmark:
            return self.bookmark

        if self.is_sublayer and self.parent.bookmark and len(self.parent.bookmark) > 0:
            return self.parent.bookmark.replace('<layer_id>', str(self.id))

        if self.is_parent:
            for theme in self.themes.all():
                return theme.url()

        # RDH: Most Marine Life layers seem to have bogus bookmarks. If the first line of this def
        #   isn't true, then we likely need to give users something that will work. This should do it.
        root_str = '/visualize/#x=-73.24&y=38.93&z=7&logo=true&controls=true&basemap=Ocean'
        layer_str = '&dls%%5B%%5D=true&dls%%5B%%5D=%s&dls%%5B%%5D=%d' % (str(self.opacity), self.id)
        companion_str = ''
        if self.has_companion:
            for companion in self.connect_companion_layers_to.all():
                companion_str += '&dls%%5B%%5D=false&dls%%5B%%5D=%s&dls%%5B%%5D=%d' % (str(companion.opacity), companion.id)
        themes_str = ''
        if self.themes.all().count() > 0:
            for theme in self.themes.all():
                themes_str = '&themes%%5Bids%%5D%%5B%%5D=%d' % theme.id

        panel_str = '&tab=data&legends=false&layers=true'

        return "%s%s%s%s%s" % (root_str, layer_str, companion_str, themes_str, panel_str)


    @property
    def data_download_link(self):
        if self.data_download and self.data_download.lower() == 'none':
            return None
        if self.parent and not self.data_download and self.is_sublayer:
            return self.parent.data_download
        else:
            return self.data_download

    @property
    def metadata_link(self):
        if self.metadata and self.metadata.lower() == 'none':
            return None
        if not self.metadata:
            if self.is_sublayer and self.parent:
                return self.parent.metadata
            else:
                return None
        else:
            return self.metadata

    @property
    def source_link(self):
        if self.source and self.source.lower() == 'none':
            return None
        if not self.source:
            if self.is_sublayer and self.parent:
                return self.parent.source
            else:
                return None
        else:
            return self.source

    @property
    def description_link(self):
        theme_name = self.themes.all()[0].name
        domain = get_domain(8000)
        return '%s/learn/%s#%s' %(domain, theme_name, self.slug_name)

    @property
    def tiles_link(self):
        if self.is_shareable and self.layer_type in ['XYZ', 'ArcRest', 'WMS']:
            domain = get_domain(8000)
            return self.slug_name
        return None

    @property
    def tooltip(self):
        if self.description and self.description.strip() != '':
            return self.description
        elif self.parent and self.parent.description and self.parent.description.strip() != '':
            return self.parent.description
        else:
            return self.data_overview_text

    @property
    def is_shareable(self):
        if self.shareable_url == False:
            return False
        if self.parent and self.parent.shareable_url == False:
            return False
        return True

    def serialize_attributes(self):
        return {'compress_attributes': self.compress_display,
                'event': self.attribute_event,
                'attributes': [{'display': attr.display_name, 'field': attr.field_name, 'precision': attr.precision} for attr in self.attribute_fields.all().order_by('order')],
                'mouseover_attribute': self.mouseover_field,
                'preserved_format_attributes': [attr.field_name for attr in self.attribute_fields.filter(preserve_format=True)]
        }

    @property
    def serialize_lookups(self):
        return {'field': self.lookup_field,
                'details': [{'value': lookup.value, 'color': lookup.color, 'stroke_color': lookup.stroke_color, 'stroke_width': lookup.stroke_width, 'dashstyle': lookup.dashstyle, 'fill': lookup.fill, 'graphic': lookup.graphic, 'graphic_scale': lookup.graphic_scale} for lookup in self.lookup_table.all()]}

    def get_espis_link(self):
        if self.espis_enabled:
            search_dict = {}
            if self.espis_search:
                search_dict['txt'] = self.espis_search
            if self.espis_region:
                search_dict['geo'] = self.espis_region
            if len(search_dict) > 0:
                try:
                    # python 3
                    from urllib.parse import urlencode
                except (ModuleNotFoundError, ImportError) as e:
                    #python 2
                    from urllib import urlencode
                return 'https://marinecadastre.gov/espis/#/search/%s' % urlencode(search_dict)
        return None

    def dimensionRecursion(self, dimensions, associations):
        associationArray = {}
        dimension = dimensions.pop(0)
        for value in sorted(dimension.multilayerdimensionvalue_set.all(), key=lambda x: x.order):
            value_associations = associations.filter(pk__in=[x.pk for x in value.associations.all()])
            if len(dimensions) > 0:
                associationArray[str(value.value)] = self.dimensionRecursion(list(dimensions), value_associations)
            else:
                if len(value_associations) == 1 and value_associations[0].layer:
                    associationArray[str(value.value)] = value_associations[0].layer.pk
                else:
                    associationArray[str(value.value)] = None
        return associationArray

    @property
    def isMultilayerParent(self):
        return len(self.multilayerdimension_set.all()) > 0

    @property
    def isMultilayer(self):
        return len(self.associated_layer.all()) > 0

    @property
    def dimensions(self):
        return sorted([
            {
                'label': x.label,
                'name': x.name,
                'order': x.order,
                'animated': x.animated,
                'angle_labels': x.angle_labels,
                'nodes': sorted([
                    {
                        'value': y.value,
                        'label': y.label,
                        'order': y.order
                    }
                    for y in x.multilayerdimensionvalue_set.all()
                ], key=lambda y: y['order'])
            }
            for x in self.multilayerdimension_set.all()
        ], key=lambda x: x['order'])

    @property
    def catalog_html(self):
        from django.template.loader import render_to_string
        try:
            return render_to_string(
                "data_catalog/includes/cacheless_layer_info.html",
                {
                    'layer': self,
                    # 'sub_layers': self.sublayers.exclude(layer_type="placeholder")
                }
            )
        except Exception as e:
            print(e)

    @property
    def associatedMultilayers(self):
        if len(self.multilayerdimension_set.all()) > 0:
            return self.dimensionRecursion(sorted(self.multilayerdimension_set.all(), key=lambda x: x.order), self.parent_layer.all())
        else:
            return {}

    def dictCache(self, site_id=None):
        from django.core.cache import cache
        layers_dict = None
        if site_id in [x.id for x in self.site.all()]:
            if site_id:
                layers_dict = cache.get('data_manager_layer_%d_%d' % (self.id, site_id))
            if not layers_dict:
                layers_dict = self.toDict
                if site_id:
                    # Cache for 1 week, will be reset if layer data changes
                    cache.set('data_manager_layer_%d_%d' % (self.id, site_id), layers_dict, 60*60*24*7)
                else:
                    for site in Site.objects.all():
                        cache.set('data_manager_layer_%d_%d' % (self.id, site.id), layers_dict, 60*60*24*7)
        return layers_dict

    @property
    def toDict(self, site_id=None):
        parent = self.parent
        if parent == self:
            parent = None
        elif not parent == None:
            try:
                parent = parent.toDict
            except Exception as e:
                parent = None
        sublayers = [
            {
                'id': layer.id,
                'is_sublayer': layer.is_sublayer,
                'name': layer.name,
                'order': layer.order,
                'type': layer.layer_type,
                'url': layer.url,
                'arcgis_layers': layer.arcgis_layers,
                'query_by_point': layer.query_by_point,
                'proxy_url': layer.proxy_url,
                'disable_arcgis_attributes': layer.disable_arcgis_attributes,
                'wms_slug': layer.wms_slug,
                'wms_version': layer.wms_version,
                'wms_format': layer.wms_format,
                'wms_srs': layer.wms_srs,
                'wms_styles': layer.wms_styles,
                'wms_timing': layer.wms_timing,
                'wms_time_item': layer.wms_time_item,
                'wms_additional': layer.wms_additional,
                'wms_info': layer.wms_info,
                'wms_info_format': layer.wms_info_format,
                'utfurl': layer.utfurl,
                'parent': self.id,
                'legend': layer.legend,
                'legend_title': layer.legend_title,
                'legend_subtitle': layer.legend_subtitle,
                'show_legend': layer.show_legend,
                'description': layer.tooltip,
                'overview': layer.data_overview_text,
                'data_source': layer.data_source,
                'data_notes': layer.data_notes,
                'kml': layer.kml,
                'data_download': layer.data_download_link,
                'learn_more': layer.learn_more,
                'metadata': layer.metadata_link,
                'source': layer.source_link,
                'tiles': layer.tiles_link,
                'label_field': layer.label_field,
                'attributes': layer.serialize_attributes(),
                'lookups': layer.serialize_lookups,
                'custom_style': layer.custom_style,
                'outline_color': layer.vector_outline_color,
                'outline_opacity': layer.vector_outline_opacity,
                'outline_width': layer.vector_outline_width,
                'point_radius': layer.point_radius,
                'color': layer.vector_color,
                'fill_opacity': layer.vector_fill,
                'graphic': layer.vector_graphic,
                'graphic_scale': layer.vector_graphic_scale,
                'opacity': layer.opacity,
                'annotated': layer.is_annotated,
                'is_disabled': layer.is_disabled,
                'disabled_message': layer.disabled_message,
                'data_url': layer.get_absolute_url(),
                'has_companion': layer.has_companion,
                'is_multilayer': layer.isMultilayer,
                'is_multilayer_parent': layer.isMultilayerParent,
                'dimensions': layer.dimensions,
                'associated_multilayers': layer.associatedMultilayers
            }
            for layer in self.sublayers.filter(is_sublayer=True)
        ]
        connect_companion_layers_to = [
            {
                'id': layer.id,
                'name': layer.name,
                'order': layer.order,
                'type': layer.layer_type,
                'url': layer.url,
                'arcgis_layers': layer.arcgis_layers,
                'query_by_point': layer.query_by_point,
                'proxy_url': layer.proxy_url,
                'disable_arcgis_attributes': layer.disable_arcgis_attributes,
                'wms_slug': layer.wms_slug,
                'wms_version': layer.wms_version,
                'wms_format': layer.wms_format,
                'wms_srs': layer.wms_srs,
                'wms_styles': layer.wms_styles,
                'wms_timing': layer.wms_timing,
                'wms_time_item': layer.wms_time_item,
                'wms_additional': layer.wms_additional,
                'wms_info': layer.wms_info,
                'wms_info_format': layer.wms_info_format,
                'utfurl': layer.utfurl,
                'parent': self.id,
                'legend': layer.legend,
                'legend_title': layer.legend_title,
                'legend_subtitle': layer.legend_subtitle,
                'show_legend': layer.show_legend,
                'description': layer.tooltip,
                'overview': layer.data_overview_text,
                'data_source': layer.data_source,
                'data_notes': layer.data_notes,
                'kml': layer.kml,
                'data_download': layer.data_download_link,
                'learn_more': layer.learn_more,
                'metadata': layer.metadata_link,
                'source': layer.source_link,
                'tiles': layer.tiles_link,
                'label_field': layer.label_field,
                'attributes': layer.serialize_attributes(),
                'lookups': layer.serialize_lookups,
                'custom_style': layer.custom_style,
                'outline_color': layer.vector_outline_color,
                'outline_opacity': layer.vector_outline_opacity,
                'outline_width': layer.vector_outline_width,
                'point_radius': layer.point_radius,
                'color': layer.vector_color,
                'fill_opacity': layer.vector_fill,
                'graphic': layer.vector_graphic,
                'graphic_scale': layer.vector_graphic_scale,
                'opacity': layer.opacity,
                'annotated': layer.is_annotated,
                'is_disabled': layer.is_disabled,
                'disabled_message': layer.disabled_message,
                'data_url': layer.get_absolute_url(),
                'has_companion': layer.has_companion,
                'is_multilayer': layer.isMultilayer,
                'is_multilayer_parent': layer.isMultilayerParent,
                'dimensions': layer.dimensions,
                'associated_multilayers': layer.associatedMultilayers
            }
            for layer in self.connect_companion_layers_to.all()
        ]
        layers_dict = {
            'id': self.id,
            'name': self.name,
            'order': self.order,
            'type': self.layer_type,
            'url': self.url,
            'arcgis_layers': self.arcgis_layers,
            'query_by_point': self.query_by_point,
            'proxy_url': self.proxy_url,
            'disable_arcgis_attributes': self.disable_arcgis_attributes,
            'wms_slug': self.wms_slug,
            'wms_version': self.wms_version,
            'wms_format': self.wms_format,
            'wms_srs': self.wms_srs,
            'wms_styles': self.wms_styles,
            'wms_timing': self.wms_timing,
            'wms_time_item': self.wms_time_item,
            'wms_additional': self.wms_additional,
            'wms_info': self.wms_info,
            'wms_info_format': self.wms_info_format,
            'utfurl': self.utfurl,
            'subLayers': sublayers,
            'companion_layers': connect_companion_layers_to,
            'has_companion': self.has_companion,
            'queryable': self.search_query,
            'legend': self.legend,
            'legend_title': self.legend_title,
            'legend_subtitle': self.legend_subtitle,
            'show_legend': self.show_legend,
            'description': self.description,
            'overview': self.data_overview,
            'data_source': self.data_source,
            'data_notes': self.data_notes,
            'kml': self.kml,
            'data_download': self.data_download_link,
            'learn_more': self.learn_more,
            'metadata': self.metadata_link,
            'source': self.source_link,
            'tiles': self.tiles_link,
            'label_field': self.label_field,
            'attributes': self.serialize_attributes(),
            'lookups': self.serialize_lookups,
            'custom_style': self.custom_style,
            'outline_color': self.vector_outline_color,
            'outline_opacity': self.vector_outline_opacity,
            'outline_width': self.vector_outline_width,
            'point_radius': self.point_radius,
            'color': self.vector_color,
            'fill_opacity': self.vector_fill,
            'graphic': self.vector_graphic,
            'graphic_scale': self.vector_graphic_scale,
            'opacity': self.opacity,
            'annotated': self.is_annotated,
            'is_disabled': self.is_disabled,
            'disabled_message': self.disabled_message,
            'data_url': self.get_absolute_url(),
            'is_multilayer': self.isMultilayer,
            'is_multilayer_parent': self.isMultilayerParent,
            'dimensions': self.dimensions,
            'associated_multilayers': self.associatedMultilayers,
            'catalog_html': self.catalog_html,
            'parent': parent
        }

        return layers_dict

    def catalogDict(self, site_id=None):
        parent = self.parent
        if parent == self:
            parent = None
        elif not parent == None:
            try:
                parent = {
                    'id':parent.id,
                    'name': parent.name,
                }
            except Exception as e:
                parent = None

        sublayers = [sublayer.catalogDict(site_id) for sublayer in self.sublayers.filter(is_sublayer=True).order_by('order')]
        # companions = [companion.catalogDict(site_id) for companion in self.connect_companion_layers_to.all().order_by('order')]
        layers_dict = {
            'id': self.id,
            'name': self.name,
            'slug_name': self.slug_name,
            'bookmark_link': self.bookmark_link,
            'is_sublayer': self.is_sublayer,
            'parent': parent,
            'kml': self.kml,
            'data_download_link': self.data_download_link,
            'metadata_link': self.metadata_link,
            'source': self.source_link,
            'tiles_link': self.tiles_link,
            'description': self.description,
            'data_overview': self.data_overview,
            'espis_enabled': self.espis_enabled,
            'espis_search': self.espis_search,
            'espis_region': self.espis_region,
            'get_espis_link': self.get_espis_link,
            'sublayers': sublayers,
            # 'companions': companions
        }

        return layers_dict

    def shortDict(self, site_id=None):
        sublayers = [{
            'id':sublayer.id,
            'parent': {'name':self.name},
            'name':sublayer.name,
            'slug_name': sublayer.slug_name,
            'bookmark_link': sublayer.bookmark_link,
            'is_sublayer': True,
            'sublayers': [],
        } for sublayer in self.sublayers.filter(is_sublayer=True).order_by('name')]
        # sublayers = [sublayer.shortDict(site_id) for sublayer in self.sublayers.filter(is_sublayer=True).order_by('order')]
        # companions = [{
        #     'id':companion.id,
        #     'parent': {'name':self.name},
        #     'name':companion.name,
        #     'slug_name': companion.slug_name,
        #     'bookmark_link': companion.bookmark_link,
        #     'is_sublayer': companion.is_sublayer,
        #     'sublayers': [],
        # } for companion in self.connect_companion_layers_to.all().order_by('name')]
        layers_dict = {
            'id': self.id,
            'parent': None,
            'name': self.name,
            'slug_name': self.slug_name,
            'bookmark_link': self.bookmark_link,
            'is_sublayer': self.is_sublayer,
            'sublayers': sublayers,
            # 'companions': companions,
        }
        return layers_dict

    def save(self, *args, **kwargs):
        from django.core.cache import cache
        if 'slug_name' in kwargs.keys():
            self.slug_name = kwargs['slug_name']
            kwargs.pop('slug_name', None)
        else:
            if self.id:
                self.slug_name = '%s%d' % (self.slug, self.id)
            else:
                self.slug_name = '%s_new' % self.slug
        if self.url == None:
            self.url = ''
        if 'recache' in kwargs.keys():
            kwargs.pop('recache', None)
        # TODO: determine all themes, companions, ancestors, and decendants prior to saving
        #       clear all of their caches.
        #       How do we do this thoroughly?
        #       How do we avoid infinite loops? (companions)(recursion?)
        super(Layer, self).save(*args, **kwargs)
        for site in Site.objects.all():
            cache.delete('data_manager_json_site_%s' % site.pk)
            cache.delete('data_manager_layer_%d_%d' % (self.id, site.pk))
            self.dictCache(site.pk)
            # Delete cache for all sublayers
            for sublayer in self.sublayers.all():
                cache.delete('data_manager_layer_%d_%d' % (sublayer.id, site.pk))
                sublayer.dictCache(site.pk)
            # Delete cache for parent layers (in case not double-linked)
            for parentlayer in Layer.objects.filter(sublayers__in=[self]):
                cache.delete('data_manager_layer_%d_%d' % (parentlayer.id, site.pk))
                parentlayer.dictCache(site.pk)
            # Delete cache for companion layers
            for companion in self.connect_companion_layers_to.all():
                cache.delete('data_manager_layer_%d_%d' % (companion.id, site.pk))
                companion.dictCache(site.pk)
            for companion in Layer.objects.filter(connect_companion_layers_to__in=[self]):
                cache.delete('data_manager_layer_%d_%d' % (companion.id, site.pk))
                companion.dictCache(site.pk)
            for association in self.associated_layer.all():
                cache.delete('data_manager_layer_%d_%d' % (association.parentLayer.pk, site.pk))
                association.layer.dictCache(site.pk)
            # TODO: if len(self.themes.all() == 0): delete all theme caches?
            #   On initial save, layers don't seem to know what themes they are associated with. :(
            for theme in self.themes.all():
                cache.delete('data_manager_theme_%d_%d' % (theme.pk, site.pk))
                theme.dictCache(site.pk)

class AttributeInfo(models.Model):
    display_name = models.CharField(max_length=255, blank=True, null=True)
    field_name = models.CharField(max_length=255, blank=True, null=True)
    precision = models.IntegerField(blank=True, null=True)
    order = models.IntegerField(default=1)
    preserve_format = models.BooleanField(default=False, help_text='Prevent portal from making any changes to the data to make it human-readable')

    def __unicode__(self):
        return unicode('%s' % (self.field_name))

    def __str__(self):
        return str(self.field_name)

class LookupInfo(models.Model):
    DASH_CHOICES = (
        ('dot', 'dot'),
        ('dash', 'dash'),
        ('dashdot', 'dashdot'),
        ('longdash', 'longdash'),
        ('longdashdot', 'longdashdot'),
        ('solid', 'solid')
    )
    COLOR_PALETTE = []

    COLOR_PALETTE.append(("#FFFFFF", 'white'))
    COLOR_PALETTE.append(("#888888", 'gray'))
    COLOR_PALETTE.append(("#000000", 'black'))
    COLOR_PALETTE.append(("#FF0000", 'red'))
    COLOR_PALETTE.append(("#FFFF00", 'yellow'))
    COLOR_PALETTE.append(("#00FF00", 'green'))
    COLOR_PALETTE.append(("#00FFFF", 'cyan'))
    COLOR_PALETTE.append(("#0000FF", 'blue'))
    COLOR_PALETTE.append(("#FF00FF", 'magenta'))

    value = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True, default=None)
    color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Fill Color",
        samples=COLOR_PALETTE,
    )
    stroke_color = ColorField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Stroke Color",
        samples=COLOR_PALETTE,
    )
    stroke_width = models.IntegerField(null=True, blank=True, default=None, verbose_name="Stroke Width")
    dashstyle = models.CharField(max_length=11, choices=DASH_CHOICES, default='solid')
    fill = models.BooleanField(default=False)
    graphic = models.CharField(max_length=255, blank=True, null=True)
    graphic_scale = models.FloatField(null=True, blank=True, default=None, verbose_name="Graphic Scale", help_text="Scale the graphic from its original size.")

    def __unicode__(self):
        if self.description:
            return unicode('{}: {}'.format(self.value, self.description))
        return unicode('%s' % (self.value))

    def __str__(self):
        if self.description:
            return '{}: {}'.format(self.value, self.description)
        return str(self.value)

class DataNeed(models.Model):
    name = models.CharField(max_length=100)
    archived = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    contact = models.CharField(max_length=255, blank=True, null=True)
    contact_email = models.CharField(max_length=255, blank=True, null=True)
    expected_date = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    themes = models.ManyToManyField("Theme", blank=True)

    @property
    def html_name(self):
        return self.name.lower().replace(' ', '-')

    def __unicode__(self):
        return unicode('%s' % (self.name))

    def __str__(self):
        return str(self.name)

class MultilayerDimension(models.Model):
    name = models.CharField(max_length=200, help_text='name to be used for selection in admin tool forms')
    label = models.CharField(max_length=50, help_text='label to be used in mapping tool slider')
    order = models.IntegerField(default=100, help_text='the order in which this dimension will be presented among other dimensions on this layer')
    animated = models.BooleanField(default=False, help_text='enable auto-toggling of layers across this dimension')
    angle_labels = models.BooleanField(default=False, help_text='display labels at an angle to make more fit')
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)

    class Meta:
        ordering = ('order',)

    def save(self, *args, **kwargs):
        super(MultilayerDimension, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if len(self.layer.dimensions) == 1:
            last = True
        else:
            last = False
        for value in self.multilayerdimensionvalue_set.all().order_by('-order'):
            value.delete((),last=last)
        super(MultilayerDimension, self).delete(*args, **kwargs)

class MultilayerAssociation(models.Model):
    name = models.CharField(max_length=200)
    parentLayer = models.ForeignKey(Layer, related_name="parent_layer",
            db_column='parentlayer', on_delete=models.CASCADE)
    layer = models.ForeignKey(Layer, null=True, blank=True, default=None,
            related_name="associated_layer", db_column='associatedlayer',
            on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)

    # def save(self, *args, **kwargs):
    #     super(MultilayerAssociation, self).save(*args, **kwargs)
    #     print("Association: %s +++SAVED+++" % str(self))
    #
    # def delete(self, *args, **kwargs):
    #     super(MultilayerAssociation, self).delete(*args, **kwargs)
    #     print("Association: %s ---DELETED---" % str(self))

class MultilayerDimensionValue(models.Model):
    dimension = models.ForeignKey(MultilayerDimension, on_delete=models.CASCADE)
    value = models.CharField(max_length=200, help_text="Actual value of selection")
    label = models.CharField(max_length=50, help_text="Label for this selection seen in mapping tool slider")
    order = models.IntegerField(default=100)
    associations = models.ManyToManyField(MultilayerAssociation)

    def __unicode__(self):
        return '%s: %s' % (self.dimension, self.value)

    def __str__(self):
        return '%s: %s' % (self.dimension, self.value)

    class Meta:
        ordering = ('order',)

    def save(self, *args, **kwargs):
        if self.pk is None:
            super(MultilayerDimensionValue, self).save(*args, **kwargs)
            parentLayer = self.dimension.layer
            associations = MultilayerAssociation.objects.filter(parentLayer=parentLayer)
            if len(associations) == 0:
                MultilayerAssociation.objects.create(name=str(self), parentLayer=parentLayer)
                associations.update()
            siblingValues = [x for x in self.dimension.multilayerdimensionvalue_set.all() if x != self]
            if len(siblingValues) == 0:
                for association in associations:
                    self.associations.add(association)
            else:
                # If this is not the first value saved to this dimension, choosing
                # an arbitrary sibling value and copying all of its associations
                # is the closest thing we can do to smart generation of associations
                from copy import deepcopy
                siblingValue = siblingValues[0]
                for association in siblingValue.associations.all():
                    dimensionValues = [x for x in association.multilayerdimensionvalue_set.all() if x.dimension != self.dimension]
                    # create a clone of association
                    newAssociation = deepcopy(association)
                    newAssociation.id = None
                    newAssociation.name = 'NEW'
                    newAssociation.save()
                    # restore value/association relationships
                    for value in dimensionValues:
                        value.associations.add(newAssociation)
                    self.associations.add(newAssociation)

        else:
            super(MultilayerDimensionValue, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        delete_all = False
        if kwargs.has_key('last'):
            if kwargs['last']:
                delete_all = True
            kwargs.pop('last', None)
        try:
            for association in self.associations.all():
                if delete_all or len(self.dimension.multilayerdimensionvalue_set.all()) > 1 or len(self.dimension.layer.parent_layer.all()) == 1:
                    association.multilayerdimensionvalue_set.clear()
                    association.delete()
        except ValueError:
            # ValueError: "<MultilayerDimensionValue: Threshold: 10>" needs to have a value for field "multilayerdimensionvalue" before this many-to-many relationship can be used.
            pass

        if self.id:
            # AssertionError: MultilayerDimensionValue object can't be deleted because its id attribute is set to None.
            super(MultilayerDimensionValue, self).delete(*args, **kwargs)
