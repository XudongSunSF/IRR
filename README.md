I implemented the *cash flow table* in the spreadsheet and *irr()* function.

example.py shows how to calcualte the cash flow table and irr number.

The code is orgnized as follows:
- data folder contains the Loan IRR.xlxs spreadsheet in which Charged Off and Prepay sheets will be load by *input.py*
- config.yaml is used to set up the input file name and data sheet names
- input.py: load Charge Off and Prepay tables to pandas DataFrame: *CHARGED_OFF*, *PREPAY* which will be exposed to *loan_amort.py* when input.py is imported
- loan_amort.py implements **Loan** and **Amortization** to calculate the amortization schedule table. These two classes are straight-forward and self-explanatory. 
I didn't reinvet the wheel for PPMT, PMT and IPMT functions. Instead, I used these functions in numpy_financial when calculating scheduled cash flows
One assumption I made here is the payment dates: if the issue date is the end of month, all payment dates will be the end of month instead of the formula used in the spreadsheet
- irr.py implements the internal rate of return calculation. Since I could see numpy_financial's implementation of irr(), I solve the non-linear equation of the internal rate of return
by a solver.
- tests contains simple tests of comparing cash flow table with the one in the spreadsheet and testing irr