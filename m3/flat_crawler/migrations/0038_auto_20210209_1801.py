# Generated by Django 3.1.5 on 2021-02-09 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0037_auto_20210209_0801'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='location_type',
        ),
        migrations.AddField(
            model_name='location',
            name='location_types',
            field=models.TextField(max_length=100, null=True),
        ),
    ]
