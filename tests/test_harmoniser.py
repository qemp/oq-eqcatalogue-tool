# Copyright (c) 2010-2012, GEM Foundation.
#
# eqcatalogueTool is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# eqcatalogueTool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with eqcatalogueTool. If not, see <http://www.gnu.org/licenses/>.


import unittest

from eqcatalogue.harmoniser import Harmoniser
from eqcatalogue.regression import (LinearModel,
                                    EmpiricalMagnitudeScalingRelationship)
from eqcatalogue.models import MagnitudeMeasure, Event, CatalogueDatabase
from tests.test_filtering import load_fixtures
from eqcatalogue.filtering import C


class HarmoniserWithFixturesAbstractTestCase(unittest.TestCase):
    """
    Create an harmonizer and some basic fixtures
    """
    def setUp(self):
        self.target_scale = "Mw"
        self.a_native_scale = "mb"
        self.ya_native_scale = "Ml"

        # generate a set of measures
        self.measures = []

        events = [Event(source_key=i, eventsource=None,
                  name="test event %d" % i) for i in range(0, 10)]

        self._append_fixture_measures(events, self.a_native_scale, 1.0)
        self._append_fixture_measures(events, self.ya_native_scale, 3.0)
        self._append_fixture_measures(events, self.target_scale, 2.0)

        self.number_of_measures = len(self.measures)

    def _append_fixture_measures(self, events, scale, mfactor, count=10):
        for i in range(0, count):
            self.measures.append(
                MagnitudeMeasure(
                    agency=None, event=events[i], origin=None,
                    scale=scale,
                    standard_error=1, value=(i + 1) * mfactor))

    def assertConversion(self, converted, converted_count,
                         unconverted, unconverted_count, formula_used_nr=1):
        self.assertEqual(converted_count, len(converted))
        self.assertEqual(unconverted_count, len(unconverted))

        for measure in self.measures:
            if measure in converted:
                converted_measure = converted[measure]
                if measure.scale == self.a_native_scale:
                    self.assertEqual(formula_used_nr,
                                     len(converted_measure['formulas']))
                    self.assertAlmostEqual(converted_measure['measure'].value,
                                           measure.value * 2)
                elif measure.scale == self.target_scale:
                    self.assertEqual(converted_measure['formulas'], [])
                    self.assertAlmostEqual(converted_measure['measure'].value,
                                           measure.value)
                elif measure.scale == self.ya_native_scale:
                    self.assertEqual(formula_used_nr,
                                     len(converted_measure['formulas']))
                    self.assertAlmostEqual(converted_measure['measure'].value,
                                           measure.value / 1.5)
            else:
                self.assertTrue(measure in unconverted)


class HarmoniserWithModelTestCase(HarmoniserWithFixturesAbstractTestCase):
    """
    Tests harmonization by using regression models as conversion formula
    """

    def setUp(self):
        super(HarmoniserWithModelTestCase, self).setUp()
        native_measures_1 = self.measures[0:self.number_of_measures / 3]
        native_measures_2 = self.measures[
            self.number_of_measures / 3:2 * self.number_of_measures / 3]
        target_measures = self.measures[2 * self.number_of_measures / 3:]
        emsr = EmpiricalMagnitudeScalingRelationship(
            native_measures=native_measures_1,
            target_measures=target_measures)
        self.a_model, _ = emsr.apply_regression_model(LinearModel)

        emsr = EmpiricalMagnitudeScalingRelationship(
            native_measures=native_measures_2,
            target_measures=target_measures)
        self.ya_model, _ = emsr.apply_regression_model(LinearModel)

    def test_one_model(self):
        """
        Test with one model. Given a target scale, a list of measures
        (in a single magnitude scales), and an empirical magnitude
        scaling relationship (between a native scale mb and the
        considered target scale), an Harmoniser should convert to the
        target scale only the measure in that native scale
        """

        mismatches = self.number_of_measures / 3

        h = Harmoniser(target_scale=self.target_scale)
        h.add_conversion_formula_from_model(self.a_model)
        converted, unconverted = h.harmonise(self.measures)

        self.assertConversion(converted, self.number_of_measures - mismatches,
                              unconverted, mismatches)

    def test_no_match(self):
        """
        Test limit situations where no harmonization should happen
        """

        # model provided does not convert from the native magnitude scale
        for measure in self.measures:
            measure.scale = "fake scale"

        h = Harmoniser(target_scale=self.target_scale)
        h.add_conversion_formula_from_model(self.a_model)
        converted, unconverted = h.harmonise(self.measures)
        self.assertEqual(0, len(converted))
        self.assertEqual(self.number_of_measures, len(unconverted))

        # no model are provided
        h = Harmoniser(target_scale=self.target_scale)
        converted, unconverted = h.harmonise(self.measures)
        self.assertEqual(0, len(converted))
        self.assertEqual(self.number_of_measures, len(unconverted))

        # no model matches the target scale
        h = Harmoniser(target_scale="wrong scale")
        h.add_conversion_formula_from_model(self.a_model)
        converted, unconverted = h.harmonise(self.measures)
        self.assertEqual(0, len(converted))
        self.assertEqual(self.number_of_measures, len(unconverted))

    def test_more_model(self):
        """
        Test with several models
        """
        h = Harmoniser(target_scale=self.target_scale)

        h.add_conversion_formula_from_model(self.a_model)
        h.add_conversion_formula_from_model(self.ya_model)
        converted, unconverted = h.harmonise(self.measures)

        self.assertConversion(converted, self.number_of_measures,
                              unconverted, 0)


