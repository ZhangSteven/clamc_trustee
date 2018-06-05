This package reads china life trustee's files for CLO portfolios. These files usually arrive in a monthly basis, containing amortized cost for HTM bond positions. We can use them to generate reports for fixed income team and create upload files for Bloomberg AIM.

The package contains two modules:

trustee.py: read an Excel file and convert it to a list of records of holdings, including cash, bond, equity, etc.

report.py: use the records from trustee.py to generate reports we need.