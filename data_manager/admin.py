from django.contrib import admin
from django import forms
from models import *

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

class LayerResource(resources.ModelResource):
    class Meta:
        model = Layer

class LayerAdmin(ImportExportMixin, admin.ModelAdmin):
    resource_class = LayerResource
    list_display = ('name', 'layer_type', 'Theme_', 'order', 'url', 'primary_site', 'preview_site')
    search_fields = ['name', 'layer_type']
    ordering = ('name',)
    exclude = ('slug_name',)

    from marco.settings import BASE_DIR
    add_form_template = '%s/../apps/mp-data-manager/data_manager/templates/admin/LayerForm.html' % BASE_DIR
    change_form_template = '%s/../apps/mp-data-manager/data_manager/templates/admin/LayerForm.html' % BASE_DIR

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
