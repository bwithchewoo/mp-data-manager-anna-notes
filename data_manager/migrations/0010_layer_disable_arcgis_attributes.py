# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0009_auto_20160919_2237'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='disable_arcgis_attributes',
            field=models.BooleanField(default=False, help_text='Click to disable clickable ArcRest layers'),
            preserve_default=True,
        ),
    ]
