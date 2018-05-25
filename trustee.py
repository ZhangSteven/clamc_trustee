# coding=utf-8
# 
# Read holdings from china life trustee excel files. For a sample, see 
# samples/00._Portfolio_Consolidation_Report_AFBH1 1804
#

from xlrd import open_workbook
import csv, re

import logging
logger = logging.getLogger(__name__)



def readFileToList(fileName):
	"""
	fileName: the file path to the trustee excel file.
	
	output: return a list, each element itself being a list representing
		a row in the holding page of the excel file.
	"""
	wb = open_workbook(filename=fileName)
	ws = wb.sheet_by_index(0)
	list = []
	row = 0
	while row < ws.nrows:
		thisRow = []
		column = 0
		while column < ws.ncols:
			thisRow.append(ws.cell_value(row, column))
			column = column + 1

		list.append(thisRow)
		row = row + 1

	return list



def listToSections(list):
	"""
	list: a list of lines representing an excel file.

	output: a list with each element bing a list containing rows of a 
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
		if isinstance((line[0]), str) and re.match('[IVX]+\\.\\s+', line[0]):
			return True
		else:
			return False



	sections = []
	tempSection = []
	for line in filter(notEmptyLine, list):
		if not startOfSection(line):
			tempSection.append(line)
		else:
			sections.append(tempSection)
			tempSection = [line]

	return sections



def sectionToRecords(list):
	"""
	list: a list of lines representing the section

	output: a list of records in the section.
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
		if (re.search('\sCash\s')):
			sectionType = 'cash'
		elif (re.search('\sDebt Securities\s')):
			sectionType = 'bond'
		elif (re.search('\sEquities\s')):
			sectionType = 'equity'

		if (re.search('\sHeld for Trading')):
			accounting = 'trading'
		elif (re.search('\sAvailable for Sales')):
			accounting = 'afs'
		elif (re.search('\sHeld for Maturity')):
			accounting = 'htm'

		return sectionType, accounting

	def sectionHeaders(line1, line2=[]):
		"""
		line1, line2: the two lines in the section that hold the field names
			of the holdings. They are assumed to be of equal length.

		output: a list of headers that map the field names containing 
			Chinese character, %, English letters to easy to understand
			header names.
		"""
		line = []
		if line2 == []:
			line = line1
		else:
			for i in range(len(line1)):
				line.append(line1[i].strip() + ' ' + line2[i].strip())

		headers = []
		headerMap = {
			
		}
		for item in filter(lambda x: x != ' ', line):
			if (re.search('Description')):
				headers.append('description')
			elif (re.search('CCY')):
				headers.append('currency')
			else:
				try:
					headers.append(headerMap[item])
				except KeyError:
					logger.error('invalid field name {0}'.format(item))
					raise





def writeCsv(list):
	with open('filelist.csv', 'w', newline='') as csvfile:
		file_writer = csv.writer(csvfile)
		for row in list:
			file_writer.writerow(row)




if __name__ == '__main__':
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)
	file = 'samples/00._Portfolio_Consolidation_Report_AFBH1 1804.xls'
	# writeCsv(readFileToList(file))

	sections = listToSections(readFileToList(file))
	writeCsv(sections[5])
