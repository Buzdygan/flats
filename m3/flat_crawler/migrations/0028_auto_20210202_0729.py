# Generated by Django 3.1.5 on 2021-02-02 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0027_imagematch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flatpost',
            name='size_m2',
            field=models.FloatField(null=True),
        ),
    ]
