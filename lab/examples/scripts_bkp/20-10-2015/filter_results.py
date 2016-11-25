#! /usr/bin/env python


import os
import sys
import glob
import csv
import re



class filter_results(object):

	def __init__ (self):
		print ("init...")

		self.table = []
		self.inFileName = "/home/shahar/outfile.csv"
		self.dictOfProblemNames = dict()
		self.numOfRepeats = 0
		self.firstLine = []

	def doFilter(self):
		print "Filtering..."

		self.readOutFile(self.inFileName)
		self.filterNonRepeatedProblems()
		self.write_to_file("/home/shahar/filtered_outfile.csv")


	def readOutFile(self, filename):
		with open(filename, "r") as ins:
			self.table = []
			for line in ins:
				self.table.append(line.split(","))
		self.firstLine = self.table[0]
		print self.table[1][2]

	def filterNonRepeatedProblems(self):
		print "filterNonRepeatedProblems"
		self.countRepeatedProblems()
		# print self.dictOfProblemNames

		# now, for the filtering...
		recIndx = 0
		for record in self.table:
			probName = record[2]
			probRepeatCount = self.dictOfProblemNames[probName]
			if probRepeatCount != self.numOfRepeats:
				poped = self.table.pop(recIndx)
				print str(poped) +  str(probRepeatCount)
			recIndx += 1


	def countRepeatedProblems(self):
		for record in self.table:
			probName = record[2]

			if probName in self.dictOfProblemNames.keys():
				self.dictOfProblemNames[probName] += 1
			else:
				self.dictOfProblemNames[probName] = 1

			# on the way - count how many time a problem occus (=the max number of repeats)
			if int(self.dictOfProblemNames[probName]) > self.numOfRepeats:
				self.numOfRepeats = int(self.dictOfProblemNames[probName])

		# print "max repeats = " + str(self.numOfRepeats)

	def write_to_file(self, filename):
		self.table.insert(0,self.firstLine)
		with open(filename, 'w') as fp:
		    a = csv.writer(fp, delimiter=',')
		    a.writerows(self.table)

if __name__ == '__main__':

	# print "collect_statistics"
	# print "exp_name = %s" % os.environ["exp_name"]
	# sys.exit(0)

	filter = filter_results()
	filter.doFilter()
	# filter.write_to_file("/home/shahar/%s.csv" % os.environ["exp_name"] ) #os.environ["exp_name"])