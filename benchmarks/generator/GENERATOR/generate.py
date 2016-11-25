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

		for repeat in range (200):
			for d in range(4,5):
				for m in range(4,6):
					for h in range(1):
						with open("prob_"+self.domain + str(repeat)+ str(d)+ str(m)+ str(h) + ".pddl", "w+") as output:
							
							args = " -d 4 -m 6 -h 90"
							command ="./assembly"
							x= command + args
 							subprocess.call(x, stdout=output, shell=True);



if __name__ == '__main__':
	exp = experiment_suit()
	exp.start_generate()