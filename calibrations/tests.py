from django.test import TestCase

from tom_targets.models import Target

targets = [
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
        for target in targets:
            self.targets.append(Target.objects.create(
                name=target[0], type='SIDEREAL', ra=target[1],
                dec=target[2], seasonal_start=target[3], seasonal_end=target[4]
            ))

    def test_get_eligible_targets(self):
        pass

        # valid seasonal end, current year
        # invalid seasonal end, current year, after current month
        # invalid seasonal end, current year, before current month
        # valid seasonal end, next year
        # invalid seasonal end, next year
        # test seasonal start as well
