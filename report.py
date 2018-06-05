# coding=utf-8
# 
# Use records from china life trustee excel files to generate report
# we need.
#

from clamc_trustee.trustee import readFileToRecords, groupToRecord, \
									writeCsv, recordsToRows
from functools import reduce
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



def readFiles(folder):
	"""
	[string] folder => [list] records

	Read all the files in a folder and return a list of records from 
	those files.
	"""
	from os import listdir
	from os.path import isfile, join
	fileList = [join(folder, f) for f in listdir(folder) if isfile(join(folder, f))]
	return reduce(lambda x,y: x+y, map(readFileToRecords, fileList), [])



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



def writeHtmRecords(folder):
	"""
	Read files under folder and write the consolidated report for all
	HTM bonds in those files into a csv
	"""
	def htmBond(record):
		if record['type'] == 'bond' and record['accounting'] == 'htm':
			return True
		return False

	records = readFiles(folder)
	records = list(consolidateRecords(filter(htmBond, records)))
	writeCsv('htm bond consolidated.csv', recordsToRows(records))



if __name__ == '__main__':
	from os.path import join
	from clamc_trustee.utility import get_current_path
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)

	writeHtmRecords(join(get_current_path(), 'samples'))


