# Generated by Django 5.1.3 on 2024-11-24 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventapp', '0002_alter_ticketpricing_ticket_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='price_early_bird',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
    ]
