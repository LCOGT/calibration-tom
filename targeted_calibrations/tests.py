from unittest.mock import patch
from unittest import skip

from django.test import TestCase
from django.urls import reverse

from tom_targets.tests.factories import SiderealTargetFactory
from tom_targets.models import TargetExtra
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

    def test_nres_calibrations_view(self):
        response = self.client.get(reverse('targeted_calibrations:nres_home'))
        self.assertContains(response, self.target.id)


class TestNRESCalibrationSubmissionView(NRESCalibrationsTestCase):
    def setUp(self):
        super().setUp()
        # add your subclass extension (or delete this method)
        pass

    def test_submit_calibration_invalid(self):
        response = self.client.post(reverse('targeted_calibrations:nres_submission'),
                                    data={'site': 'cpt', 'frequency': 24, 'target': self.target})
        self.assertContains(response, 'error message')


class TestTargetedCalibrationsExtras(NRESCalibrationsTestCase):
    def setUp(self):
        super().setUp()
        # add your subclass extension (or delete this method)
        pass

    def test_nres_targets_list(self):
        pass

    def test_nres_cadence_list(self):
        pass

    def test_nres_submission_form(self):
        pass  # This test may not be necessary
