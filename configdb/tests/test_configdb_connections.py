import json
import os
import unittest
from http import HTTPStatus

import responses

from configdb.configdb_connections import ConfigDBInterface, ConfigDBException  # the module under test
from configdb.state import InstrumentState

# TODO: timestamp the configdb json dump so we know how old it is.
# TODO: update data/sites.json with latest configdb data.
_configdb_sites = os.path.join(os.path.dirname(__file__), 'data/sites.json')

f = open(_configdb_sites, 'r')
sites = json.load(f)
f.close()


class ConfigDbInterfaceTests(unittest.TestCase):

    def setUp(self):
        self.config_db_url = 'http://some-url'
        self.config_db = ConfigDBInterface(self.config_db_url)
        responses.start()
        responses.add(responses.GET, f'{self.config_db_url}/sites/', json=sites, status=HTTPStatus.OK)

    def testDown(self):
        responses.stop()
        responses.reset()

    @unittest.skip
    def test_update_site_info_exception(self):
        print(responses.mock._matches)
        responses.replace(responses.GET, f'{self.config_db_url}/sites/', status=HTTPStatus.NOT_FOUND)
        with self.assertRaises(ConfigDBException):
            self.config_db.update_site_info()

    def test_should_not_contain_disabled_instruments(self):
        """TODO: document me
        """
        active_instruments = self.config_db.get_active_instruments_info()

        for telescope_instruments in active_instruments.values():
            for instrument in telescope_instruments:
                state = InstrumentState[instrument['state']]

                assert state != InstrumentState.DISABLED

    def test_should_include_instrument_commissioning(self):
        """TODO: document me
        """
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.COMMISSIONING, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.COMMISSIONING, True, False)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.COMMISSIONING, False, True)
        self.assertTrue(include_instrument)

    def test_should_not_include_instrument_commissioning(self):
        """TODO: document me
        """
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.COMMISSIONING, False, False)
        self.assertFalse(include_instrument)

    def test_should_include_instrument_disabled(self):
        """TODO: document me
        """
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.DISABLED, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.DISABLED, True, False)
        self.assertTrue(include_instrument)

    def test_should_not_include_instrument_disabled(self):
        """TODO: document me
        """
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.DISABLED, False, True)
        self.assertFalse(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.DISABLED, False, False)
        self.assertFalse(include_instrument)

    def test_should_include_instrument_manual(self):
        """TODO: document me
        """
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.MANUAL, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.MANUAL, True, False)
        self.assertTrue(include_instrument)

    def test_should_not_include_instrument_manual(self):
        """TODO: document me
        """
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.MANUAL, False, False)
        self.assertFalse(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.MANUAL, False, True)
        self.assertFalse(include_instrument)

    def test_should_include_instrument_schedulable(self):
        """TODO: document me
        """
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.SCHEDULABLE, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.SCHEDULABLE, True, False)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.SCHEDULABLE, False, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.SCHEDULABLE, False, False)
        self.assertTrue(include_instrument)

    def test_should_include_instrument_standby(self):
        """TODO: document me
        """
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.STANDBY, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.STANDBY, True, False)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.STANDBY, False, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.STANDBY, False, False)
        self.assertTrue(include_instrument)

    def test_get_instruments_types(self):
        """assert various properties of the return value

        * return value should be a list of dictionaries, with 'code' and 'name' keys
        * the list of instrument codes should be unique (i.e. the list of code values should not contain duplicates)
        """
        # call the method under test
        instrument_types = self.config_db.get_instruments_types()  # the method under test

        # the return value should be a list of dictionaries, with 'code' and 'name' keys
        self.assertIsInstance(instrument_types, list)
        self.assertIsInstance(instrument_types[0], dict)
        self.assertTrue(instrument_types[0].keys().__contains__('code'))
        self.assertTrue(instrument_types[0].keys().__contains__('name'))

        # the codes should be unique (the list of code values should not contain duplicates)
        instrument_codes = [instrument_type['code'] for instrument_type in instrument_types]
        self.assertEqual(len(instrument_codes), len(set(instrument_codes)))

    def test_get_matching_instruments(self):
        three_enclosure_sites = ['coj', 'cpt', 'lsc', 'elp', ]
        enclosures = ['doma', 'domb', 'domc']
        for site in three_enclosure_sites:
            for enclosure in enclosures:
                instrument = self.config_db.get_matching_instrument(site=site, observatory=enclosure)
                self.assertEqual(site, instrument['site'])
                self.assertEqual(enclosure, instrument['observatory'])
                self.assertEqual('SCHEDULABLE', instrument['state'])


