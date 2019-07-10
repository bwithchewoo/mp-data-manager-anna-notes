# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0021_multilayerassociation_multilayerdimension_multilayerdimensionvalue'),
    ]

    operations = [
        migrations.AddField(
            model_name='multilayerassociation',
            name='parentLayer',
            field=models.ForeignKey(related_name='parent_layer', db_column='parentlayer', default=1, to='data_manager.Layer', on_delete=django.db.models.deletion.SET_DEFAULT),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='multilayerassociation',
            name='layer',
            field=models.ForeignKey(related_name='associated_layer', db_column='associatedlayer', default=None, blank=True, to='data_manager.Layer', null=True, on_delete=django.db.models.deletion.SET_NULL),
            preserve_default=True,
        ),
    ]
