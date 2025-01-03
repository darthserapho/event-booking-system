# Generated by Django 5.1.3 on 2024-12-01 12:33

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventapp', '0009_booking_is_paid_booking_is_refunded'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ticket',
            name='attendee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to=settings.AUTH_USER_MODEL),
        ),
    ]
