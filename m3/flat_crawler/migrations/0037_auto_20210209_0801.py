# Generated by Django 3.1.5 on 2021-02-09 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0036_auto_20210208_2320'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='lat',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='lng',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='location',
            name='location_type',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
