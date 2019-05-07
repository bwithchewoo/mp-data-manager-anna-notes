from django.contrib import admin
from django import forms
from models import *
import nested_admin

from import_export import fields, resources
from import_export.admin import ImportExportMixin

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
    fields = (('name', 'label', 'order', 'animated'),)
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
    class Meta:
        model = Layer
        widgets = {
            'themes': admin.widgets.FilteredSelectMultiple('Themes', False),
            'sublayers': admin.widgets.FilteredSelectMultiple('Sublayers', False),
            'connect_companion_layers_to': admin.widgets.FilteredSelectMultiple('Connect companion layers to', False),
            'attribute_fields': admin.widgets.FilteredSelectMultiple('Attribute fields', False),
            'lookup_table': admin.widgets.FilteredSelectMultiple('Lookup table', False),
        }

class LayerAdmin(ImportExportMixin, nested_admin.NestedModelAdmin):
    resource_class = LayerResource
    form = LayerForm
    list_display = ('name', 'layer_type', 'Theme_', 'order', 'data_publish_date', 'data_source', 'primary_site', 'preview_site', 'url')
    search_fields = ['name', 'layer_type', 'url', 'data_source']
    ordering = ('name',)
    exclude = ('slug_name',)

    fieldsets = (
        ('BASIC INFO', {
            'fields': (
                ('name','layer_type'),
                'url',
                'site'
            )
        }),
        ('LAYER ORGANIZATION', {
            'fields': (
                ('order','themes'),
                ('is_sublayer','sublayers'),
                ('has_companion','connect_companion_layers_to'),
                ('is_disabled','disabled_message')
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
                ('arcgis_layers', 'disable_arcgis_attributes'),
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
                ('attribute_event', 'attribute_fields'),
                ('lookup_field', 'lookup_table'),
                ('mouseover_field'),
                ('is_annotated', 'compress_display'),
            )
        }),
        ('STYLE', {
            'classes': ('collapse',),
            'fields': (
                ('opacity'),
                ('vector_outline_color', 'vector_outline_opacity'),
                ('vector_color', 'vector_fill'),
                ('vector_graphic'),
                ('point_radius'),
                'thumbnail',
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

    from settings import BASE_DIR
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
        # extra_context['test'] = 'BAR'
        return super(LayerAdmin, self).add_view(request, form_url, extra_context)

    # Edit Layer Form
    def change_view(self, request, id=None, extra_context={}):
        # extra_context['test'] = 'BAR'
        return super(LayerAdmin, self).change_view(request, id, extra_context=extra_context)

    def get_queryset(self, request):
        # use our manager, rather than the default one
        qs = self.model.all_objects.get_queryset()

        # we need this from the superclass method
        ordering = self.ordering or () # otherwise we might try to *None, which is bad ;)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

class AttributeInfoAdmin(admin.ModelAdmin):
    list_display = ('field_name', 'display_name', 'precision', 'order')

class LookupInfoAdmin(admin.ModelAdmin):
    list_display = ('value', 'color', 'dashstyle', 'fill', 'graphic')

class DataNeedAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

admin.site.register(Theme, ThemeAdmin)
admin.site.register(Layer, LayerAdmin)
admin.site.register(AttributeInfo, AttributeInfoAdmin)
admin.site.register(LookupInfo, LookupInfoAdmin)
admin.site.register(DataNeed, DataNeedAdmin)
