import json
import os
import unittest
from http import HTTPStatus

import responses

from configdb.configdb_connections import ConfigDBInterface # the module under test
from configdb.state import  InstrumentState

_configdb_sites = os.path.join(os.path.dirname(__file__), 'data/sites.json')

f = open(_configdb_sites, 'r')
sites = json.load(f)
f.close()


class ConfigDbInterfaceTests(unittest.TestCase):
    @responses.activate
    def test_should_not_contain_disabled_instruments(self):
        config_db_url = 'http://some-url'

        responses.add(responses.GET, f'{config_db_url}/sites/', json=sites, status=HTTPStatus.OK)

        config_db = ConfigDBInterface(config_db_url)
        active_instruments = config_db.get_active_instruments_info()

        for telescope_instruments in active_instruments.values():
            for instrument in telescope_instruments:
                state = InstrumentState[instrument['state']]

                assert state != InstrumentState.DISABLED

    def test_should_include_instrument_commissioning(self):
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.COMMISSIONING, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.COMMISSIONING, True, False)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.COMMISSIONING, False, True)
        self.assertTrue(include_instrument)

    def test_should_not_include_instrument_commissioning(self):
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.COMMISSIONING, False, False)
        self.assertFalse(include_instrument)

    def test_should_include_instrument_disabled(self):
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.DISABLED, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.DISABLED, True, False)
        self.assertTrue(include_instrument)

    def test_should_not_include_instrument_disabled(self):
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.DISABLED, False, True)
        self.assertFalse(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.DISABLED, False, False)
        self.assertFalse(include_instrument)

    def test_should_include_instrument_manual(self):
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.MANUAL, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.MANUAL, True, False)
        self.assertTrue(include_instrument)

    def test_should_not_include_instrument_manual(self):
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.MANUAL, False, False)
        self.assertFalse(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.MANUAL, False, True)
        self.assertFalse(include_instrument)

    def test_should_include_instrument_schedulable(self):
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.SCHEDULABLE, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.SCHEDULABLE, True, False)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.SCHEDULABLE, False, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.SCHEDULABLE, False, False)
        self.assertTrue(include_instrument)

    def test_should_include_instrument_standby(self):
        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.STANDBY, True, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.STANDBY, True, False)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.STANDBY, False, True)
        self.assertTrue(include_instrument)

        include_instrument = ConfigDBInterface.should_include_instrument(InstrumentState.STANDBY, False, False)
        self.assertTrue(include_instrument)
