#! /usr/bin/env python

import os
import sys
import glob
import csv
import re
import subprocess

class experiment_suit(object):


	def __init__(self):
		self.epsilon = [0, 0.1, 0.2, 0.5]
		self.delta = [0, 0.1, 0.2, 0.5]
		self.weight = 30
		print "blkasjdflkasjdfl;ksadj"

	def start_experiment_suit(self):
		i=1

		os.environ["weight"]	=str(self.weight)


		for e in self.epsilon:
			for d in self.delta:
				s = "exp_" + str(i) + "-e" + str(e) + "-d" + str(d) + "-w" + str(self.weight)
				print s
				os.environ["exp_name"]	=str(s)
				os.environ["epsilon"]	=str(e)
				os.environ["delta"]		=str(d)

				command_1 = "./anytime_test.py --all"
				p1 = subprocess.Popen(command_1, shell=True)
				p1.wait()

				command_2 = "./collect_stats.py"
				p2 = subprocess.Popen(command_2, shell=True)
				p2.wait()


if __name__ == '__main__':
	exp = experiment_suit()
	exp.start_experiment_suit()