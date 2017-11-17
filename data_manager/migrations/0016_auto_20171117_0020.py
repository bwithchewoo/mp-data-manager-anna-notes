# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def migrate_site_data2(apps, schema_editor):
    Site = apps.get_model("sites", "Site")
    Layer = apps.get_model("data_manager", "Layer")
    Theme = apps.get_model("data_manager", "Theme")
    for layer in Layer.objects.all():
        if layer.site_migrate:
            layer_sites = eval(layer.site_migrate)
            for site_pk in layer_sites:
                layer.site.add(Site.objects.get(pk=site_pk))
            layer.save()
    for theme in Theme.objects.all():
        if theme.site_migrate:
            theme_sites = eval(theme.site_migrate)
            for site_pk in theme_sites:
                theme.site.add(Site.objects.get(pk=site_pk))
            theme.save()

class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0015_auto_20171117_0015'),
    ]

    operations = [
        migrations.RunPython(migrate_site_data2),
    ]
