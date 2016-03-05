# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-03-05 16:13
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ABET_DB', '0011_auto_20160305_1449'),
    ]

    operations = [
        migrations.RenameField(
            model_name='courses',
            old_name='courseDescription',
            new_name='description',
        ),
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