# Generated by Django 4.2.16 on 2024-10-10 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sitescrapers', '0002_alter_property_agent_alter_property_house_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='scrapingjob',
            name='property',
        ),
        migrations.AddField(
            model_name='scrapingjob',
            name='callback_url',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scrapingjob',
            name='property_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='scrapingjob',
            name='source',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='scrapingjob',
            name='task_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
