# coding=utf-8
# 
# Read holdings from china life trustee excel files, then generate report
# we need.
#

from clamc_trustee.trustee import readFileToRecords, groupToRecord, \
									writeCsv, recordsToRows
from functools import reduce
import logging
logger = logging.getLogger(__name__)



def consolidateRecords(records):
	"""
	records: [iterable] a list of records of the same type, i.e.,
		htm bond, afs bond or equity. Cash is not supported.

	output: [iterable] a new list of consolidated records, where
		multiple records of the same security are consolidated into
		one. Note that when we do consolidation, the 'portfolio' and
		'percentage of fund' fields will be removed because these
		two fields cannot be consolidated.

		The passed in list of records stay untouched.
	"""
	def removeFields(record):
		r = {}
		for key in record:
			if key != 'percentage of fund' and key != 'portfolio':
				r[key] = record[key]

		return r
	# end of removeFields

	return map(groupToRecord, recordsToGroups(map(removeFields, records)))



def readFiles(folder):
	"""
	folder: a folder containing trustee files.

	output: [list] a list of records from all the files.
	"""
	from os import listdir
	from os.path import isfile, join
	fileList = [join(folder, f) for f in listdir(folder) \
						if isfile(join(folder, f))]
	totalRecords = []
	for file in fileList:
		totalRecords = totalRecords + readFileToRecords(file)

	return totalRecords



def recordsToGroups(records):
	"""
	records: [iterable] a list of records for securites of the same type,
		e.g., htm bonds, afs bonds, equities. Cash is not supposed to be
		used here.

	output:  [iterable] a list of record groups, where each group is a list
		object consisting records of the same security.
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



if __name__ == '__main__':
	from os import listdir
	from os.path import isfile, join
	from clamc_trustee.utility import get_current_path
	import logging.config
	logging.config.fileConfig('logging.config', disable_existing_loggers=False)



	def testRecordsToGroups():
		r1 = {'description': 'b1', 'quantity': 100, 'average cost': 20}
		r2 = {'description': 'b2', 'quantity': 150, 'average cost': 60}
		r3 = {'description': 'b1', 'quantity': 300, 'average cost': 24}
		print(recordsToGroups([r1,r2,r3]))

	# testRecordsToGroups()

	def writeHtmRecords():
		records = readFiles(join(get_current_path(), 'samples'))

		def htmBond(record):
			if record['type'] == 'bond' and record['accounting'] == 'htm':
				return True
			return False

		records = list(consolidateRecords(filter(htmBond, records)))
		writeCsv('bond htm consolidated.csv', recordsToRows(records))
	# end of writeHtmRecords()
	writeHtmRecords()


