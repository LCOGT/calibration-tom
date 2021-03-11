from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

# Create your tests here.


class TestNRESCalibrationsView(TestCase):
    def setUp(self):
        pass

    def test_nres_calibrations_view(self):
        response = self.client.get(reverse('targeted_calibrations:nres_home'))
        self.assertContains(response, self.target.id)


class TestNRESCalibrationSubmissionView(TestCase):
    def setUp(self):
        pass

    def test_submit_calibration_invalid(self):
        response = self.client.post(reverse('targeted_calibrations:submit-cadence'),
                                    data={'site': 'cpt', 'frequency': 24, 'target': self.target})
        self.assertContains(response, 'error message')


class TestTargetedCalibrationsExtras(TestCase):
    def setUp(self):
        pass

    def test_nres_targets_list(self):
        pass

    def test_nres_cadence_list(self):
        pass

    def test_nres_submission_form(self):
        pass  # This test may not be necessary
