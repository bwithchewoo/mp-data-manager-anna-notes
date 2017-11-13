# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0012_auto_20171111_0122'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='wms_time_item',
            field=models.CharField(help_text=b'Time Attribute Field, if different from "TIME"', max_length=255, null=True, verbose_name=b'WMS Time Field', blank=True),
            preserve_default=True,
        ),
    ]
