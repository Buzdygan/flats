# Generated by Django 3.1.5 on 2021-02-02 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0029_imagematch_num_comparers_maybe_matched'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='imagematch',
            name='pos_id_1',
        ),
        migrations.RemoveField(
            model_name='imagematch',
            name='pos_id_2',
        ),
        migrations.AddField(
            model_name='imagematch',
            name='img_pos_1',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='imagematch',
            name='img_pos_2',
            field=models.IntegerField(null=True),
        ),
    ]
