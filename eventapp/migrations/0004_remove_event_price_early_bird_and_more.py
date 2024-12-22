# Generated by Django 5.1.3 on 2024-11-24 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventapp', '0003_event_price_early_bird'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='price_early_bird',
        ),
        migrations.RemoveField(
            model_name='event',
            name='price_general',
        ),
        migrations.RemoveField(
            model_name='event',
            name='price_vip',
        ),
        migrations.RemoveField(
            model_name='event',
            name='tickets_available',
        ),
        migrations.AddField(
            model_name='ticket',
            name='price_early_bird',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticket',
            name='price_general',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ticket',
            name='price_vip',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='tickets_available',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='ticket',
            name='ticket_type',
            field=models.CharField(max_length=20),
        ),
        migrations.DeleteModel(
            name='TicketPricing',
        ),
    ]
