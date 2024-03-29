# Generated by Django 3.1.5 on 2021-01-24 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flat_crawler', '0006_flatpost_post_hash'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostHash',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.CharField(choices=[('OTO', 'Otodom'), ('GT', 'Gumtree'), ('OLX', 'Olx'), ('DP', 'Domiporta'), ('MZN', 'Morizon'), ('WAW_N', 'Waw Nieruchomosci'), ('ADA', 'Ada'), ('GTK', 'Gratka'), ('ADS', 'Adresowo'), ('OKO', 'Okolica')], max_length=6)),
                ('post_hash', models.CharField(max_length=64)),
            ],
        ),
    ]
