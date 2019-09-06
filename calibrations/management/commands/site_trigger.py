from django.core.management.base import BaseCommand


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
        parser.add_argument('-s', '--site', help=self.sites, required=True)

    def handle(self, *args, **options):
        # early exits
        if not options['site']:
            return 'Must supply a valid site. For usage: ./manage.py site_trigger -h'
        if options['site'] not in self._sites:
            return f"{options['site']} not a valid site. For valid sites: ./manage.py site_trigger -h"

        # send a trigger to the site
        pass

        return "Success!"
