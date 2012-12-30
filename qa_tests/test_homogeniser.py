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
import os
from datetime import datetime

from tests.test_utils import in_data_dir

from eqcatalogue import (CatalogueDatabase, C, Precise, AgencyRanking,
                         MUSSetDefault, MUSSetEventMaximum, MUSDiscard,
                         Homogeniser, LinearModel, PolynomialModel)


class HomogeniserAPI(unittest.TestCase):
    def setUp(self):
        CatalogueDatabase(filename=in_data_dir('qa.db'))

    def _plot_and_assert(self, homo, filename_prefix):
        graph_filename = in_data_dir("qa_homo_%s.png" % filename_prefix)
        homo.plot(graph_filename)
        self.assertTrue(os.path.exists(in_data_dir(graph_filename)))

    def test_different_configs(self):
        homo = Homogeniser("mb", "MS")
        homo.set_criteria(C(agency__in=["ISC", "BJI"]))
        homo.set_selector(Precise)
        homo.add_model(LinearModel)
        self._plot_and_assert(homo, 'first')

        homo.set_criteria(C(before=datetime.now()))
        ranking = {"ML": ["ISC", "IDC"], "mb": ["ISC", "FUNV"]}
        homo.set_selector(AgencyRanking, ranking=ranking)
        homo.set_scales("ML", "mb")
        homo.add_model(PolynomialModel, order=2)
        self._plot_and_assert(homo, 'second')

        homo.set_criteria(
            C(between=(datetime(2010, 2, 28, 4, 11), datetime.now())) &
            C(agency__in=["NIED", "IDC"]) & C(scale__in=["ML", "mb"]))
        homo.set_selector(Precise)
        homo.set_missing_uncertainty_strategy(MUSSetDefault,
                                              default=0.2)
        homo.reset_models()
        homo.add_model(LinearModel)
        homo.add_model(PolynomialModel, order=3)
        self._plot_and_assert(homo, 'fourth')

        polygon = 'POLYGON((127.40 30.24, 144.36 49.96, 150.22 34.78))'
        homo.set_criteria(C(within_polygon=polygon))
        homo.set_missing_uncertainty_strategy(MUSSetEventMaximum)
        self._plot_and_assert(homo, 'third')

        point = 'POINT(138.80 33.80)'
        distance = 10000000
        homo.set_criteria(C(within_distance_from_point=[point, distance]))
        homo.set_missing_uncertainty_strategy(MUSDiscard)
        self._plot_and_assert(homo, 'fifth')
