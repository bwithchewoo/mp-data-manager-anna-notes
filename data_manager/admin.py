from django.conf import settings
from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django import forms

from import_export import fields, resources
from import_export.admin import ImportExportMixin
import json

import nested_admin
import requests

from .models import *
from .forms import RemotePortalMigrationForm
from .views import compare_remote_layers


class ThemeAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'name', 'order', 'primary_site', 'preview_site')

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'site':
            kwargs['widget'] = forms.CheckboxSelectMultiple()
            kwargs['widget'].attrs['style'] = 'list-style-type: none;'
            kwargs['widget'].can_add_related = False

        return db_field.formfield(**kwargs)

    def get_queryset(self, request):
        # use our manager, rather than the default one
        qs = self.model.all_objects.get_queryset()

        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

class NestedMultilayerDimensionValueInline(nested_admin.NestedTabularInline):
    model = MultilayerDimensionValue
    fields = ('value', 'label', 'order')
    extra = 1
    classes = ['collapse', 'open']
    verbose_name_plural = 'Multilayer Dimension Values'

class NestedMultilayerDimensionInline(nested_admin.NestedTabularInline):
    model = MultilayerDimension
    fields = (('name', 'label', 'order', 'animated', 'angle_labels'),)
    extra = 1
    classes = ['collapse', 'open']
    verbose_name_plural = 'Multilayer Dimensions'
    inlines = [
        NestedMultilayerDimensionValueInline,
    ]

class NestedMultilayerAssociationInline(nested_admin.NestedTabularInline):
    model = MultilayerAssociation
    fk_name = 'parentLayer'
    readonly_fields = ('get_values',)
    fields = (('get_values', 'name', 'layer'),)
    extra = 0
    classes = ['collapse', 'open']
    verbose_name_plural = 'Multilayer Associations'

    def get_values(self, obj):
        return '| %s |' % ' | '.join([str(x) for x in obj.multilayerdimensionvalue_set.all()])

    def get_readlony_values(self, obj):
        return obj.multilayerdimensionvalue_set.all()

    def get_dimensions(self, obj):
        dimensions = []
        for value in obj.multilayerdimensionvalue_set.all():
            dimension = value.dimension
            if dimension not in dimensions:
                dimensions.append(dimension)
        return dimensions

class LayerResource(resources.ModelResource):
    class Meta:
        model = Layer

class LayerForm(forms.ModelForm):
    exclude = ('slug_name',)
    class Meta:
        exclude = ('slug_name',)
        model = Layer
        widgets = {
            'themes': admin.widgets.FilteredSelectMultiple('Themes', False),
            'sublayers': admin.widgets.FilteredSelectMultiple('Sublayers', False),
            'connect_companion_layers_to': admin.widgets.FilteredSelectMultiple('Connect companion layers to', False),
            'attribute_fields': admin.widgets.FilteredSelectMultiple('Attribute fields', False),
            'lookup_table': admin.widgets.FilteredSelectMultiple('Lookup table', False),
        }

