# Generated by Django 4.1.5 on 2023-02-03 19:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('patient', '0004_label_category'),
    ]

    operations = [
        migrations.RenameField(
            model_name='label',
            old_name='Category',
            new_name='category',
        ),
    ]
