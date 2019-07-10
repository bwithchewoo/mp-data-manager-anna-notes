# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0004_layer_wms_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='wms_version',
            field=models.CharField(help_text='WMS Versioning - usually either 1.1.1 or 1.3.0', max_length=10, null=True, blank=True),
            preserve_default=True,
        ),
    ]
