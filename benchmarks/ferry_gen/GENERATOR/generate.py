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

		for repeat in range (5): # ./ferry -l 16 -c 5
			for l in range(15,25):
				for c in range(5,10):
					with open("prob_"+self.domain + str(repeat)+ str(l)+ str(c) + ".pddl", "w+") as output:
						
						args = " -l " + str(l) + " -c " + str(c) 
						command ="./briefcaseworld"
						x= command + args
						print x
						subprocess.call(x, stdout=output, shell=True);



if __name__ == '__main__':
	exp = experiment_suit()
	exp.start_generate()