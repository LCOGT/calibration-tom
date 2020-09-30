from django.core.management.base import BaseCommand
from django.db.models import Q

from tom_targets.models import Target, TargetExtra
from tom_observations.models import DynamicCadence, ObservationGroup, ObservationRecord


DynamicCadence.objects.create(
    observation_group=og,
    cadence_strategy='NRESCalibrationCadence',
    active=True,
    cadence_parameters={
        'site': 'cpt',
        'target_id': 1,
        'period': 120
    }
)


class Command(BaseCommand):
    """
    Intended to be run monthly, this command creates the new cadence for a site.
    """

    help = 'Trigger an event at a specific site.'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--site', help=self.sites, required=True)

    def handle(self, *args, **options):
        # Identify and get the correct DynamicCadence for a site
        target_for_site = Target.objects.filter(
            targetextra__in=Q(TargetExtra.objects.filter(key='site', value=options['site']) |
                              TargetExtra.objects.filter(key='nres_active_target', value=True))
        ).first() # This assumes that there's only one
        most_recent_obs_for_target = ObservationRecord.objects.filter(target=target_for_site).order_by('-created').first()
        observation_group_for_cadence = ObservationGroup.objects.filter(observation_set__contains=most_recent_obs_for_target, dynamiccadence_set__contains(DynamicCadence.objects.filter(cadence_strategy='NRESCalibrationCadence'))).first()

        DynamicCadence.objects.filter(cadence_parameters__site='cpt', active=True).observation_group

        old_dynamic_cadence = DynamicCadence.objects.first()

        # Check if the cadence is still valid

        # If the cadence is still valid, do nothing
        
        # If the cadence is no longer valid:
        new_dynamic_cadence = DynamicCadence.objects.create(
            cadence_strategy=old_dynamic_cadence,
            cadence_parameters={'target_id': new_target.id},
            observation_group=old_dynamic_cadence.observation_group, active=True
        )
        old_dynamic_cadence.active = False
        old_dynamic_cadence.save()
