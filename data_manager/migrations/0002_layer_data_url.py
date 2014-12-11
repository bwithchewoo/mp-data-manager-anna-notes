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
            name='data_url',
            field=models.URLField(help_text=b'Link to the data catalog', max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
    ]
