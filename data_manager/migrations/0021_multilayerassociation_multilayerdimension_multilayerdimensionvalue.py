# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


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
                ('layer', models.ForeignKey(default=None, blank=True, to='data_manager.Layer', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MultilayerDimension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(help_text=b'name to be used for selection in admin tool forms', max_length=200)),
                ('label', models.CharField(help_text=b'label to be used in mapping tool slider', max_length=50)),
                ('order', models.IntegerField(default=100, help_text=b'the order in which this dimension will be presented among other dimensions on this layer')),
                ('animated', models.BooleanField(default=False, help_text=b'enable auto-toggling of layers across this dimension')),
                ('layer', models.ForeignKey(to='data_manager.Layer')),
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
                ('value', models.CharField(help_text=b'Actual value of selection', max_length=200)),
                ('label', models.CharField(help_text=b'Label for this selection seen in mapping tool slider', max_length=50)),
                ('order', models.IntegerField(default=100)),
                ('associations', models.ManyToManyField(to='data_manager.MultilayerAssociation')),
                ('dimension', models.ForeignKey(to='data_manager.MultilayerDimension')),
            ],
            options={
                'ordering': ('order',),
            },
            bases=(models.Model,),
        ),
    ]
