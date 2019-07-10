# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0006_auto_20160304_0025'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='layer',
            name='order_num',
        ),
        migrations.RemoveField(
            model_name='theme',
            name='order_num',
        ),
        migrations.AddField(
            model_name='layer',
            name='order',
            field=models.PositiveSmallIntegerField(default=10, help_text='input an integer to determine the priority/order of the layer being displayed (1 being the highest)', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='theme',
            name='order',
            field=models.PositiveSmallIntegerField(default=10, help_text='input an integer to determine the priority/order of the layer being displayed (1 being the highest)', null=True, blank=True),
            preserve_default=True,
        ),
    ]
