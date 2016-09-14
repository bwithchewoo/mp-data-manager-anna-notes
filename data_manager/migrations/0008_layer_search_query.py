# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0007_auto_20160304_0057'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='search_query',
            field=models.BooleanField(default=False, help_text=b'Select when layers are queryable - e.g. MDAT and CAS'),
            preserve_default=True,
        ),
    ]
