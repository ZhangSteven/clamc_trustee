# coding=utf-8
# 
# Use records from china life trustee excel files to generate report
# we need.
#

from clamc_trustee.trustee import fileToRecords, groupToRecord, \
									writeCsv, recordsToRows
from functools import reduce
from os.path import join
import logging
logger = logging.getLogger(__name__)



def consolidateRecords(records):
	"""
	records => records

	Consolidate records from muotiple portfolios, so that records of the 
	same security are combined into one record.
	"""
	def toNewRecords(record):
		"""
		record => new record

		Duplicate all entries, except the 'portfolio' and 'percentage of 
		fund' fields because they don't make sense in a consolidated record.
		"""
		r = {}
		for key in record:
			if not key in ('percentage of fund', 'portfolio'):
				r[key] = record[key]
		return r
	# end of toNewRecords()

	return map(groupToRecord, recordsToGroups(map(toNewRecords, records)))



def recordsToGroups(records):
	"""
	[iterable] records => [list] groups

	Group a list of records into a list of sub groups, based on the record's
	description. Records with the same description are put into one sub
	group.
	"""
	def addToGroup(groups, record):
		temp = [g for g in groups if g[0]['description'] == record['description']]
		assert len(temp) < 2, 'addToGroup(): too many groups {0}'.format(len(temp))
		if temp == []:
			groups.append([record])	# create new group
		elif (len(temp) == 1):
			temp[0].append(record)	# add to existing group

		return groups

	return reduce(addToGroup, records, [])



def readFiles(folder):
	"""
	[string] folder => [list] records

	Read all the files in a folder and return a list of records from 
	those files.
	"""
	return reduce(lambda x,y: x+y, map(fileToRecords, getExcelFiles(folder)), [])



def getExcelFiles(folder):
	"""
	[string] folder => [list] excel files in folder
	"""
	from os import listdir
	from os.path import isfile

	def isExcelFile(file):
		"""
		[string] file name (without path) => [Bool] is it an Excel file?
		"""
		return file.split('.')[-1] in ('xls', 'xlsx')

	return [join(folder, f) for f in listdir(folder) \
			if isfile(join(folder, f)) and isExcelFile(f)]



def htmBond(record):
	if record['type'] == 'bond' and record['accounting'] == 'htm':
		return True
	return False



def writeHtmRecords(folder):
	"""
	(string) folder => (string) full path to csv file
	side effect: create a csv file in that folder.

	Read files in folder and write a consolidated report for all
	HTM bonds from those files into a csv.
	"""
	records = list(consolidateRecords(filter(htmBond, readFiles(folder))))
	csvFile = join(folder, 'htm bond consolidated.csv')
	writeCsv(csvFile, recordsToRows(records))
	return csvFile



if __name__ == '__main__':
	from clamc_trustee.utility import get_current_path
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	# Put trustee reports in 'trustee_reports' folder then run this
	writeHtmRecords(join(get_current_path(), 'trustee_reports'))


