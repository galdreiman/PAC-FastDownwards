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

		for repeat in range (2): # ./logistics -a 3 -c 5 -s 3 -p 2
			for a in range(5,10):
				for c in range(a,a+3):
					for s in range(3,7):
						for p in range(2,5):
							with open("prob_"+self.domain + str(repeat)+ str(a)+ str(c) + str(s)+ str(p) + ".pddl", "w+") as output:
								
								args = " -a " + str(a) + " -c " + str(c) + " -s " + str(s) + " -p " + str(p) 
								command ="./logistics"
								x= command + args
								print x
								subprocess.call(x, stdout=output, shell=True);



if __name__ == '__main__':
	exp = experiment_suit()
	exp.start_generate()