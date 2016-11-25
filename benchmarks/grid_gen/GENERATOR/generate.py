#! /usr/bin/env python

import subprocess


import os
import sys
import glob
import csv
import re
import subprocess

class experiment_suit(object):


	def __init__(self):
		self.domain = sys.argv[1]

	def start_generate(self):
		print self.domain

		for repeat in range (7): #-x 10 -y 10  -t 1 -k 2 -l 2 -p 90 >> prob.pddl
			for x in range(8,12):
				for y in range(8,12):
					for t in range(7,12):
						filename = "prob_grid_" + str(repeat)+ str(x)+ str(y)+ str(t) + str(2) + str(2)+ str(90)+ ".pddl"
						print 'filename: ' + filename
						with open(filename, "w+") as output:
							
							args = " -x " + str(x) + " -y " + str(y) + " -t " + str(t) + " -k " + str(2) + " -l " + str(2) + " -p " + str(90) 
							command ="./grid"
							c = command + args
							print c
							subprocess.call(c, stdout=output, shell=True);



if __name__ == '__main__':
	exp = experiment_suit()
	exp.start_generate()