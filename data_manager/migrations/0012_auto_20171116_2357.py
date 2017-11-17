# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0011_auto_20170723_2036'),
    ]

    operations = [
        migrations.AddField(
            model_name='layer',
            name='site_migrate',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='wms_additional',
            field=models.TextField(help_text=b'additional WMS key-value pairs: &key=value...', null=True, verbose_name=b'WMS Additional Fields', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='wms_format',
            field=models.CharField(help_text=b'most common: image/png. Only image types supported.', max_length=100, null=True, verbose_name=b'WMS Format', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='wms_help',
            field=models.BooleanField(default=False, help_text=b'Enable simple selection for WMS fields. Only supports WMS 1.1.1'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='wms_srs',
            field=models.CharField(help_text=b'If not EPSG:3857 WMS requests will be proxied', max_length=100, null=True, verbose_name=b'WMS SRS', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='wms_styles',
            field=models.CharField(help_text=b'pre-determined styles, if exist', max_length=255, null=True, verbose_name=b'WMS Styles', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='wms_time_item',
            field=models.CharField(help_text=b'Time Attribute Field, if different from "TIME". Proxy only.', max_length=255, null=True, verbose_name=b'WMS Time Field', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='wms_timing',
            field=models.CharField(help_text=b'http://docs.geoserver.org/stable/en/user/services/wms/time.html#specifying-a-time', max_length=255, null=True, verbose_name=b'WMS Time', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='theme',
            name='site_migrate',
            field=models.CharField(max_length=255, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='layer',
            name='wms_slug',
            field=models.CharField(max_length=255, null=True, verbose_name=b'WMS Layer Name', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='layer',
            name='wms_version',
            field=models.CharField(blank=True, max_length=10, null=True, help_text=b'WMS Versioning - usually either 1.1.1 or 1.3.0', choices=[(None, b''), (b'1.0.0', b'1.0.0'), (b'1.1.0', b'1.1.0'), (b'1.1.1', b'1.1.1'), (b'1.3.0', b'1.3.0')]),
            preserve_default=True,
        ),
    ]
