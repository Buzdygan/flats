# Generated by Django 3.1.5 on 2021-02-06 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0031_remove_flatpost_photos_signature_json'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('city', models.CharField(max_length=50, null=True)),
                ('full_name', models.CharField(max_length=80, null=True)),
                ('by_name', models.CharField(max_length=80, null=True)),
                ('short_name', models.CharField(max_length=80, null=True)),
                ('district_local_name', models.CharField(max_length=50, null=True)),
                ('geolocation_json', models.TextField(null=True)),
                ('ne_lat', models.FloatField(null=True)),
                ('ne_lng', models.FloatField(null=True)),
                ('sw_lat', models.FloatField(null=True)),
                ('sw_lng', models.FloatField(null=True)),
            ],
        ),
    ]
