# Generated by Django 3.1.5 on 2021-02-12 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0043_auto_20210211_1116'),
    ]

    operations = [
        migrations.AddField(
            model_name='crawlinglog',
            name='crawl_id',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
