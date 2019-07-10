# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0017_auto_20171117_0041'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='data_publish_date',
            field=models.DateField(default=None, null=True, verbose_name='Date created/published', blank=True),
            preserve_default=True,
        ),
    ]
