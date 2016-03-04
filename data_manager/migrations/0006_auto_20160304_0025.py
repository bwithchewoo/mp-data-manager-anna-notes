# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0005_layer_wms_version'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='order_num',
            field=models.PositiveSmallIntegerField(default=10, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='theme',
            name='order_num',
            field=models.PositiveSmallIntegerField(default=10, null=True, blank=True),
            preserve_default=True,
        ),
    ]
