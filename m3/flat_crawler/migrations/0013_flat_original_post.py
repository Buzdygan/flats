# Generated by Django 3.1.5 on 2021-01-28 08:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0012_auto_20210124_2323'),
    ]

    operations = [
        migrations.AddField(
            model_name='flat',
            name='original_post',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='flat_crawler.flatpost'),
            preserve_default=False,
        ),
    ]