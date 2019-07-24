# coding=utf-8
# 

import unittest2
from os.path import join
from clamc_trustee.utility import get_current_path
from clamc_trustee.hcost import fileToTSCF, toDictionary, getRawPositions, \
                                fileToLines, folderToTSCF
from utils.iter import firstOf


class TestHCost(unittest2.TestCase):
    """
    Consolidated records from two files.
    """

    def __init__(self, *args, **kwargs):
        super(TestHCost, self).__init__(*args, **kwargs)


    def testFile(self):
        """
        Randomly check a bond's purchase cost and yield at cost
        """
        dataFile = join(get_current_path(), 'samples', 'test_historical'
                       , 'CLO Holdings 2019.06.28.xlsx')
        historicalData = toDictionary(getRawPositions(fileToLines(dataFile)))
        file = join(get_current_path(), 'samples', 'test_historical'
                   , '12229 tax lot 201906.xlsx')
        rows = list(fileToTSCF(historicalData, file))
        self.assertEqual(154, len(rows))    # 12229 has 77 positions
                                            # therefore generates 2 x 77 rows

        bond1_cost = lambda L: True if L[0]=='CD022' and L[2]=='HK0000226404' else False
        bond1_yield = lambda L: True if L[0]=='CD021' and L[2]=='HK0000226404' else False

        item = firstOf(bond1_cost, rows)
        self.assertTrue(item != None)
        self.assertEqual(item[3], '12229')
        self.assertAlmostEqual(item[4], 99.027)

        item = firstOf(bond1_yield, rows)
        self.assertTrue(item != None)
        self.assertEqual(item[3], '12229')
        self.assertAlmostEqual(item[4], 6.2)



    def testFolder(self):
        """
        Read a folder and pick another position to test.
        """
        rows = list(folderToTSCF(join(get_current_path()
                                     , 'samples', 'test_historical')))
        self.assertEqual(240, len(rows))    # 12229 has 77 bond positions,
                                            # 12366 has 43 bond positions,
                                            # so total 120 positions and 240 rows

        bond2_cost = lambda L: True if L[0]=='CD022' and L[2]=='US06428YAA47' and L[3]=='12366' else False
        bond2_yield = lambda L: True if L[0]=='CD021' and L[2]=='US06428YAA47' and L[3]=='12366' else False

        item = firstOf(bond2_cost, rows)
        self.assertTrue(item != None)
        self.assertAlmostEqual(item[4], 100)

        item = firstOf(bond2_yield, rows)
        self.assertTrue(item != None)
        self.assertAlmostEqual(item[4], 5.9)