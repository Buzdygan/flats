# Generated by Django 3.1.5 on 2021-01-24 14:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0008_auto_20210124_1240'),
    ]

    operations = [
        migrations.AlterField(
            model_name='flat',
            name='size_m2',
            field=models.DecimalField(decimal_places=2, max_digits=7, null=True),
        ),
        migrations.AlterField(
            model_name='flatpost',
            name='size_m2',
            field=models.DecimalField(decimal_places=2, max_digits=7, null=True),
        ),
    ]
