# coding=utf-8
# 
# Read holdings from china life trustee excel files. For a sample, see 
# samples/00._Portfolio_Consolidation_Report_AFBH1 1804
#

from xlrd import open_workbook
from functools import reduce
from datetime import datetime
import csv, re

import logging
logger = logging.getLogger(__name__)



def readFileToRecords(fileName):
	"""
	fileName: the file path to the trustee excel file.

	output: a list object, containing records (dictionary object) of
		cash and holding in this file.

	To do:
		1. read first section to retrive portfolio info.
		2. add portfolio info to records.
	"""
	sections = linesToSections(readFileToLines(fileName))
	# valuationDate, portfolioId = fileInfo(sections[0])
	totalRecords = []
	for i in range(1, len(sections)):
		records = sectionToRecords(sections[i])
		if (records[0]['type'] == 'bond' and records[0]['accounting'] == 'htm'):
			records = patchHtmBondRecords(records)
		if (records[0]['type'] == 'bond' or records[0]['type'] == 'equity'):
			records = list(map(modifyDates, map(addIdentifier, records)))

		totalRecords = totalRecords + records
	
	return totalRecords



def readFileToLines(fileName):
	"""
	fileName: the file path to the trustee excel file.
	
	output: a list of lines, each line represents a row in the holding 
		page of the excel file.
	"""
	wb = open_workbook(filename=fileName)
	ws = wb.sheet_by_index(0)
	lines = []
	row = 0
	while row < ws.nrows:
		thisRow = []
		column = 0
		while column < ws.ncols:
			cellValue = ws.cell_value(row, column)
			if isinstance(cellValue, str):
				cellValue = cellValue.replace('\n', ' ')
			thisRow.append(cellValue)
			column = column + 1

		lines.append(thisRow)
		row = row + 1

	return lines



def linesToSections(lines):
	"""
	lines: a list of lines representing an excel file.

	output: a list of sections, each section being a list of lines in that
		section.
	"""
	def notEmptyLine(line):
		for i in range(len(line) if len(line) < 20 else 20):
			if not isinstance(line[i], str) or line[i].strip() != '':
				return True

		return False

	def startOfSection(line):
		"""
		Tell whether the line represents the start of a section.

		A section starts if the first element of the line starts like
		this:

		I. Cash - CNY xxx
		IV. Debt Securities xxx
		VIII. Accruals xxx
		"""
		if isinstance((line[0]), str) and re.match('[IVX]+\.\s+', line[0]):
			return True
		else:
			return False
	# end of startOfSection()

	sections = []
	tempSection = []
	for line in filter(notEmptyLine, lines):
		if not startOfSection(line):
			tempSection.append(line)
		else:
			sections.append(tempSection)
			tempSection = [line]

	return sections



