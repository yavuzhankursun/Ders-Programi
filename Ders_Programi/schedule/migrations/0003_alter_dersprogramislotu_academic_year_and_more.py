# Generated by Django 5.2 on 2025-05-05 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0002_alter_ders_ders_kodu'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dersprogramislotu',
            name='academic_year',
            field=models.CharField(max_length=20, verbose_name='Akademik Yıl'),
        ),
        migrations.AlterField(
            model_name='dersprogramislotu',
            name='semester',
            field=models.CharField(max_length=20, verbose_name='Dönem (Güz/Bahar)'),
        ),
    ]
