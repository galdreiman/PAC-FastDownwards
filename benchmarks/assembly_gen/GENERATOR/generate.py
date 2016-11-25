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

		for repeat in range (5): # ./freecell -f 10 -c 20 -s 3 -i 2
			for f in range(15,20):
				for c in range(15,25):
					for s in range(2,3):
						for i in range(2,3):
							with open("prob_"+self.domain + str(repeat)+ str(f)+ str(c)+ str(s) + str(i) + ".pddl", "w+") as output:
								
								args = " -f " + str(f) + " -c " + str(c) + " -s " +str(s) + " -i " + str(i)
								command ="./freecell"
								x= command + args
								print x
 								subprocess.call(x, stdout=output, shell=True);



if __name__ == '__main__':
	exp = experiment_suit()
	exp.start_generate()