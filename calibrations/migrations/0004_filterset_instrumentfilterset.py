# Generated by Django 4.2.10 on 2024-10-23 22:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('calibrations', '0003_filter_instrument_instrumentfilter'),
    ]

    operations = [
        migrations.CreateModel(
            name='FilterSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filter_set_code', models.ManyToManyField(to='calibrations.filter')),
            ],
        ),
        migrations.CreateModel(
            name='InstrumentFilterSet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_age', models.IntegerField(default=5)),
                ('filter_set', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calibrations.filterset')),
                ('instrument', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='calibrations.instrument')),
            ],
        ),
    ]
