from django.test import TestCase

# for TestCadenceTargetSelection
from tom_targets.models import Target

# for TestFacilityConfiguration
from calibrations.facilities.photometric_standards_facility import PhotometricStandardsFacility
from calibrations.facilities.lco_calibration_facility import LCOCalibrationFacility
from django.conf import settings


test_targets = [
    # Name, RA, Dec, seasonal_start, seasonal_end
    ('GJ699', 269.45, 4.69, 4, 8),
    ('GJ2066', 124.033256, 1.30257423, 12, 3),
    ('HD4628', 12.09573477, 5.28061377, 8, 12),
    ('HD16160', 39.0204266, 6.88678655, 9, 1),
    ('HD36395', 82.86414936, -3.67722821, 10, 2),
    ('HD76151', 133.5747791, -5.43445736, 12, 3),
    ('HD103631', 179.0052609, -1.44236244, 1, 6),
    ('HD12053', 215.8136865, 1.24156716, 3, 8),
    ('HD148513', 247.1415858, 0.66499963, 4, 8),
    ('HD152391', 253.2450106, -0.02642119, 4, 8),
    ('HD173818', 281.863544, -3.63983342, 5, 10),
    ('HD210988', 333.5596737, -5.74625853, 7, 11),
    ('HR9087', 0.45603553, -3.02750263, 6, 1),
    ('HR1544', 72.65301243, 8.90018037, 9, 2),
    ('HR3454', 130.8061458, 3.39866297, 12, 4),
    ('HR5501', 221.375851, 0.71727486, 3, 7),
    ('HR7596', 298.6866567, 0.27362796, 5, 10),
]


# TODO: end-to-end test settargets.py management command
class TestSetTargets(TestCase):
    def setUp(self):
        pass


# TODO: write tests
class TestCadenceTargetSelection(TestCase):
    def setUp(self):
        self.targets = []
        for target in test_targets:
            self.targets.append(Target.objects.create(
                name=target[0], type='SIDEREAL', ra=target[1],
                dec=target[2]))

            # TODO: add target_extras to these targets
            # add target_extras
            # seasonal_start=target[3], seasonal_end=target[4]

    def test_get_eligible_targets(self):
        pass

        # valid seasonal end, current year
        # invalid seasonal end, current year, after current month
        # invalid seasonal end, current year, before current month
        # valid seasonal end, next year
        # invalid seasonal end, next year
        # test seasonal start as well


class TestFacilityConfiguration(TestCase):
    def setUp(self) -> None:
        super().setUp()
        # get the facility base URL from settings.py::FACILITY dictionary
        self.expected = settings.FACILITIES['LCO']['portal_url']


    def test_phometric_standards_facility_url(self):
        """test that the PhotometricStandardsFacility is configured and can
         construct it's request URL properly.
         """
        # get the facility base URL from the instanciated Facility object
        photometric_standards_facility = PhotometricStandardsFacility()
        actual = photometric_standards_facility.facility_settings.get_setting('portal_url')
        self.assertEqual(self.expected, actual)


    def test_NRES_standards_facility_url(self):
        """test that the PhotometricStandardsFacility is configured and can
         construct it's request URL properly.
         """
        # get the facility base URL from the instanciated Facility object
        nres_calibration_facility = LCOCalibrationFacility()
        actual = nres_calibration_facility.facility_settings.get_setting('portal_url')
        self.assertEqual(self.expected, actual)
