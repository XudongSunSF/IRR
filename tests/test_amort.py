from loan_amort import Loan, Amortization
import pandas as pd
from numpy.testing import assert_almost_equal

class TestAmortization:

    def test_calc_cashflows(self):
        loan = Loan(grade = 'C4', issue_date = '08/24/2015', term = 36, coupon = 0.28, \
                    invested=7500.0, outstanding_bal = 3228.61, recov_rate = 0.08, \
                    premium = 0.0514, serv_fee = 0.025, earnout_fee = 0.025)
        cf = Amortization()
        cf_df = cf.calc_cashflows(loan)
        # load spreadsheet results
        ref_df = pd.read_csv('./tests/results.csv', header=0)
        # use numpy.testing instead of pandas.testing to avoid differences caused by dtype
        # exlude 'Payment_Date' and 'Playdate'
        arr_calc = cf_df.loc[:, cf_df.columns!='Payment_Date'].to_numpy()
        arr_ref = ref_df.loc[:, ref_df.columns!='Playdate'].to_numpy()
        assert_almost_equal(arr_calc, arr_ref, decimal=6)