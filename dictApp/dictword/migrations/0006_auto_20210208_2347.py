# Generated by Django 3.1.6 on 2021-02-08 20:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dictword', '0005_auto_20210208_2152'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dictword',
            old_name='partOfSpeech',
            new_name='part_of_speech',
        ),
    ]