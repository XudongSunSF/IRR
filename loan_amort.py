from dataclasses import dataclass
from input import CHARGED_OFF, PREPAY
import numpy as np
import numpy_financial as npf
import pandas as pd
from pandas._libs.tslibs.timestamps import Timestamp
from typing import Union, Optional

__all__ = ['Loan', 'Amortization', 'FREQ_PERIOD_MAP']

FREQ_PERIOD_MAP = {'D': 365, 'M': 12, '3M': 4, '6M': 2,
                   'Y': 1}  # actual / 365 day count convention


class Loan:

    def __init__(
            self,
            grade: str,
            issue_date: str,
            term: int,
            coupon: float,
            invested: float,
            outstanding_bal: float,
            recov_rate: float,
            premium: float,
            serv_fee: float,
            earnout_fee: float,
            amort_freq: str = 'M',
            charge_off_col_num: Optional[int] = None):
        """Loan class having all loan characteristics.
        Attributes:
            - grade (str): loan grade
            - issue_date (datetime): loan issue date
            - term (int): number of payments
            - coupon (float): coupon rate
            - invested (float): invested amount
            - outstanding_balance (float): loan's outstanding balance
            - recovery_rate (float): recovery rate
            - premium (float): purchase premium
            - servicing_fee (float): servicing fee
            - earnout_fee (float): earn out fee
            - amort_freq (str): amortization frequency with options: 'D', 'M', '3M', '6M', 'Y'. Default to 'M'
            - charge_off_col_num (int): column number in the charge off table, used to look up for the charge off rates
        """
        self.grade = str(grade)
        self.issue_date = pd.to_datetime(issue_date)
        self.term = term
        self.coupon = coupon
        self.invested = invested
        self.outstanding_balance = outstanding_bal
        self.recovery_rate = recov_rate
        self.premium = premium
        self.servicing_fee = serv_fee
        self.earnout_fee = earnout_fee
        self.amort_freq = amort_freq
        self.charge_off_lookup_key = '-'.join([str(term), self.grade])
        self.charge_off_col_num = charge_off_col_num


