# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0016_auto_20171117_0020'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='layer',
            name='site_migrate',
        ),
        migrations.RemoveField(
            model_name='theme',
            name='site_migrate',
        ),
    ]
