# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('data_manager', '0019_auto_20171120_2310'),
    ]

    operations = [
        migrations.CreateModel(
            name='MultilayerAssociation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('layer', models.ForeignKey(default=None, blank=True, to='data_manager.Layer', null=True, on_delete=django.db.models.deletion.SET_NULL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilayerDimension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text='name to be used for selection in admin tool forms', max_length=200)),
                ('label', models.CharField(help_text='label to be used in mapping tool slider', max_length=50)),
                ('order', models.IntegerField(default=100, help_text='the order in which this dimension will be presented among other dimensions on this layer')),
                ('animated', models.BooleanField(default=False, help_text='enable auto-toggling of layers across this dimension')),
                ('layer', models.ForeignKey(to='data_manager.Layer', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilayerDimensionValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.CharField(help_text='Actual value of selection', max_length=200)),
                ('label', models.CharField(help_text='Label for this selection seen in mapping tool slider', max_length=50)),
                ('order', models.IntegerField(default=100)),
                ('associations', models.ManyToManyField(to='data_manager.MultilayerAssociation')),
                ('dimension', models.ForeignKey(to='data_manager.MultilayerDimension', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
    ]
