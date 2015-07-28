# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0003_auto_20150709_2140'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='wms_slug',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
