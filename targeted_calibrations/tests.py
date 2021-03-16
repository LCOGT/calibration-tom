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

        DynamicCadence.objects.create(
            cadence_strategy='NRESCadenceStrategy',
            cadence_parameters={
                'target_id': self.target.id,
                'cadence_frequency': -17,
                'site': site
            },
            observation_group=observation_group,
            active=True
        )


class TestNRESCalibrationsView(NRESCalibrationsTestCase):
    def setUp(self):
        super().setUp()
        # add your subclass extension (or delete this method)
        pass

    def test_nres_calibrations_view(self):
        response = self.client.get(reverse('targeted_calibrations:nres_home'))
        self.assertContains(response, self.target.id)


class TestNRESCalibrationSubmissionView(NRESCalibrationsTestCase):
    def setUp(self):
        super().setUp()
        # add your subclass extension (or delete this method)
        pass

    @skip
    def test_submit_calibration_invalid(self):
        invalid_form_data = {'site': 'cpt', 'target': self.target}
        response = self.client.post(reverse('targeted_calibrations:nres_submission'),
                                    data=invalid_form_data)
        # TODO: how is this supposed to work???
        self.assertContains(response, 'error message')


class TestTargetedCalibrationsExtras(NRESCalibrationsTestCase):
    def setUp(self):
        super().setUp()
        # add your subclass extension (or delete this method)
        pass

    def test_nres_targets_list(self):
        """Test that the nres_home target list contains the NRES calibration targets
        """
        response = self.client.get(reverse('targeted_calibrations:nres_home'))
        self.assertContains(response, self.target.id)

    def test_nres_cadence_list(self):
        """Test that the NRES Cadence list contains the ObservationGroup name of the DynamicCadence
        """
        response = self.client.get(reverse('targeted_calibrations:nres_home'))
        self.assertContains(response, self.observation_group_name)  # should appear in History column


class TestNRESCadenceToggleView(NRESCalibrationsTestCase):
    def test_toggle_play(self):
        dc = DynamicCadence.objects.first()
        dc.active = False
        dc.save()

        self.client.get(reverse('targeted_calibrations:cadence_toggle', kwargs={'pk': dc.id}))
        dc.refresh_from_db()
        self.assertTrue(dc.active)

    def test_toggle_pause(self):
        dc = DynamicCadence.objects.first()

        self.client.get(reverse('targeted_calibrations:cadence_toggle', kwargs={'pk': dc.id}))
        dc.refresh_from_db()
        self.assertFalse(dc.active)


class TestNRESCadenceDeleteView(NRESCalibrationsTestCase):
    def test_cadence_delete(self):
        dc = DynamicCadence.objects.first()

        self.client.post(reverse('targeted_calibrations:cadence_delete', kwargs={'pk': dc.id}))
        self.assertFalse(DynamicCadence.objects.filter(pk=dc.id).exists())
