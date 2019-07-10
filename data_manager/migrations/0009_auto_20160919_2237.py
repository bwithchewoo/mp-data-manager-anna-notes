# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0008_layer_search_query'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='connect_companion_layers_to',
            field=models.ManyToManyField(help_text='Select which main layer(s) you would like to use in conjuction with this companion layer.', related_name='connect_companion_layers_to_rel_+', null=True, to='data_manager.Layer', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='has_companion',
            field=models.BooleanField(default=False, help_text='Check if this layer has a companion layer'),
            preserve_default=True,
        ),
    ]
