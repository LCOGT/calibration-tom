from datetime import datetime, timedelta
import json
import random

from django.core.files import File
from django.core.management.base import BaseCommand

from tom_targets.models import Target
from tom_observations.models import ObservationRecord
from tom_dataproducts.models import DataProduct, ReducedDatum


class Command(BaseCommand):
    """
    Generates ObservationRecords and corresponding DataProducts and ReducedDatums for RV Standards for testing purposes.
    """

    def add_arguments(self, parser):
        parser.add_argument('target_id', nargs=1, type=int)
        parser.add_argument('test_file', nargs=1, type=str)
        parser.add_argument('--num_records', help='Number of observation records to generate')

    def handle(self, *args, **options):
        print(options)
        t = Target.objects.get(pk=options['target_id'][0])
        test_file = options['test_file'][0]
        num_records = options['num_records'] if options['num_records'] else 9

        for i in range(0, num_records):
            obs_date = datetime(
                2020, 12, 17, random.randrange(24), random.randrange(60), random.randrange(60)
            ) - timedelta(days=i)
            obsr = ObservationRecord.objects.create(target=t, facility='LCO Calibrations', status='COMPLETED',
                                                    scheduled_start=obs_date)
            with open(test_file, 'rb') as f:
                dp = DataProduct.objects.create(target=t, observation_record=obsr, data_product_type='nres_rv',
                                                data=File(f))
            _ = ReducedDatum.objects.create(target=t,
                                            data_product=dp,
                                            timestamp=obs_date,
                                            data_type='nres_rv',
                                            value=json.dumps({'radial_velocity': random.uniform(8, 9)}))
