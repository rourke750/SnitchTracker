# Generated by Django 2.0.6 on 2018-06-17 17:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('snitches', '0008_auto_20180615_1736'),
    ]

    operations = [
        migrations.AddField(
            model_name='snitch_record',
            name='type',
            field=models.CharField(choices=[(0, 'Entered'), (1, 'Logged in'), (2, 'Logged out')], default=None, max_length=2),
        ),
        migrations.AddField(
            model_name='snitch_record',
            name='user',
            field=models.CharField(default=None, max_length=16),
            preserve_default=False,
        ),
    ]
