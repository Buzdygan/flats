# Generated by Django 3.1.5 on 2021-02-06 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0032_location'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='district_local_name',
        ),
        migrations.AddField(
            model_name='location',
            name='districts_local_names',
            field=models.TextField(null=True),
        ),
    ]