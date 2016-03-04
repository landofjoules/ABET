# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-03 23:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ABET_DB', '0006_auto_20160303_2332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseoutcomemap',
            name='studentOutcome',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='ABET_DB.studentOutcomes'),
        ),
        migrations.AlterField(
            model_name='outcomedata',
            name='studentOutcome',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='ABET_DB.studentOutcomes'),
        ),
    ]
