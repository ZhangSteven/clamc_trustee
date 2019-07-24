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
from itertools import takewhile, chain, filterfalse
from functools import reduce, partial
import re
from os.path import join
from datetime import datetime
from collections import namedtuple
from utils.iter import pop, firstOf
from utils.excel import worksheetToLines
from utils.utility import writeCsv
from clamc_datafeed import feeder
from clamc_trustee.report import getExcelFiles
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



def fileToTSCF(data, file):
	"""
	[Dictionary] data, [String] file => [Iterable] TSCF rows

	data: a dictionary mapping a bond to its purchase cost and yield at cost
	file: a Geneva tax lot appraisal report (Excel)	
	"""
	print('fileToTSCF(): working on {0}'.format(file))

	glueTogether = lambda L: reduce(chain, L, [])
	return glueTogether(map(partial(tscfRows, data)
						   , bonds(fileToLines(file))))



def folderToTSCF(folder):
	"""
	[String] folder => [Iterable] TSCF rows

	folder: a folder containing the historical data file and all the Geneva
		tax lot appraisal report files (Excel).
	"""
	isHistoricalDataFile = lambda f: f.split('\\')[-1].startswith('CLO Holdings')
	dataFile = firstOf(isHistoricalDataFile, getExcelFiles(folder))
	if (dataFile == None):
		print('folderToTSCF(): data file not found')
		raise ValueError
	else:
		print('folderToTSCF(): data file: {0}'.format(dataFile))

	historicalData = toDictionary(getRawPositions(fileToLines(dataFile)))

	glueTogether = lambda L: reduce(chain, L, [])
	return glueTogether(map(partial(fileToTSCF, historicalData)
						   , filterfalse(isHistoricalDataFile
						   				, getExcelFiles(folder))))




def writeTSCF(folder):
	"""
	[String] folder => write an output csv in the folder.
	"""
	headRows = [
				 ['Upload Method', 'INCREMENTAL', '', '', '', '']
			   , [ 'Field Id', 'Security Id Type', 'Security Id'
			   	 , 'Account Code', 'Numeric Value', 'Char Value']
			   ]

	writeCsv(join(folder, 'f3321tscf.htm.' + datetime.now().strftime('%Y%m%d') + '.inc')
			, chain(headRows, folderToTSCF(folder)))



if __name__ == '__main__':
	from clamc_trustee.utility import get_current_path
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	"""
	Create a TSCF upload file to upload two data fields for bond positions in
	CLO bond portfolios on Bloomberg AIM.

	To complete this task, we need:

	(1) Obtain the data file that contains the purchase cost and yield at
		cost for all the bond positions. This file should have its file
		name starting with "CLO Holdings", and 3 columns named as
		"ISIN", "Purchase Cost" and "Yield at Cost".

	(2) Geneva tax lot appraisal reports (Excel format) for all the CLO
		bond portfolios (12229, 12366, 12549, 12630 and 12734). The program
		does not check which portfolios are there, it simply grabs all the
		tax lot appraisal reports in the folder and generate upload file
		for them.

	(3) Save all the above files into the folder "trustee_historical".

	For a sample of the files, see "samples\test_historical".

	"""
	writeTSCF('trustee_historical')