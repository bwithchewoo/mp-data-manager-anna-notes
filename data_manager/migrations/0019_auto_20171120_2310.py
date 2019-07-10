# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0018_layer_data_publish_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='layer',
            name='data_publish_date',
            field=models.DateField(default=None, help_text='YYYY-MM-DD', null=True, verbose_name='Date published', blank=True),
            preserve_default=True,
        ),
    ]
