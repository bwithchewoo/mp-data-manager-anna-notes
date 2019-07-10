# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0010_layer_disable_arcgis_attributes'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='espis_enabled',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='espis_region',
            field=models.CharField(blank=True, max_length=100, null=True, help_text='Region to search within', choices=[('Mid Atlantic', 'Mid Atlantic')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='espis_search',
            field=models.CharField(help_text='keyphrase search for ESPIS Link', max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
