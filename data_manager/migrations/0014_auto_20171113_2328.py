# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0013_layer_wms_time_item'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='wms_help',
            field=models.BooleanField(default=False, help_text=b'Enable simple selection for WMS fields'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='layer',
            name='wms_time_item',
            field=models.CharField(help_text=b'Time Attribute Field, if different from "TIME". Proxy only.', max_length=255, null=True, verbose_name=b'WMS Time Field', blank=True),
            preserve_default=True,
        ),
    ]
