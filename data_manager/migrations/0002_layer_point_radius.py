# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='point_radius',
            field=models.IntegerField(help_text='Used only for for Point layers (default is 2)', null=True, blank=True),
            preserve_default=True,
        ),
    ]
