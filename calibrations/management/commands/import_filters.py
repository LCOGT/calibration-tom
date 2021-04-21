import csv
import logging

from django.core.management.base import BaseCommand
from targeted_calibrations.models import Filter

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Generates ObservationRecords and corresponding DataProducts and ReducedDatums for RV Standards for testing purposes.
    """

    def add_arguments(self, parser):
        parser.add_argument('filter_csv_file_path', nargs=1, type=str)

    def handle(self, *args, **options):
        csv_file_path = options['filter_csv_file_path'][0]
        logger.setLevel(options['verbosity'])

        logger.info(f'Importing Filters from {csv_file_path}')
        with open(csv_file_path) as fp:
            reader = csv.reader(fp)
            next(reader, None)  # skip the headers

            data_line_count = 0
            created_filter_count = 0
            for line in reader:
                if not line:
                    logger.debug(f'skipping blank line')
                    continue  # skip blank lines

                logger.debug(f'line: {line}')
                data_line_count += 1
                optical_filter, created = Filter.objects.get_or_create(
                    name=line[0],
                    exposure_time=float(line[1]),
                    exposure_count=int(line[2]),
                )
                logger.debug(f'{optical_filter} {"created" if created else "found"}')
                if created:
                    created_filter_count += 1
                # creates a tuple of the new object or
                # current object and a boolean of if it was created
        logger.info(f'Created {created_filter_count} new filters from {data_line_count} lines of filter data.')
