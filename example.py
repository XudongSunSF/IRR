
from loan_amort import Loan, Amortization
from irr import irr


loan = Loan(grade = 'C4', issue_date = '08/24/2015', term = 36, coupon = 0.28, \
            invested=7500.0, outstanding_bal = 3228.61, recov_rate = 0.08, \
            premium = 0.0514, serv_fee = 0.025, earnout_fee = 0.025)
cf = Amortization()
cf.calc_cashflows(loan)
cf.to_csv('./results/cashflow.csv')
anual_irr = irr(cf.total_cf) * 12
print(f'Anualized IRR is {anual_irr}')