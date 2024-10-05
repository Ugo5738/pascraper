# Generated by Django 5.0.7 on 2024-09-23 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_loginhistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='auth_provider',
            field=models.CharField(choices=[('email', 'Email'), ('google', 'Google')], default='email', max_length=20),
        ),
    ]