@dataclass
class Amortization:
    """Calculate and store a loan's cash flows.
    """
    pmt_cnt: np.ndarray = None
    pmt_date: np.ndarray = None
    scheduled_principal: np.ndarray = None
    scheduled_interest: np.ndarray = None
    scheduled_balance: np.ndarray = None
    prepay_speed: np.ndarray = None
    default_rate: np.ndarray = None
    recovery: np.ndarray = None
    servicing_cf: np.ndarray = None
    earout_cf: np.ndarray = None
    balance: np.ndarray = None
    principle: np.ndarray = None
    default: np.ndarray = None
    prepay: np.ndarray = None
    interest: np.ndarray = None
    total_cf: np.ndarray = None
    _default_multiplier: float = 1.0
    _prepay_multiplier: float = 1.0

    @property
    def default_multiplier(self):
        return self._default_multiplier

    @default_multiplier.setter
    def default_multiplier(self, val: float):
        self._default_multiplier = val

    @property
    def prepay_multiplier(self):
        return self._prepay_multiplier

    @prepay_multiplier.setter
    def prepay_multiplier(self, val: float):
        self._prepay_multiplier = val

    def payment_date(self, start_date: Timestamp, periods: int, freq='M'):
        """Calculate loan's payment dates

        Args:
            start_date (str): start date str
            periods (int): number of amortization periods
            freq (str): amortization frequency. Default to 'M'
        """
        # add 1 to nper to include issue_date
        nper = periods + 1
        self.pmt_date = pd.date_range(
            start=start_date, periods=nper, freq=freq)
        # pd.date_range will generate end of month dates, update day if start_date isn't an end of month date
        if start_date.day != self.pmt_date[0].day:
            self.pmt_date = list(map(lambda t: t.replace(day = start_date.day), self.pmt_date))
        

    def fetch_prepay_speed(self, nper: int):
        """Retrieve prepay speed from PREPAY DataFrame by number of payment periods

        Args:
            nper (int): number of payment periods
        """
        if nper not in PREPAY:
            raise KeyError(
                f'{nper} cannot be found in the Prepay table')
        self.prepay_speed = np.zeros(nper + 1)
        #TODO: check PREPAY[nper].dropna() length
        self.prepay_speed[1:] = PREPAY[nper].dropna().to_numpy()

    def fetch_default_rate(self, chargeoff_col: Union[str, int]):
        """Retrieve default rate from CHARGED_OFF DataFrame by chargeoff_col_name

        Args:
            chargeoff_col (str): column name in the CHARGED_OFF DataFrame

        Returns:
            np.ndarray: default rate
        """
        if isinstance(chargeoff_col, int):
            if chargeoff_col >= CHARGED_OFF.shape[1]:
                raise ValueError(
                    f"{chargeoff_col} exceeds Charge Off table's column index.")
            self.default_rate = CHARGED_OFF.iloc[:, chargeoff_col].to_numpy()
        elif isinstance(chargeoff_col, str):
            if chargeoff_col not in CHARGED_OFF:
                raise KeyError(
                    f'{chargeoff_col} cannot be found in the Charge Off table')
            self.default_rate = CHARGED_OFF[chargeoff_col].to_numpy()
        else:
            raise KeyError(f"chargeoff_col argument must be either a str or an int")

    def calc_scheduled_cashflow(self, loan: Loan):
        """Calculate a loan's scheduled principal, scheduled interest and scheduled balance

        Args:
            loan (Loan): Loan object of a loan's characteristics
        """
        rate = loan.coupon / FREQ_PERIOD_MAP[loan.amort_freq]
        nper = loan.term
        pv = -loan.invested
        nper_1 = nper + 1
        self.pmt_cnt = np.arange(0, nper_1)
        self.scheduled_principal = np.zeros(nper_1)
        self.scheduled_principal[1:] = npf.ppmt(rate, self.pmt_cnt[1:], nper, pv)
        self.scheduled_interest = np.zeros(nper_1)
        self.scheduled_interest[1:] = npf.ipmt(rate, self.pmt_cnt[1:], nper, pv)
        self.scheduled_balance = np.zeros(nper_1)
        self.scheduled_balance[0] = loan.invested
        for i in range(1, nper_1):
            self.scheduled_balance[i] = self.scheduled_balance[i - 1] - self.scheduled_principal[i]

    def calc_default_prepay_adjust_cashflow(self, loan: Loan):
        """calculate prepay, default, balance, principal and interest after default and prepay adjustment
            - default[i] = balance[i - 1] * default rate[i - 1] * default_multiplier
            - prepay[i] = (balance[i - 1] - (balance[i - 1] - scheduled_interest[i])/scheduled_balance[i - 1] * scheduled_principal[i])
                     * prepay_speed[i - 1] * prepay_multiplier
            - principal[i] = (balance[i - 1] - default[i]) * scheduled_principal[i] / scheduled_balance[i - 1] + prepay[i-1]
            - balance[i] = balance[i - 1] - principal[i] - default[i]
            - interest[i] = (balance[i - 1] - default[i]) * rate
        Args:
            loan (Loan): Loan object of a loan's characteristics
        """
        if self.pmt_cnt is None:
            raise("calc_scheduled_cashflow needs to be called first")
        nper = len(self.pmt_cnt)
        # preallocate
        self.balance = np.zeros(nper)
        self.default = np.zeros(nper)
        self.prepay = np.zeros(nper)
        self.principle = np.zeros(nper)
        self.interest = np.zeros(nper)
        nper_per_year = FREQ_PERIOD_MAP[loan.amort_freq]
        rate = loan.coupon / nper_per_year
        # intial cashflow
        self.balance[0] = self.scheduled_balance[0]
        # loop through all periods
        for i in range(1, nper):
            self.default[i] = self.balance[i-1] * self.default_rate[i-1] * self._default_multiplier
            self.prepay[i] = (self.balance[i-1] - (self.balance[i-1] - self.scheduled_interest[i]) / self.scheduled_balance[i-1]
                              * self.scheduled_principal[i]) * self.prepay_speed[i] * self._prepay_multiplier
            self.principle[i] = (self.balance[i-1] - self.default[i]) * self.scheduled_principal[i] / self.scheduled_balance[i-1] \
                              + self.prepay[i]
            self.balance[i] = self.balance[i-1] - self.principle[i] - self.default[i]
            self.interest[i] = (self.balance[i-1] - self.default[i]) * rate

        self.recovery = self.default * loan.recovery_rate
        self.servicing_cf = np.zeros(nper)
        self.servicing_cf[1:] = (
            self.balance[0:-1] - self.default[1:]) * loan.servicing_fee / nper_per_year
        self.earout_cf = np.zeros(nper)
        self.earout_cf[12] = self.earout_cf[18] = loan.earnout_fee / 2 * loan.invested
        self.total_cf = self.principle + self.interest + self.recovery - self.servicing_cf - self.earout_cf
        self.total_cf[0] = -loan.invested * (1 + loan.premium)

    def calc_cashflows(self, loan: Loan):
        """Calculate all cash flows for a loan

        Args:
            loan (Loan): Loan object of a loan's characteristics
        """
        # step 1 retrieve prepay spead
        self.fetch_prepay_speed(loan.term)
        # step 2 retrive default rate
        # user input column number has a higher priority
        if loan.charge_off_col_num:
            self.fetch_default_rate(loan.charge_off_col_num)
        else:
            self.fetch_default_rate(loan.charge_off_lookup_key)
        # step 3 calculate payment dates
        self.payment_date(loan.issue_date, loan.term, loan.amort_freq)
        # step 4 calculate scheduled cash flows
        self.calc_scheduled_cashflow(loan)
        # step 5 calculate prepay and default adjusted cash flows
        self.calc_default_prepay_adjust_cashflow(loan)

        return self.to_dataframe()

    def to_dataframe(self):
        months = range(1, len(self.pmt_date) + 1)
        field_dict = {
            'Months': months,
            'Paymnt_Count': self.pmt_cnt,
            'Payment_Date': self.pmt_date,
            'Scheduled_Principal': self.scheduled_principal,
            'Scheduled_Interest': self.scheduled_interest,
            'Scheduled_Balance': self.scheduled_balance,
            'Prepay_Speed': self.prepay_speed,
            'Default_Rate': self.default_rate[:len(months)],
            'Recovery': self.recovery,
            'Servicing_CF': self.servicing_cf,
            'Earnout_CF': self.earout_cf,
            'Balance': self.balance,
            'Principal': self.principle,
            'Default': self.default,
            'Prepay': self.prepay,
            'Interest_Amount': self.interest,
            'Total_CF': self.total_cf
        }
        return pd.DataFrame(field_dict)

    def __repr__(self):
        """ represent the class as a pandas DataFrame
        """
        return repr(self.to_dataframe())

    def to_csv(self, filename: str):
        """Output Cashflow class to CSV as a pandas DataFrame

        Args:
            filename (str): output file full path
        """
        self.to_dataframe().to_csv(filename, index=False)