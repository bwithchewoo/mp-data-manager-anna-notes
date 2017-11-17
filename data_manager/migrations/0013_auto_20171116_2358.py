# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def migrate_site_data(apps, schema_editor):
    Layer = apps.get_model("data_manager", "Layer")
    Theme = apps.get_model("data_manager", "Theme")
    ThemeSite = apps.get_model("data_manager", "ThemeSite")
    LayerSite = apps.get_model("data_manager", "LayerSite")
    for layer_site in LayerSite.objects.all():
        layer = layer_site.layer
        if not layer.site_migrate or len(layer.site_migrate) == 0:
            layer_sites = []
        else:
            layer_sites = eval(layer.site_migrate)
        layer_sites.append(layer_site.site.pk)
        layer.site_migrate = str(layer_sites)
        layer.save()
    for theme_site in ThemeSite.objects.all():
        theme = theme_site.theme
        if not theme.site_migrate or len(theme.site_migrate) == 0:
            theme_sites = []
        else:
            theme_stires = eval(theme.site_migrate)
        theme_sites.append(theme_site.site.pk)
        theme.site_migrate = str(theme_sites)
        theme.save()

class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0012_auto_20171116_2357'),
    ]

    operations = [
        migrations.RunPython(migrate_site_data),
    ]
