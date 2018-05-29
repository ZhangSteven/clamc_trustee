# coding=utf-8
# 

import unittest2, os
from clamc_trustee.utility import get_current_path
from clamc_trustee.trustee import readFileToRecords



def htmBond(record):
    if (record['type'], record['accounting']) == ('bond', 'htm'):
        return True
    return False



class TestHTM(unittest2.TestCase):
    """
    Read records from one file only.
    """

    def __init__(self, *args, **kwargs):
        super(TestHTM, self).__init__(*args, **kwargs)


    def testHtmBond1(self):
        file = os.path.join(get_current_path(), 'samples', 
                    '00._Portfolio_Consolidation_Report_CGFB 1804.xls')
        records = readFileToRecords(file)
        records = list(filter(htmBond, records))
        self.assertEqual(len(records), 20)
        self.verifyBond1(records[2])
        self.verifyBond2(records[4])



    def testHtmBond2(self):
        file = os.path.join(get_current_path(), 'samples', 
                    '00._Portfolio_Consolidation_Report_AFBH1 1804.xls')
        records = readFileToRecords(file)
        records = list(filter(htmBond, records))
        self.assertEqual(len(records), 70)
        self.verifyBond3(records[1])
        self.verifyBond4(records[6])



    def verifyBond1(self, record):
        """
        first bond in USD HTM bond section,
        samples/00._Portfolio_Consolidation_Report_CGFB 1804.xls
        """
        self.assertEqual('US55608JAB44 Macquarie Gp L7.625%', record['description'])
        self.assertEqual('USD', record['currency'])
        self.assertEqual(1350000, record['quantity'])
        self.assertAlmostEqual(7.625, record['coupon'])
        self.assertEqual('2018-2-13', record['interest start day'])
        self.assertEqual('2019-8-13', record['maturity'])
        self.assertAlmostEqual(105.402, record['average cost'])
        self.assertAlmostEqual(101.1070089, record['amortized cost'])
        self.assertEqual(1422927, record['total cost'])
        self.assertAlmostEqual(22303.12, record['accrued interest'])
        self.assertAlmostEqual(1387247.74, record['total amortized cost'])



    def verifyBond2(self, record):
        """
        3rd bond in USD HTM bond section,
        samples/00._Portfolio_Consolidation_Report_CGFB 1804.xls
        """
        self.assertEqual('US55608KAD72', record['isin'])
        self.assertEqual('bond', record['type'])
        self.assertEqual('USD', record['currency'])
        self.assertEqual(346000, record['quantity'])
        self.assertAlmostEqual(6.25, record['coupon'])
        self.assertEqual('2018-1-14', record['interest start day'])
        self.assertAlmostEqual(99.1805723, record['average cost'])
        self.assertAlmostEqual(99.7179162, record['amortized cost'])
        self.assertAlmostEqual(1859.21, record['total amortized gain loss'])
        self.assertAlmostEqual(2665776.63, record['total cost HKD'])
        self.assertAlmostEqual(50445.68, record['accrued interest HKD'], 2)
        self.assertAlmostEqual(2758366.47, record['total amortized cost HKD'], 2)
        self.assertAlmostEqual(14592.01, record['total amortized gain loss HKD'], 2)
        self.assertAlmostEqual(27552.15, record['FX gain loss HKD'], 2)
        self.assertAlmostEqual(0.0025, record['percentage of fund'])



    def verifyBond3(self, record):
        """
        first bond in HKD HTM bond section,
        samples/00._Portfolio_Consolidation_Report_AFBH1 1804.xls
        """
        self.assertEqual('DBANFB12014 Dragon Days Ltd 6.0%', record['description'])
        self.assertEqual('HK0000175916', record['isin'])
        self.assertEqual('HKD', record['currency'])
        self.assertEqual(916000000, record['quantity'])
        self.assertAlmostEqual(6, record['coupon'])
        self.assertEqual('2018-3-21', record['interest start day'])
        self.assertEqual('2022-3-21', record['maturity'])
        self.assertAlmostEqual(104.072804, record['average cost'], 6)
        self.assertAlmostEqual(101.746667, record['amortized cost'], 6)
        self.assertEqual(953306880, record['total cost'])
        self.assertAlmostEqual(6173589.04, record['accrued interest'], 2)
        self.assertAlmostEqual(938173058.72, record['total amortized cost'], 2)



    def verifyBond4(self, record):
        """
        last bond in HKD HTM bond section,
        samples/00._Portfolio_Consolidation_Report_AFBH1 1804.xls
        """
        self.assertEqual('XS1036272570', record['isin'])
        self.assertEqual('bond', record['type'])
        self.assertEqual('HKD', record['currency'])
        self.assertEqual(1800000000, record['quantity'])
        self.assertAlmostEqual(6.00, record['coupon'])
        self.assertEqual('2018-3-10', record['interest start day'])
        self.assertAlmostEqual(100, record['average cost'])
        self.assertAlmostEqual(100, record['amortized cost'])
        self.assertAlmostEqual(0, record['total amortized gain loss'])
        self.assertAlmostEqual(1800000000, record['total cost HKD'])
        self.assertAlmostEqual(15386301.38, record['accrued interest HKD'], 2)
        self.assertAlmostEqual(1815386301.38, record['total amortized cost HKD'], 2)
        self.assertAlmostEqual(0, record['total amortized gain loss HKD'])
        self.assertAlmostEqual(0, record['FX gain loss HKD'])
        self.assertAlmostEqual(0.0262, record['percentage of fund'], 6)