def sectionToRecords(lines):
	"""
	lines: a list of lines representing the section

	output: a list of position records (dictionary objects) in the section.
	"""
	def sectionInfo(line):
		"""
		line: the line at the beginning of the section

		output: return two item: type, accounting treatment,
			type as a string, either 'cash', 'equity', 'bond' or empty string 
				if not the above.
			accounting treatment is either 'htm', 'trading', or empty string
				if not the above.
		"""
		sectionType = ''
		accounting = ''
		if (re.search('\sCash\s', line[0])):
			sectionType = 'cash'
		elif (re.search('\sDebt Securities\s', line[0])):
			sectionType = 'bond'
		elif (re.search('\sEquities\s', line[0])):
			sectionType = 'equity'

		if (re.search('\sHeld for Trading', line[0])):
			accounting = 'trading'
		elif (re.search('\sAvailable for Sales', line[0])):
			accounting = 'afs'
		elif (re.search('\sHeld for Maturity', line[0])):
			accounting = 'htm'

		return sectionType, accounting
	# end of sectionInfo()

	def sectionHeaders(line1, line2, line3):
		"""
		line1, line2, line3: the three lines that hold the field names
			of the holdings. They are assumed to be of equal length.

		output: a list of headers that map the field names containing 
			Chinese character, %, English letters to easy to understand
			header names.
		"""
		def mapFieldName(fieldNameTuple):
			return reduce(lambda x,y : (x+' '+y).strip(), fieldNameTuple)

		headerMap = {
			'': '',

			# for HTM bond
			'項目 Description': 'description',
			'幣值 CCY': 'currency',
			'票面值 Par Amt': 'quantity',
			'利率 Interest Rate%': 'coupon',
			'Interest Start Day': 'interest start day',
			'到期日 Maturity': 'maturity',
			'平均成本 Avg Cost': 'average cost',
			'修正價 Amortized Price': 'amortized cost',
			'成本 Cost': 'total cost',
			'應收利息 Accr. Int.': 'accrued interest',
			'Total Amortized Value': 'total amortized cost',
			'P/L A. Value': 'total amortized gain loss',
			'成本 Cost HKD': 'total cost HKD',
			'應收利息 Acc. Int. HKD': 'accrued interest HKD',
			'總攤銷值 Total A. Value HKD': 'total amortized cost HKD',
			'盈/虧-攤銷值 P/L A. Value HKD': 'total amortized gain loss HKD',
			'盈/虧-匯率 P/L FX HKD': 'FX gain loss HKD',
			'百分比 % of Fund': 'percentage of fund',
			'百份比 % of Fund': 'percentage of fund',

			# for AFS bond
			'市場現價 Market Price': 'market price',
			'Total Mkt Value': 'total market value',
			'P/L M. Value': 'market value gain loss',
			'總市值 Total Mkt Value HKD': 'total market value HKD',
			'盈/虧-市值 P/L M. Value HKD': 'market value gain loss HKD',

			# for equity
			'股數 Share': 'quantity',
			'最近交易日 Latest T. D.': 'last trade day',
			'成本價 Cost': 'total cost',
			'應收紅利 Acc. Dividend': 'accrued dividend',
			'Total M. Value': 'total market value',
			'應收紅利 Acc. Dividend HKD': 'accrued dividend HKD',

			# for cash
			'項目 & 戶口號碼 Description & Account No.': 'description',
			'Avg FX Rate': 'average FX rate',
			'貨幣匯率 Ex Rate': 'portfolio FX rate',
			'盈/虧-匯率 P/L FX HKD Equiv.': 'FX gain loss HKD'
		}

		def mapFieldNameToHeader(fieldName):
			try:
				return headerMap[fieldName]
			except KeyError:
				logger.error('invalid field name \'{0}\''.format(fieldName))
				raise
		# end of mapFieldNameToHeader

		fieldNames = map(mapFieldName, zip(line1, line2, line3))

		"""
		Note: We must convert the headers (map object) to a list before 
		returning it.
		
		As we need to iterate through the headers multiple times, without
		the conversion, the headers will behave like an empty list because
		a generator (map object) can only be iterate through once.
		"""
		return list(map(mapFieldNameToHeader, fieldNames))
	# end of sectionHeaders()

	def findHeaderRowIndex(lines):
		"""
		lines: a list of lines representing the section

		output: the index of the line in the lines that contain header 
			'Description'.
		"""
		i = 0
		while (not lines[i][0].startswith('Description')):
			i = i + 1

		return i
	# end of findHeaderRowIndex()

	def sectionRecords(headers, lines):
		"""
		headers: the list of headers
		lines: the list of lines in the section containing the holding
			records. Note the line representing summary of records (i.e., 
			totals) is not included.

		output: a list of records, each being a dictionary holding a position
			record.
		"""
		def lineToRecord(line):
			headerValuePairs = filter(lambda x: x[0] != '', zip(headers, line))
			return {key: value for (key, value) in headerValuePairs}

		return map(lineToRecord, lines)
	# end of sectionRecords()

	sectionType, accounting = sectionInfo(lines[0])
	i = findHeaderRowIndex(lines)
	headers = sectionHeaders(lines[i-2], lines[i-1], lines[i])

	def addSectionInfo(record):
		record['type'] = sectionType
		record['accounting'] = accounting
		return record

	return list(map(addSectionInfo, sectionRecords(headers, lines[i+1:-1])))



def patchHtmBondRecords(records):
	"""
	records: a list of HTM bond records. On some portfolio, there are 
		multiple records of the same HTM bond. Only the first one has
		description and currency fields filled, the rest have these two
		fields empty.

	output: a list of records where:

	1. All have their description and currency fields filled.
	2. Multiple records on the same bond are consolidated into one.
	"""
	def recordsToGroups(groups, record):
		"""
		Divided the records into sub groups, each group containing records
		of the same bond.
		"""
		if (record['description'] == ''):
			groups[-1].append(record)
		else:
			groups.append([record])

		return groups
	# end of recordsToGroups()

	return list(map(groupToRecord, reduce(recordsToGroups, records, [])))



