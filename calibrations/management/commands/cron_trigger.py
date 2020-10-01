from django.core.management.base import BaseCommand

from lcogt_logging import LCOGTFormatter
import logging
import logging.config

# TODO: move to settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            '()': LCOGTFormatter
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO'
        },
    }
}
logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)


class Command(BaseCommand):

    help = 'Trigger an event at a specific site.'
    _sites = ['COJ', 'TLV', 'CPT', 'SOR', 'LSC', 'ELP', 'BPL', 'SQA', 'TST', 'MFG', 'OGG']

    @property
    def sites(self):
        """
        A string listing the possible arguments to -s, --site
        :return:
        """
        sites = ""
        for site in self._sites:
            sites += (site + ', ')
        sites = sites.rstrip(', ')
        return sites

    def add_arguments(self, parser):
        parser.add_argument('-s', '--site', help=self.sites, required=False)

    def handle(self, *args, **options):
        # early exits

        # do something
        logger.log(msg='trigger received', level=logging.INFO)

