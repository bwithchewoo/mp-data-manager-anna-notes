# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion

def reverse_m2ms(apps, schema_editor):
    # Do nothing, the M2M table will be destroyed
    pass

def add_default_m2m_relationships(apps, schema_editor):
    """After the m2m fields to Site are created, add M2M from each existing
    Layer and Theme to the "default" site (1).
    """
    Site = apps.get_model('sites', 'Site')
    Layer = apps.get_model('data_manager', 'Layer')
    LayerSite = apps.get_model('data_manager', 'LayerSite')
    Theme = apps.get_model('data_manager', 'Theme')
    ThemeSite = apps.get_model('data_manager', 'ThemeSite')

    try:
        site1 = Site.objects.get(id=1)
    except Site.DoesNotExist:
        site1 = Site(id=1, name='site one', domain='set-domain')
        site1.save()

    for layer in Layer.objects.all():
        LayerSite.objects.create(layer=layer, site=site1)

    for theme in Theme.objects.all():
        ThemeSite.objects.create(theme=theme, site=site1)


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('data_manager', '0002_layer_point_radius'),
    ]

    operations = [
        migrations.CreateModel(
            name='ThemeSite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('site', models.ForeignKey(to='sites.Site', on_delete=django.db.models.deletion.CASCADE)),
                ('theme', models.ForeignKey(to='data_manager.Theme', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='themesite',
            unique_together=set([('theme', 'site')]),
        ),
        migrations.AddField(
            model_name='theme',
            name='site',
            field=models.ManyToManyField(to='sites.Site', through='data_manager.ThemeSite'),
            preserve_default=True,
        ),



        migrations.CreateModel(
            name='LayerSite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('site', models.ForeignKey(to='sites.Site', on_delete=django.db.models.deletion.CASCADE)),
                ('layer', models.ForeignKey(to='data_manager.Layer', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={},
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='layersite',
            unique_together=set([('layer', 'site')]),
        ),
        migrations.AddField(
            model_name='layer',
            name='site',
            field=models.ManyToManyField(to='sites.Site', through='data_manager.LayerSite'),
            preserve_default=True,
        ),

        migrations.RunPython(add_default_m2m_relationships, reverse_m2ms)
    ]