class HarmoniserWithFormulaTestCase(HarmoniserWithFixturesAbstractTestCase):
    def setUp(self):
        super(HarmoniserWithFormulaTestCase, self).setUp()
        native_measures_1 = self.measures[0:self.number_of_measures / 3]
        native_measures_2 = self.measures[
            self.number_of_measures / 3:2 * self.number_of_measures / 3]

        self.a_conversion = {'formula': lambda x: x * 2.,
                             'domain': native_measures_1,
                             'target_scale': self.target_scale}
        self.ya_conversion = {'formula': lambda x: x / 1.5,
                              'domain': native_measures_2,
                              'target_scale': self.target_scale}

    def test_one_conversion(self):
        """
        Test with one conversion. Given a target scale, a list of measures
        (in a single magnitude scales), and an empirical magnitude
        scaling relationship (between a native scale mb and the
        considered target scale), an Harmoniser should convert to the
        target scale only the measure in that native scale
        """

        mismatches = self.number_of_measures / 3

        h = Harmoniser(target_scale=self.target_scale)
        h.add_conversion_formula(**self.a_conversion)
        converted, unconverted = h.harmonise(self.measures)
        self.assertConversion(converted, self.number_of_measures - mismatches,
                              unconverted, mismatches)

    def test_no_match(self):
        """
        Test limit situations where no harmonization should happen
        """

        # conversion provided applies to a different domain
        h = Harmoniser(target_scale=self.target_scale)
        self.a_conversion.update({'domain': []})
        h.add_conversion_formula(**self.a_conversion)
        converted, unconverted = h.harmonise(self.measures)

        # 1/3 of the measures are already in the target_scale
        self.assertEqual(self.number_of_measures / 3, len(converted))
        self.assertEqual(self.number_of_measures * 2 / 3, len(unconverted))

        # no conversion are provided
        h = Harmoniser(target_scale=self.target_scale)
        converted, unconverted = h.harmonise(self.measures)

        self.assertEqual(self.number_of_measures / 3, len(converted))
        self.assertEqual(self.number_of_measures * 2 / 3, len(unconverted))

        # no conversion matches the target scale
        h = Harmoniser(target_scale="wrong scale")
        h.add_conversion_formula(**self.a_conversion)
        converted, unconverted = h.harmonise(self.measures)
        self.assertEqual(0, len(converted))
        self.assertEqual(self.number_of_measures, len(unconverted))

    def test_more_conversion(self):
        """
        Test with several conversions
        """
        h = Harmoniser(target_scale=self.target_scale)

        h.add_conversion_formula(**self.a_conversion)
        h.add_conversion_formula(**self.ya_conversion)
        converted, unconverted = h.harmonise(self.measures)
        self.assertConversion(converted, self.number_of_measures,
                              unconverted, 0)


class HarmoniserWithFormulaAndCriteriaTestCase(
        HarmoniserWithFixturesAbstractTestCase):
    """
    Test the usage of an Homogeniser by using a formula associated
    with a criteria
    """
    def setUp(self):
        super(HarmoniserWithFormulaAndCriteriaTestCase, self).setUp()
        cat = CatalogueDatabase(memory=True, drop=True)
        cat.recreate()
        load_fixtures(cat.session)
        self.measures = C()

    def test_conversion(self):
        h = Harmoniser(target_scale=self.target_scale)

        h.add_conversion_formula(formula=lambda x: x * 2,
                                 domain=C(agency__in=['LDG', 'NEIC']),
                                 target_scale=self.target_scale)
        converted, unconverted = h.harmonise(self.measures)

        self.assertConversion(converted, 6, unconverted, 24)


class HarmoniserWithDifferentTargetScales(
        HarmoniserWithFixturesAbstractTestCase):
    """
    Tests the usage of an harmoniser with formula that targets
    different scales
    """

    def setUp(self):
        super(HarmoniserWithDifferentTargetScales, self).setUp()

    def test_conversion(self):
        h = Harmoniser(target_scale=self.target_scale)

        h.add_conversion_formula(formula=lambda x: x * 2.,
                                 domain=C(scale=self.a_native_scale),
                                 target_scale="M2")

        h.add_conversion_formula(formula=lambda x: x * 3.,
                                 domain=C(scale=self.ya_native_scale),
                                 target_scale="M3")
        h.add_conversion_formula(formula=lambda x: x * 3.,
                                 domain=C(scale="M3"),
                                 target_scale="M2")
        h.add_conversion_formula(formula=lambda x: x * 4.,
                                 domain=C(scale="M2"),
                                 target_scale=self.target_scale)
        converted, unconverted = h.harmonise(self.measures)

        self.assertEqual(30, len(converted))
        self.assertEqual(0, len(unconverted))

        for measure in self.measures:
            self.assertTrue(measure in converted)

            converted_measure = converted[measure]
            if measure.scale == self.a_native_scale:
                self.assertEqual(2, len(converted_measure['formulas']))
                self.assertAlmostEqual(converted_measure['measure'].value,
                                       measure.value * 8)
            elif measure.scale == self.target_scale:
                self.assertEqual(converted_measure['formulas'], [])
                self.assertAlmostEqual(converted_measure['measure'].value,
                                       measure.value)
            elif measure.scale == self.ya_native_scale:
                self.assertEqual(3,
                                 len(converted_measure['formulas']))
                self.assertAlmostEqual(converted_measure['measure'].value,
                                       measure.value * 36)
