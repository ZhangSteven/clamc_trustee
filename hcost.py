# coding=utf-8
# 
# Extract and upload two data fields to Bloomberg AIM for China Life
# Overseas portfolios:
# 
# 1. Historical purchase cost
# 2. Yield at cost
# 
# Data provided:
# 
# 1. purchase cost and yield at cost from fixed income team.
# 2. holdings of CLO portfolios from Geneva reports.
#
# Similar to report.py, this module produces a upload file in the following
# format (Bloomberg TSCF upload):
# 
# Upload Method,INCREMENTAL,,,,
# Field Id,Security Id Type,Security Id,Account Code,Numeric Value,Char Value
# CD021,4,HK0000171949,12229,100,100
# CD022,4,HK0000171949,12229,6.5,6.5
# ...

from xlrd import open_workbook
from itertools import takewhile
from functools import reduce
import re
from os.path import join
from collections import namedtuple
from utils.iter import pop
from utils.excel import worksheetToLines
from clamc_datafeed import feeder
import logging
logger = logging.getLogger(__name__)



def getRawPositions(lines):
	"""
	[Iterable] lines => [Iterable] Positions

	lines: rows in a file, where each row is a list of columns
	"""
	nonEmpty = lambda s: s.strip() != ''
	toLower = lambda s: s.lower()
	headers = list(takewhile(nonEmpty, map(toLower, map(str, pop(lines)))))

	position = lambda values: dict(zip(headers, values))
	nonEmptyLine = lambda line: True if len(line) > 0 and nonEmpty(line[0]) else False

	return map(position, takewhile(nonEmptyLine, lines))



def toDictionary(positions):
	"""
	[Iterable] positions => [Dictionary] a dictionary mapping the isin
		code to a namedtuple containing ('purchase_cost', 'yield_at_cost')

	The positions are the raw positions from the file containing all the
	historical cost and yield at cost.
	"""
	Value = namedtuple('Value', ['purchase_cost', 'yield_at_cost'])

	def addEntry(d, position):
		d[position['isin']] = Value(position['purchase cost']
								   , position['yield at cost'])
		return d


	return reduce(addEntry, positions, {})



def bonds(lines):
	"""
	[Iterable] lines => [Iterable] bonds

	lines: lines from a Geneva tax lot appraisal report.
	bonds: a list of tuples representing bond holdings in that report, like
	('12229', 'XS1234567890')
	"""
	isinFromId = lambda id: id.split()[0]
	bondEntry = lambda p: (p['Portfolio'], isinFromId(p['InvestID']))
	return set(map(bondEntry
				  , filter(feeder.isBond
				  		  , feeder.getPositions(lines))))




if __name__ == '__main__':
	from clamc_trustee.utility import get_current_path
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	historicalData = toDictionary(
						getRawPositions(
							worksheetToLines(
								open_workbook(
									join('samples'
										, 'CLO Holdings 2019.06.28.xlsx')
								).sheet_by_index(0))))

	# print(historicalData)
	bb = bonds(worksheetToLines(
					open_workbook(
						join('samples'
							, '12229 tax lot 201906.xlsx')
					).sheet_by_index(0)))
	for b in bb:
		print(b)

