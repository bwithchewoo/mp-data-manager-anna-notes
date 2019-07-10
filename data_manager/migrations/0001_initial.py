# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AttributeInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_name', models.CharField(max_length=255, null=True, blank=True)),
                ('field_name', models.CharField(max_length=255, null=True, blank=True)),
                ('precision', models.IntegerField(null=True, blank=True)),
                ('order', models.IntegerField(default=1)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DataNeed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('archived', models.BooleanField(default=False)),
                ('description', models.TextField(null=True, blank=True)),
                ('source', models.CharField(max_length=255, null=True, blank=True)),
                ('status', models.TextField(null=True, blank=True)),
                ('contact', models.CharField(max_length=255, null=True, blank=True)),
                ('contact_email', models.CharField(max_length=255, null=True, blank=True)),
                ('expected_date', models.CharField(max_length=255, null=True, blank=True)),
                ('notes', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Layer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug_name', models.CharField(max_length=100, null=True, blank=True)),
                ('layer_type', models.CharField(help_text='use placeholder to temporarily remove layer from TOC', max_length=50, choices=[('XYZ', 'XYZ'), ('WMS', 'WMS'), ('ArcRest', 'ArcRest'), ('radio', 'radio'), ('checkbox', 'checkbox'), ('Vector', 'Vector'), ('placeholder', 'placeholder')])),
                ('url', models.CharField(max_length=255, null=True, blank=True)),
                ('shareable_url', models.BooleanField(default=True, help_text='Indicates whether the data layer (e.g. map tiles) can be shared with others (through the Map Tiles Link)')),
                ('arcgis_layers', models.CharField(help_text='comma separated list of arcgis layer IDs', max_length=255, null=True, blank=True)),
                ('is_sublayer', models.BooleanField(default=False)),
                ('is_disabled', models.BooleanField(default=False, help_text='when disabled, the layer will still appear in the TOC, only disabled')),
                ('disabled_message', models.CharField(max_length=255, null=True, blank=True)),
                ('legend', models.CharField(help_text='URL or path to the legend image file', max_length=255, null=True, blank=True)),
                ('legend_title', models.CharField(help_text='alternative to using the layer name', max_length=255, null=True, blank=True)),
                ('legend_subtitle', models.CharField(max_length=255, null=True, blank=True)),
                ('utfurl', models.CharField(max_length=255, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('data_overview', models.TextField(null=True, blank=True)),
                ('data_source', models.CharField(max_length=255, null=True, blank=True)),
                ('data_notes', models.TextField(null=True, blank=True)),
                ('bookmark', models.CharField(help_text='link to view data layer in the planner', max_length=755, null=True, blank=True)),
                ('kml', models.CharField(help_text='link to download the KML', max_length=255, null=True, blank=True)),
                ('data_download', models.CharField(help_text='link to download the data', max_length=255, null=True, blank=True)),
                ('learn_more', models.CharField(help_text='link to view description in the Learn section', max_length=255, null=True, blank=True)),
                ('metadata', models.CharField(help_text='link to view/download the metadata', max_length=255, null=True, blank=True)),
                ('source', models.CharField(help_text='link back to the data source', max_length=255, null=True, blank=True)),
                ('map_tiles', models.CharField(help_text='internal link to a page that details how others might consume the data', max_length=255, null=True, blank=True)),
                ('thumbnail', models.URLField(help_text='not sure we are using this any longer...', max_length=255, null=True, blank=True)),
                ('compress_display', models.BooleanField(default=False)),
                ('attribute_event', models.CharField(default='click', max_length=35, choices=[('click', 'click'), ('mouseover', 'mouseover')])),
                ('mouseover_field', models.CharField(help_text='feature level attribute used in mouseover display', max_length=75, null=True, blank=True)),
                ('lookup_field', models.CharField(max_length=255, null=True, blank=True)),
                ('is_annotated', models.BooleanField(default=False)),
                ('vector_outline_color', models.CharField(max_length=7, null=True, blank=True)),
                ('vector_outline_opacity', models.FloatField(null=True, blank=True)),
                ('vector_color', models.CharField(max_length=7, null=True, blank=True)),
                ('vector_fill', models.FloatField(null=True, blank=True)),
                ('vector_graphic', models.CharField(max_length=255, null=True, blank=True)),
                ('opacity', models.FloatField(default=0.5, null=True, blank=True)),
                ('attribute_fields', models.ManyToManyField(to='data_manager.AttributeInfo', null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LookupInfo',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(max_length=255, null=True, blank=True)),
                ('color', models.CharField(max_length=7, null=True, blank=True)),
                ('dashstyle', models.CharField(default='solid', max_length=11, choices=[('dot', 'dot'), ('dash', 'dash'), ('dashdot', 'dashdot'), ('longdash', 'longdash'), ('longdashdot', 'longdashdot'), ('solid', 'solid')])),
                ('fill', models.BooleanField(default=False)),
                ('graphic', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('display_name', models.CharField(max_length=100)),
                ('name', models.CharField(max_length=100)),
                ('visible', models.BooleanField(default=True)),
                ('header_image', models.CharField(max_length=255, null=True, blank=True)),
                ('header_attrib', models.CharField(max_length=255, null=True, blank=True)),
                ('overview', models.TextField(null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('thumbnail', models.URLField(max_length=255, null=True, blank=True)),
                ('factsheet_thumb', models.CharField(max_length=255, null=True, blank=True)),
                ('factsheet_link', models.CharField(max_length=255, null=True, blank=True)),
                ('feature_image', models.CharField(max_length=255, null=True, blank=True)),
                ('feature_excerpt', models.TextField(null=True, blank=True)),
                ('feature_link', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='layer',
            name='lookup_table',
            field=models.ManyToManyField(to='data_manager.LookupInfo', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='sublayers',
            field=models.ManyToManyField(related_name='sublayers_rel_+', null=True, to='data_manager.Layer', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='layer',
            name='themes',
            field=models.ManyToManyField(to='data_manager.Theme', null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='dataneed',
            name='themes',
            field=models.ManyToManyField(to='data_manager.Theme', null=True, blank=True),
            preserve_default=True,
        ),
    ]
