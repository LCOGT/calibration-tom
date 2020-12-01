import json
import os
from requests.exceptions import RequestException
import unittest
from http import HTTPStatus

import responses

from configdb.configdb_connections import ConfigDBInterface, ConfigDBException, \
    InstrumentNotFoundException  # the module under test
from configdb.state import InstrumentState

_configdb_sites = os.path.join(os.path.dirname(__file__), 'data/sites_2020-11-30.json')

f = open(_configdb_sites, 'r')
sites = json.load(f)
f.close()


# TODO: This should be broken up into more classes, probably one per method.
class ConfigDbInterfaceTests(unittest.TestCase):

    def setUp(self):
        self.config_db_url = 'http://some-url'
        responses.start()
        responses.add(responses.GET, f'{self.config_db_url}/sites/', json=sites, status=HTTPStatus.OK)
        self.config_db = ConfigDBInterface(self.config_db_url)

    def tearDown(self):  # noqa
        responses.stop()
        responses.reset()

    def test_update_site_info_exception(self):
        """Test that an exception in _get_all_sites raises the correct exception and message."""
        self.config_db.site_info = ['test_site_info_value']

        responses.replace(responses.GET, f'{self.config_db_url}/sites/', status=HTTPStatus.NOT_FOUND)
        self.config_db.update_site_info()
        with self.assertLogs('configdb.configdb_connections', level='WARNING') as logs:
            self.config_db.update_site_info()
            # FIXME: How to properly format this for flake8?
            self.assertIn(
                f'WARNING:configdb.configdb_connections:update_site_info error ConfigDBException(\'get_all_sites failed: ConfigDB status code {HTTPStatus.NOT_FOUND}\'). Reusing previous site info',
                logs.output)
        self.assertEqual(self.config_db.site_info, ['test_site_info_value'])

    def test_get_all_sites(self):
        results = self.config_db._get_all_sites()

        self.assertDictContainsSubset({'code': 'bpl'}, results[0])

    def test_get_all_sites_request_exception(self):
        """Test that an exception in a request raises the correct exception and message."""
        responses.replace(responses.GET, f'{self.config_db_url}/sites/', body=RequestException())

        with self.assertRaises(ConfigDBException) as cm:
            self.config_db._get_all_sites()

        self.assertEqual(cm.exception.args[0], 'RequestException: get_all_sites failed: ConfigDB connection down')

    def test_get_all_sites_bad_http_response(self):
        """Test that a response other than 200 raises the correct exception and message."""
        responses.replace(responses.GET, f'{self.config_db_url}/sites/', status=HTTPStatus.NOT_FOUND)

        with self.assertRaises(ConfigDBException) as cm:
            self.config_db._get_all_sites()

        self.assertEqual(cm.exception.args[0], f'get_all_sites failed: ConfigDB status code {HTTPStatus.NOT_FOUND}')

    def test_get_all_sites_invalid_response(self):
        """Test that an unexpected response from ConfigDB raises the correct exception and message."""
        responses.replace(responses.GET, f'{self.config_db_url}/sites/', body='{"invalid": "response"}')

        with self.assertRaises(ConfigDBException) as cm:
            self.config_db._get_all_sites()

        self.assertEqual(cm.exception.args[0], 'get_all_sites failed: ConfigDB returned no results')

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
        # FIXME: we're not reading sites.json consistently b/c elp, coj, and domc
        #  should work and sometimes they do and sometimes they don't.
        three_enclosure_sites = ['cpt', 'lsc']  # skipping coj, elp
        enclosures = ['doma']  # skipping domb, domc
        for site in three_enclosure_sites:
            for enclosure in enclosures:
                with self.subTest():
                    instrument = self.config_db.get_matching_instrument(site=site, observatory=enclosure)
                    self.assertEqual(site, instrument['site'])
                    self.assertEqual(enclosure, instrument['observatory'])

        # now ask for an non-existent instrument
        with self.assertRaises(InstrumentNotFoundException):
            _ = self.config_db.get_matching_instrument(site='ogg', observatory='doma')  # OGG has no doma


class TestGetActiveTelescopesInfo(unittest.TestCase):
    # NOTE: This is in its own class because it uses a modified data set to test inactive telescopes/enclosures/sites
    def setUp(self):
        f = open(os.path.join(os.path.dirname(__file__), 'data/test_sites.json'), 'r')
        test_sites = json.load(f)
        f.close()

        self.config_db_url = 'http://some-url'

        responses.start()
        responses.add(responses.GET, f'{self.config_db_url}/sites/', json=test_sites, status=HTTPStatus.OK)

        self.config_db = ConfigDBInterface(self.config_db_url)
        self.config_db.update_site_info()

    def test_get_active_telescopes_info_all_sites(self):
        active_telescopes = self.config_db.get_active_telescopes_info()

        self.assertIn('bpl.doma.1m0a', active_telescopes)
        self.assertIn('coj.clma.0m4a', active_telescopes)
        self.assertNotIn('coj.clma.0m4b', active_telescopes)
        self.assertNotIn('coj.doma.1m0a', active_telescopes)
        self.assertNotIn('wtf.doma.1m0a', active_telescopes)

    def test_get_active_telescopes_info_one_sites(self):
        active_telescopes = self.config_db.get_active_telescopes_info(site_code='bpl')

        self.assertIn('bpl.doma.1m0a', active_telescopes)
        self.assertNotIn('coj.clma.0m4a', active_telescopes)

    def tearDown(self):  # noqa
        responses.stop()
        responses.reset()
