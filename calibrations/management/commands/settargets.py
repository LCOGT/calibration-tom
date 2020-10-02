import calendar
from datetime import datetime, timedelta
import random

from django.core.management.base import BaseCommand
from django.db.models import DateTimeField, ExpressionWrapper, F

from tom_targets.models import Target, TargetExtra
from tom_observations.models import DynamicCadence, ObservationGroup, ObservationRecord


CADENCE_DURATION = 3


class Command(BaseCommand):
    """
    Intended to be run monthly, this command creates the new cadence for a site.
    """

    help = 'Trigger an event at a specific site.'

    def add_arguments(self, parser):
        parser.add_argument('-s', '--site', help=self.sites, required=True)

    def get_eligible_targets(self, target_ids_to_exclude=[]):
        """
        Gets targets eligible to be selected for the next cadence window

        :param target_ids_to_exclude: List of target IDs to omit from the result
        :type target_ids_to_exclude: list of ints
        """

        now = datetime.now()
        cadence_end_datestamp = now + timedelta(month=CADENCE_DURATION)

        eligible_targets = []
        for target in Target.objects.exclude(
                                        id__in=target_ids_to_exclude
                                    ).filter(
                                        targetextra__key='nres_active_target', value=True
                                    ):
            # TODO: validate that there's only one of each TargetExtra
            target_seasonal_start = target.targetextra_set.filter(key='seasonal_start').first().float_value
            seasonal_start_year = now.year if now.month >= target_seasonal_start else now.year - 1
            seasonal_start_date = datetime(year=seasonal_start_year, month=target_seasonal_start, day=1)

            target_seasonal_end = target.targetextra_set.filter(key='seasonal_end').first().float_value
            seasonal_end_year = now.year if now.month <= target_seasonal_end else now.year + 1
            visible_window_length = datetime(
                year=seasonal_end_year,
                month=target_seasonal_end,
                day=calendar.monthrange(cadence_end_datestamp.year, target_seasonal_end)
            )[1] - now

            if seasonal_start_date <= now and visible_window_length > CADENCE_DURATION:
                eligible_targets.append(target)

        return eligible_targets

    def get_new_target(self, target_ids_to_exclude=[]):
        """
        Selects a target visible at the given site that will be visible for the next three months.

        :param target_ids_to_exclude: List of target IDs to omit from the result
        :type target_ids_to_exclude: list of ints
        """

        # seasonal_start must be in current month or prior
        # remaining time in the visibility window > CADENCE_DURATION
        # remaining time = seasonal_end - now >= CADENCE_DURATION

        # visible_window_length = ExpressionWrapper(
        #     datetime(year=now.year if now.month <= F('seasonal_end') else now.year + 1,
        #              month=F('seasonal_end'),
        #              day=calendar.monthrange(cadence_end_datestamp.year, F('seasonal_end'))[1]
        #              ) - datetime.now()
        # )

        # seasonal_end_date = ExpressionWrapper(
        #     datetime(year=now.year if now.month <= F('seasonal_end') else now.year + 1,
        #              month=F('seasonal_end'),
        #              day=calendar.monthrange(cadence_end_datestamp.year, F('seasonal_end'))[1]
        #              )
        # )

        # current date 6/1/2020
        # seasonal_end 11/30/2020 -> should be visible window length of 5 months
        # CADENCE_DURATION 7 months
        # 11/30/2021 -> actual visible window length = 17 months
        # should be invalid target, becomes eligible target

        # seasonal_end_dates = TargetExtra.objects.filter(key='seasonal_end')

        # eligible_targets = Target.objects.exclude(
        #                                     targets_to_exclude
        #                                 ).filter(
        #                                     targetextra__in=TargetExtra.objects.filter(key='nres_active_target', value=True)
        #                                 ).filter(
        #                                     targetextra__in=TargetExtra.objects.filter(key='seasonal_end')   
        #                                 )

        eligible_targets = self.get_eligible_targets(target_ids_to_exclude=target_ids_to_exclude)

        return eligible_targets[random.randint(0, len(eligible_targets)-1)]

    def handle(self, *args, **options):
        # Identify and get the correct DynamicCadence for a site
        # TODO: add "last_run" as a property for DynamicCadence
        cadence_for_site = DynamicCadence.objects.filter(cadence_parameters__site=options['site'], active=True)
        if len(cadence_for_site) == 0:
            raise Exception(f"No active cadence was found for site {options['site']}")
        elif len(cadence_for_site) > 1:
            raise Exception(f"More than one active cadence was found for site {options['site']}")
        else:
            cadence_for_site = cadence_for_site.first()

        # Check if the cadence is still valid
        # Check if the first run of the cadence was less than 3 months ago
        cadence_expired = (datetime.now - cadence_for_site.created) >= timedelta(month=CADENCE_DURATION)

        # If the cadence is still valid, do nothing
        if not cadence_expired:
            pass
        else:
            # If the cadence is no longer valid:
            # Find next target and create new cadence
            old_target = cadence_for_site.observation_group.observation_set.first().target
            new_target = self.get_new_target([old_target.id])
            new_dynamic_cadence = DynamicCadence.objects.create(
                cadence_strategy=cadence_for_site.cadence_strategy,
                cadence_parameters={'target_id': new_target.id},
                observation_group=cadence_for_site.observation_group,
                active=True
            )
            cadence_for_site.active = False
            cadence_for_site.save()
