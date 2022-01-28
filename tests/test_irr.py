from irr import irr
from loan_amort import Loan, Amortization
from numpy.testing import assert_almost_equal

class TestIRR:
    def test_irr(self):
        v = [-150000, 15000, 25000, 35000, 45000, 60000]
        assert_almost_equal(irr(v), 0.0524, 2)
        v = [-100, 0, 0, 74]
        assert_almost_equal(irr(v), -0.0955, 2)
        v = [-100, 39, 59, 55, 20]
        assert_almost_equal(irr(v), 0.28095, 2)
        v = [-100, 100, 0, -7]
        assert_almost_equal(irr(v), -0.0833, 2)
        v = [-100, 100, 0, 7]
        assert_almost_equal(irr(v), 0.06206, 2)
        v = [-5, 10.5, 1, -8, 1]
        assert_almost_equal(irr(v), 0.0886, 2)

        loan = Loan('C4', '08/24/2015', 36, 0.28, 7500.0,
            3228.61, 0.08, 0.0514, 0.025, 0.025)
        cf = Amortization()
        cf.calc_cashflows(loan)
        anual_irr = irr(cf.total_cf) * 12
        assert_almost_equal(anual_irr, 0.0549130698297251)