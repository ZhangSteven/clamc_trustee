﻿NO longer used.

Use the trustee_report package to generate TSCF upload instead. 2020-05-05

This package reads china life trustee's files for CLO portfolios. These files usually arrive in a monthly basis, containing amortized cost for HTM bond positions. We can use them to generate reports for fixed income team and create upload files for Bloomberg AIM.

The package contains two modules:

trustee.py: read an Excel file and convert it to a list of records of holdings, including cash, bond, equity, etc.

report.py: use the records from trustee.py to generate reports we need.



+++++++++++++++++++
ver 0.11 @ 2018-6-6
+++++++++++++++++++
1. Convert trustee reports to TSCF upload file for all HTM positions, ready to be uploaded to Bloomberg AIM.


+++++++++++++++++++
ver 0.1 @ 2018-6-5
+++++++++++++++++++
1. Convert trustee reports (Excel files) to a consolidated HTM bond csv.