def groupToRecord(group):
	"""
	group: a list of records of the same bond.

	output: a single record, consolidated from the group of records.
	"""
	if (len(group) == 1):
		return group[0]

	headers = list(group[0].keys())
	def toValueList(record):
		return [record[header] for header in headers]

	# say there are 3 records in the group, for each header, there are 
	# 3 values. we group them as a tuple (v1, v2, v3). For all the headers, 
	# we form a list [(a1, a2, a3), (b1, b2, b3), ...], where (a1, a2, a3) 
	# for header a, (b1, b2, b3) for header b, etc.
	valueTuples = list(zip(*map(toValueList, group)))

	def groupWeight(quantTuple):
		"""
		quantTuple: the tuple containing quantities of each record in
			the group.

		output: the weight of each record based on their quantity, as
			a list.
		"""
		totalQuantity = reduce(lambda x,y: x+y, quantTuple, 0)
		return list(map(lambda x: x/totalQuantity, quantTuple))
	# end of groupWeight()

	weights = groupWeight(valueTuples[headers.index('quantity')])

	def weightedAverage(valueTuple):
		return reduce(lambda x,y: x+y[0]*y[1], zip(weights, valueTuple), 0)
		
	def sumUp(valueTuple):
		return reduce(lambda x,y: x+y, valueTuple, 0)

	def takeFirst(valueTuple):
		return valueTuple[0]

	assert abs(sumUp(weights)-1) < 0.000001, 'invalid weights {0}'.format(weights)
	record = {}
	for (header, valueTuple) in zip(headers, valueTuples):
		if header in ['maturity', 'coupon', 'interest start day',
						'type', 'currency', 'accounting', 'description']:
			record[header] = takeFirst(valueTuple)
		elif header in ['average cost', 'amortized cost']:
			record[header] = weightedAverage(valueTuple)
		else:
			record[header] = sumUp(valueTuple)

	return record



def addIdentifier(record):
	"""
	record: a bond or equity position which has a 'description' field that
	holds its identifier. 

	output: the record, with an isin or ticker field added.
	"""
	identifier = record['description'].split()[0]
	
	# some bond identifiers are not ISIN, we then map them to ISIN
	bondIsinMap = {
		'DBANFB12014':'HK0000175916',	# Dragon Days Ltd 6% 03/21/22
		'HSBCFN13014':'HK0000163607'	# New World Development 6% Sept 2023
	}
	if record['type'] == 'bond':
		try:
			identifier = bondIsinMap[identifier]
		except KeyError:
			pass	# no change

		record['isin'] = identifier

	elif record['type'] == 'equity':
		# FIXME: US equity ticker is not real ticker 
		record['ticker'] = identifier

	return record

	

def modifyDates(record):
	"""
	record: a bond or record position which has fields that hold a date,
		such as interest start day, maturity date, or trade day. But those
		dates hold an Excel ordinal value like 43194.0 (float).

	output: the record with the date value changed to a string representation,
		in the form of 'yyyy-mm-dd'
	"""
	def ordinalToDate(ordinal):
		# from: https://stackoverflow.com/a/31359287
		return datetime.fromordinal(datetime(1900, 1, 1).toordinal() + 
										int(ordinal) - 2)

	def dateToString(dt):
		return str(dt.year) + '-' + str(dt.month) + '-' + str(dt.day)

	for header in ['interest start day', 'maturity', 'last trade day']:
		try:
			record[header] = dateToString(ordinalToDate(record[header]))
		except KeyError:
			pass

	return record



def recordsToRows(records):
	"""
	records: a list of position records with the same set of headers, 
		such as HTM bonds, or AFS bonds, equitys, cash entries.

	headers: the headers of the records
	
	output: a list of rows ready to be written to csv, with the first
		row being headers, the rest being values from each record.
		headers.
	"""
	headers = list(records[0].keys())
	def recordToValues(record):
		return [record[header] for header in headers]

	return [headers] + list(map(recordToValues, records))



def writeCsv(fileName, rows):
	with open(fileName, 'w', newline='') as csvfile:
		file_writer = csv.writer(csvfile)
		for row in rows:
			file_writer.writerow(row)




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	def writeRecords():
		file = 'samples/00._Portfolio_Consolidation_Report_AFBH1 1804.xls'
		records = readFileToRecords(file)

		def cashOnly(record):
			if record['type'] == 'cash':
				return True
			else:
				return False

		writeCsv('cash.csv', recordsToRows(list(filter(cashOnly, records))))

		def HtmBondOnly(record):
			if record['type'] == 'bond' and record['accounting'] == 'htm':
				return True
			return False

		writeCsv('bond.csv', recordsToRows(list(filter(HtmBondOnly, records))))
	# end of writeRecords()
	writeRecords()


	def writeRecords2():
		file = 'samples/00._Portfolio_Consolidation_Report_AFEH5 1804.xls'
		records = readFileToRecords(file)

		def cashOnly(record):
			if record['type'] == 'cash':
				return True
			else:
				return False

		writeCsv('cash2.csv', recordsToRows(list(filter(cashOnly, records))))

		def equityOnly(record):
			if record['type'] == 'equity':
				return True
			return False

		writeCsv('equity.csv', recordsToRows(list(filter(equityOnly, records))))
	# end of writeRecords()
	writeRecords2()


