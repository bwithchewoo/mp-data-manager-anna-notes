# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0013_auto_20171116_2358'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='layersite',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='layersite',
            name='layer',
        ),
        migrations.RemoveField(
            model_name='layersite',
            name='site',
        ),
        migrations.AlterUniqueTogether(
            name='themesite',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='themesite',
            name='site',
        ),
        migrations.RemoveField(
            model_name='themesite',
            name='theme',
        ),
        migrations.RemoveField(
            model_name='layer',
            name='site',
        ),
        migrations.DeleteModel(
            name='LayerSite',
        ),
        migrations.RemoveField(
            model_name='theme',
            name='site',
        ),
        migrations.DeleteModel(
            name='ThemeSite',
        ),
    ]
