# Generated by Django 4.2.20 on 2025-04-20 23:13

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('planner', '0005_alter_vacationplan_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacationplan',
            name='shared_with',
            field=models.ManyToManyField(blank=True, related_name='shared_vacations', to=settings.AUTH_USER_MODEL),
        ),
    ]