class RemoteImportExportMixin(ImportExportMixin):
    import_template_name = 'admin/data_manager/import.html'
    compare_remote_template_name = 'admin/data_manager/compare_remote_layers.html'

    remote_import_form_class = RemotePortalMigrationForm

    # def get_remote_import_form_class(self, request):
    def get_remote_import_form_class(self, request=None):
        return self.remote_import_form_class

    # def create_remote_import_form(self, request):
    def create_remote_import_form(self, request=None):
        if request:
            form_class= self.get_remote_import_form_class(request)
        else:
            form_class= self.get_remote_import_form_class()
        return form_class()
    
    def get_context_data(self, **kwargs):
        context_data = super(RemoteImportExportMixin, self).get_context_data(**kwargs)
        # context_data['remote_import_form'] = self.create_remote_import_form(request)
        context_data['remote_import_form'] = self.create_remote_import_form()
        return context_data

    def import_remote_action(self, request, *args, **kwargs):
        if not self.has_import_permission(request):
            raise PermissionDenied

        view_context = self.get_import_context_data()
        view_context['opts'] = self.model._meta
        results = {
            'status': 'Error',
            'code': 500,
            'message': 'Unknown Error',
            'data': {}
        }
        portal_id = None
        portal_name = None
        portal_url = None

        if request.method == 'POST':
            form =  RemotePortalMigrationForm(request.POST)

            if form.is_valid():
                portal_id = int(form['portal'].value())

                #   * Get Remote Portal Object
                portal = ExternalPortal.objects.get(pk=portal_id)
                portal_name = portal.name
                portal_url = portal.url

                #   * Get Remote Portal Endpoint for layer status
                remote_status = requests.get(f"{portal.layer_status_endpoint}")
                #   * Build layer status comparison dict
                # TODO: Handle Error on request!
                comparison_results = compare_remote_layers(remote_status.json())
                #   * Feed comparison dict back to template
                results = {
                    'status': 'Success',
                    'code': 200,
                    'message': 'Success',
                    # 'data': comparison_results
                }
                remote_status_dict = {
                    # 'layers': [comparison_results['layers'][x] for x in comparison_results['layers'].keys() if not comparison_results['layers'][x]['source'] == 'local'],
                    'layers': comparison_results['layers'],
                    'themes': [remote_status.json()['themes'][key] for key in remote_status.json()['themes'].keys()]
                }
                local_status = {'layers': [comparison_results['layers'][x] for x in comparison_results['layers'].keys() if comparison_results['layers'][x]['source'] == 'local']}
                for layer in local_status['layers']:
                    layer.pop('local_modified')
                    layer.pop('remote_modified')
                    layer['name'] = layer['local_name']


            view_context['results'] = results
            view_context['remote_status'] = remote_status_dict
            view_context['local_status'] = json.dumps(local_status)
            view_context['remote_portal'] = {
                'id': portal_id,
                'name': portal_name,
                'url': portal_url
            }

            return TemplateResponse(request, [self.compare_remote_template_name], view_context)

    def get_urls(self):
        urls = super().get_urls()
        info = self.get_model_info()
        opts = self.model._meta
        remote_import_urls = [
            path('import_remote',
                self.admin_site.admin_view(self.import_remote_action),
                name='%s_%s_import_remote' % info),
        ]
        return remote_import_urls + urls


