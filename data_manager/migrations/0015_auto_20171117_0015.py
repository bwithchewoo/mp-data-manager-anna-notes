# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('data_manager', '0014_auto_20171117_0014'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='site',
            field=models.ManyToManyField(to='sites.Site'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='theme',
            name='site',
            field=models.ManyToManyField(to='sites.Site'),
            preserve_default=True,
        ),
    ]
