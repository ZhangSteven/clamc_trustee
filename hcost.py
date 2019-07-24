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
from itertools import takewhile, chain
from functools import reduce, partial
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
	[Iterable] lines => [Iterable] bond entries

	lines: lines from a Geneva tax lot appraisal report.
	bond entries: a list of tuples representing bond holdings, like
	('12229', 'XS1234567890')
	"""
	isinFromId = lambda id: id.split()[0]
	bondEntry = lambda p: (p['Portfolio'], isinFromId(p['InvestID']))
	return set(map(bondEntry
				  , filter(feeder.isBond
				  		  , feeder.getPositions(lines))))



def tscfRows(data, bondEntry):
	"""
	[Dictionary] data, [Tuple] Bond entry => [List] TSCF Rows

	data: a dictionary mapping a bond to its purchase cost and yield at cost

	A TSCF upload row consists of 4 elements, i.e.,

	Field Id,Security Id Type,Security Id,Account Code,Numeric Value,Char Value
	
	Since we are uploading two values per bond entry, i.e., purchase cost 
	(CD022) and yield at cost (CD021), then the return value will a list of
	2 lines (each being a list itself) for a bond entry like
	('12229', 'HK0000171949'), such as:

	CD022,4,HK0000171949,12229,98.89,98.89
	CD021,4,HK0000171949,12229,6.535,6.535
	
	If the bond is not found in 'data', then return value will be an empty
	list []. At the same time, it will print out a warning message.
	"""
	portfolio, isin = bondEntry
	try:
		value = data[isin]
		return [ 
				 ['CD022', '4', isin, portfolio, value.purchase_cost, value.purchase_cost]
			   , ['CD021', '4', isin, portfolio, value.yield_at_cost, value.yield_at_cost]
			   ]
	except KeyError:
		print('{0} not found in historical data'.format(bondEntry))
		return []



def fileToLines(file):
	"""
	[String] file => [Iterable] lines

	Read the first sheet of an Excel file and convert its rows to lines
	"""
	return worksheetToLines(open_workbook(file).sheet_by_index(0))




if __name__ == '__main__':
	from clamc_trustee.utility import get_current_path
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	historicalData = toDictionary(
						getRawPositions(
							fileToLines(
								join('samples'
									, 'CLO Holdings 2019.06.28.xlsx'))))

	# print(historicalData)
	bb = bonds(fileToLines(join('samples', '12229 tax lot 201906.xlsx')))


	buildList = lambda L: chain.from_iterable(reduce(chain, L, []))
	for x in buildList(map(partial(tscfRows, historicalData)
						  , bb)):
		print(x)