class LayerAdmin(RemoteImportExportMixin, nested_admin.NestedModelAdmin):
    resource_class = LayerResource
    form = LayerForm
    list_display = ('name', 'layer_type', 'date_modified', 'Theme_', 'order', 'data_publish_date', 'data_source', 'primary_site', 'preview_site', 'url')
    search_fields = ['name', 'layer_type', 'date_modified', 'url', 'data_source']
    ordering = ('name', )
    exclude = ('slug_name',)

    if settings.CATALOG_TECHNOLOGY not in ['default', None]:
        # catalog_fields = ('catalog_name', 'catalog_id',)
        # catalog_fields = 'catalog_name'
        basic_fields = (
                'catalog_name',
                ('name','layer_type',),
                ('url', 'proxy_url'),
                'site'
            )
    else:
        basic_fields = (
                ('name','layer_type',),
                ('url', 'proxy_url'),
                'site'
            )

    fieldsets = (
        ('BASIC INFO', {
            'fields': basic_fields
        }),
        ('LAYER ORGANIZATION', {
            # 'classes': ('collapse', 'open',),
            'fields': (
                ('order','themes'),
                ('is_sublayer','sublayers'),
                ('has_companion','connect_companion_layers_to'),
                # RDH 2019-10-25: We don't use this, and it doesn't seem helpful
                # ('is_disabled','disabled_message')
            )
        }),
        ('METADATA', {
            'classes': ('collapse',),
            'fields': (
                'description', 'data_overview','data_source','data_notes', 'data_publish_date'
            )
        }),
        ('LEGEND', {
            'classes': ('collapse',),
            'fields': (
                'show_legend',
                'legend',
                ('legend_title','legend_subtitle')
            )
        }),
        ('LINKS', {
            'classes': ('collapse',),
            'fields': (
                ('metadata','source'),
                ('bookmark', 'kml'),
                ('data_download','learn_more'),
                ('map_tiles'),
            )
        }),
        ('SHARING', {
            'classes': ('collapse',),
            'fields': (
                'shareable_url',
            )
        }),
        ('ArcGIS DETAILS', {
            'classes': ('collapse',),
            'fields': (
                ('arcgis_layers', 'query_by_point', 'disable_arcgis_attributes'),
            )
        }),
        ('WMS DETAILS', {
            'classes': ('collapse',),
            'fields': (
                'wms_help',
                ('wms_slug', 'wms_version'),
                ('wms_format', 'wms_srs'),
                ('wms_timing', 'wms_time_item'),
                ('wms_styles', 'wms_additional'),
                ('wms_info', 'wms_info_format'),
            )
        }),
        ('Dynamic Layers (MDAT & CAS)', {
            'classes': ('collapse',),
            'fields': (
                'search_query',
            )
        }),
        ('UTF Grid Layers', {
            'classes': ('collapse',),
            'fields': (
                'utfurl',
            )
        }),
        ('ATTRIBUTE REPORTING', {
            'classes': ('collapse',),
            'fields': (
                ('label_field'),
                ('attribute_event', 'attribute_fields'),
                ('mouseover_field'),
                ('is_annotated', 'compress_display'),
            )
        }),
        ('DISPLAY & STYLE', {
            'classes': ('collapse',),
            'fields': (
                'opacity',
                (
                    'minZoom',
                    'maxZoom'
                ),
                'custom_style',
                (
                    'vector_outline_width',
                    'vector_outline_color', 
                    # 'vector_outline_opacity',
                ),
                (
                    'vector_fill',
                    'vector_color', 
                ),
                (
                    'point_radius',
                    'vector_graphic',
                    'vector_graphic_scale',
                ),
                (
                    'lookup_field',
                    'lookup_table',
                ),
                # 'thumbnail',
            )
        }),
        ('ESPIS', {
            'classes': ('collapse',),
            'fields': (
                ('espis_enabled', 'espis_region'),
                ('espis_search' ),
            )
        }),
    )

    inlines = [
        NestedMultilayerAssociationInline,
        NestedMultilayerDimensionInline,
    ]

    from . import settings as data_manager_settings
    BASE_DIR = data_manager_settings.DATA_MANAGER_BASE_DIR
    add_form_template = '%s/data_manager/templates/admin/LayerForm.html' % BASE_DIR
    change_form_template = '%s/data_manager/templates/admin/LayerForm.html' % BASE_DIR

    def Theme_(self, obj):
        return obj.themes.first()

    Theme_.admin_order_field = 'themes'

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'attribute_fields':
            kwargs['queryset'] = AttributeInfo.objects.order_by('field_name')
        elif db_field.name == 'sublayers':
            kwargs['queryset'] = Layer.objects.order_by('name')
        elif db_field.name == 'themes':
            kwargs['queryset'] = Theme.objects.order_by('name')
        elif db_field.name == 'lookup_table':
            kwargs['queryset'] = LookupInfo.objects.order_by('value')
        elif db_field.name == 'site':
            kwargs['widget'] = forms.CheckboxSelectMultiple()
            kwargs['widget'].attrs['style'] = 'list-style-type: none;'
            kwargs['widget'].can_add_related = False
            return db_field.formfield(**kwargs)

        return super(LayerAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)

    # New Layer Form
    def add_view(self, request, form_url='', extra_context={}):
        extra_context['CATALOG_TECHNOLOGY'] = settings.CATALOG_TECHNOLOGY
        extra_context['CATALOG_PROXY'] = settings.CATALOG_PROXY
        return super(LayerAdmin, self).add_view(request, form_url, extra_context)

    # Edit Layer Form
    def change_view(self, request, object_id, extra_context={}):
        extra_context['CATALOG_TECHNOLOGY'] = settings.CATALOG_TECHNOLOGY
        extra_context['CATALOG_PROXY'] = settings.CATALOG_PROXY
        return super(LayerAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def get_queryset(self, request):
        # use our manager, rather than the default one
        qs = self.model.all_objects.get_queryset()

        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

class AttributeInfoAdmin(admin.ModelAdmin):
    list_display = ('field_name', 'display_name', 'precision', 'order', 'preserve_format')

class LookupInfoAdmin(admin.ModelAdmin):
    list_display = ('value', 'description', 'color', 'stroke_color', 'dashstyle', 'fill', 'graphic')

class DataNeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')



if hasattr(settings, 'DATA_MANAGER_ADMIN'):
    admin.site.register(Theme, ThemeAdmin)
    admin.site.register(Layer, LayerAdmin)
    admin.site.register(AttributeInfo, AttributeInfoAdmin)
    admin.site.register(LookupInfo, LookupInfoAdmin)
    admin.site.register(DataNeed, DataNeedAdmin)
    admin.site.register(ExternalPortal)
