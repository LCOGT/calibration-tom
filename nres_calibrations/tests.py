from unittest.mock import patch
from unittest import skip

from django.test import TestCase
from django.urls import reverse

from tom_targets.tests.factories import SiderealTargetFactory
from tom_targets.models import TargetExtra
from tom_observations.models import DynamicCadence, ObservationGroup
# Create your tests here.


class NRESCalibrationsTestCase(TestCase):
    """
    Provide a setUp that other Test (sub)classes can inherit. (So we don't duplicate the setUp code).
    """
    def setUp(self):
        # create some Targets and DynamicCadences
        self.target = SiderealTargetFactory.create(ra=123.456, dec=-32.1)
        # these targetextras are required!
        TargetExtra.objects.create(target=self.target, key='standard_type', value='RV')
        TargetExtra.objects.create(target=self.target, key='seasonal_start', value=1)
        TargetExtra.objects.create(target=self.target, key='seasonal_end', value=4)

        # a DynamicCadence needs an ObservationGroup
        standard_type = 'RV'
        site = 'tlv'
        # save ObservationGroup name for testing later
        self.observation_group_name = f'NRES {standard_type} calibration for {site.upper()}'
        observation_group = ObservationGroup.objects.create(name=self.observation_group_name)

        # save cadence_parameters for testing later
        self.original_cadence_parameters = {
                'target_id': self.target.id,
                'cadence_frequency': 1,
                'site': site
            }
        DynamicCadence.objects.create(
            cadence_strategy='NRESCadenceStrategy',
            cadence_parameters=self.original_cadence_parameters,
            observation_group=observation_group,
            active=True
        )


class TestNRESCalibrationsView(NRESCalibrationsTestCase):
    def setUp(self):
        super().setUp()
        # add your subclass extension (or delete this method)
        pass

    def test_nres_calibrations_view(self):
        response = self.client.get(reverse('nres_calibrations:nres_home'))
        self.assertContains(response, self.target.id)


class TestNRESCalibrationsSubmissionView(NRESCalibrationsTestCase):
    def setUp(self):
        super().setUp()
        # add your subclass extension (or delete this method)
        pass

    @skip("We have HTML validation on this form, so this test can wait.")
    def test_submit_calibration_invalid(self):
        invalid_form_data = {'site': 'cpt', 'target': self.target}
        response = self.client.post(reverse('nres_calibrations:nres_submission'),
                                    data=invalid_form_data)
        # TODO: how is this supposed to work???
        self.assertContains(response, 'error message')

    def test_submit_calibration_valid(self):
        """Test updating a cadence_frequency for an existing cadence
        """
        new_form_data = {
            'site': 'tlv',
            'cadence_frequency': 2,  # new cadence_frequency
            'target_id': self.target.id
        }
        response = self.client.post(reverse('nres_calibrations:nres_submission'),
                                    data=new_form_data)
        # get updated cadence from db
        dc = DynamicCadence.objects.all().first()

        # the cadence_frequency should have changed from the original
        self.assertNotEqual(self.original_cadence_parameters['cadence_frequency'],
                            dc.cadence_parameters['cadence_frequency'])
        # the cadence_frequency should be what we set in new_form_data
        self.assertEqual(new_form_data['cadence_frequency'],
                         dc.cadence_parameters['cadence_frequency'])

    def test_create_cadence_for_new_site(self):
        """Test that a new DynamicCadence is created by form submission
        """
        new_form_data = {
            'site': 'cpt',
            'cadence_frequency': 10,
            'target_id': self.target.id
        }
        original_dc_count = DynamicCadence.objects.all().count()
        response = self.client.post(reverse('nres_calibrations:nres_submission'),
                                    data=new_form_data)
        new_dc_count = DynamicCadence.objects.all().count()
        # there should be one more DynamicCadence than before
        self.assertEqual(new_dc_count, original_dc_count+1)


class TestNresCalibrationsExtras(NRESCalibrationsTestCase):
    def setUp(self):
        super().setUp()
        # add your subclass extension (or delete this method)
        pass

    def test_nres_targets_list(self):
        """Test that the nres_home target list contains the NRES calibration targets
        """
        response = self.client.get(reverse('nres_calibrations:nres_home'))
        self.assertContains(response, self.target.id)

    def test_nres_cadence_list(self):
        """Test that the NRES Cadence list contains the ObservationGroup name of the DynamicCadence
        """
        response = self.client.get(reverse('nres_calibrations:nres_home'))
        self.assertContains(response, self.observation_group_name)  # should appear in History column


class TestNRESCadenceToggleView(NRESCalibrationsTestCase):
    def test_toggle_play(self):
        dc = DynamicCadence.objects.first()
        dc.active = False
        dc.save()

        self.client.get(reverse('nres_calibrations:cadence_toggle', kwargs={'pk': dc.id}))
        dc.refresh_from_db()
        self.assertTrue(dc.active)

    def test_toggle_pause(self):
        dc = DynamicCadence.objects.first()

        self.client.get(reverse('nres_calibrations:cadence_toggle', kwargs={'pk': dc.id}))
        dc.refresh_from_db()
        self.assertFalse(dc.active)


class TestNRESCadenceDeleteView(NRESCalibrationsTestCase):
    def test_cadence_delete(self):
        dc = DynamicCadence.objects.first()

        self.client.post(reverse('nres_calibrations:cadence_delete', kwargs={'pk': dc.id}))
        self.assertFalse(DynamicCadence.objects.filter(pk=dc.id).exists())
