# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0021_multilayerassociation_multilayerdimension_multilayerdimensionvalue'),
    ]

    operations = [
        migrations.AddField(
            model_name='multilayerassociation',
            name='parentLayer',
            field=models.ForeignKey(related_name='parent_layer', db_column=b'parentlayer', default=1, to='data_manager.Layer'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='multilayerassociation',
            name='layer',
            field=models.ForeignKey(related_name='associated_layer', db_column=b'associatedlayer', default=None, blank=True, to='data_manager.Layer', null=True),
            preserve_default=True,
        ),
    ]
