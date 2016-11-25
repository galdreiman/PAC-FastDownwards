#! /usr/bin/env python

import os
import sys
import glob
import csv
import re
import subprocess
import time

class experiment_suit(object):


	def __init__(self):
		self.is_lower_bound_pac = 0;  # 1- true, 0- false
		self.is_open_based_pac = 0;  # 1- true, 0- false
		self.epsilon =   [0, 0.1, 0.2, 0.5] # 
		self.delta =    [0.2] # [0, 0.1, 0.2, 0.5] # [0.5] #
		self.weight = 3
		self.exp_results_filename = []

	def start_experiment_suit(self):
		i=1
		# os.environ["DEBUG_LEVEL"]				=str(1)

		os.environ["weight"]					=str(self.weight)
		os.environ["is_lower_bound_pac"]		=str(self.is_lower_bound_pac)
		os.environ["is_open_based_pac"]			=str(self.is_open_based_pac)

		for e in self.epsilon:
			for d in self.delta:
				s = "new_exp_" + str(i) + "-e" + str(e) + "-d" + str(d) + "-w" + str(self.weight) + "-l" + str(self.is_lower_bound_pac)
				self.exp_results_filename.append('/home/shahar/' + s + '.csv')
				print s
				os.environ["exp_name"]					=str(s)
				os.environ["epsilon"]					=str(e)
				os.environ["delta"]						=str(d)
				

				command_1 = "./anytime_test.py --all"
				p1 = subprocess.Popen(command_1, shell=True)
				p1.wait()
				time.sleep(3)

				command_2 = "./collect_stats_post_process.py"
				p2 = subprocess.Popen(command_2, shell=True)
				p2.wait()
				time.sleep(3)


		self.concatenate_result_files()
		time.sleep(3)

		command_3 = "./filter_results.py"
		p3 = subprocess.Popen(command_3, shell=True)
		p3.wait()

	def concatenate_result_files(self):
		topLine = True
		with open('/home/shahar/outfile.csv', 'w') as outfile:
		    for fname in self.exp_results_filename:
		        with open(fname) as infile:
		            for line in infile:
		            	if "algo" in line:
		            		if(topLine):
		                		outfile.write(line)
		                		topLine = False
		                else:
		                	outfile.write(line)

if __name__ == '__main__':
	exp = experiment_suit()
	exp.start_experiment_suit()