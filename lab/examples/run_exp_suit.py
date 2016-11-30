#! /usr/bin/env python

import os
import sys
import glob
import csv
import re
import subprocess
import time
from lab.EnvHandler import BASE_REPO


class experiment_suit(object):


	def __init__(self):
		self.is_trivial_pac 	= 0;  # 1- true, 0- false
		self.is_ratio_based_pac = 0;  # 1- true, 0- false
		self.is_lower_bound_pac = 0;  # 1- true, 0- false
		self.is_open_based_pac 	= 0;  # 1- true, 0- false
		self.epsilon = [0.3] # [0, 0.1, 0.5, 0.9]   [0, 0.1,0.5] #
		self.delta =   [0.3] #[0, 0.5, 0.9] #[0, 0.1, 0.5, 0.9] #[0, 0.1, 0.2, 0.5] # [0.5] # [0.2] #
		self.weight = 3
		self.heuristics = ['lmcut']
		self.exp_results_filename = []

	def start_experiment_suit(self):
		i=1
		# os.environ["DEBUG_LEVEL"]				=str(1)
		for heuristic_method in self.heuristics:
			for conditionIndx in [2,4]:

				self.is_trivial_pac 	= int(conditionIndx == 1)  # 1- true, 0- false
				self.is_ratio_based_pac = int(conditionIndx == 2)  # 1- true, 0- false
				self.is_lower_bound_pac = int(conditionIndx == 3)  # 1- true, 0- false
				self.is_open_based_pac 	= int(conditionIndx == 4)  # 1- true, 0- false

				os.environ["weight"]					=str(self.weight)
				os.environ["is_trivial_pac"]			=str(self.is_trivial_pac)
				os.environ["is_ratio_based_pac"]		=str(self.is_ratio_based_pac)
				os.environ["is_lower_bound_pac"]		=str(self.is_lower_bound_pac)
				os.environ["is_open_based_pac"]			=str(self.is_open_based_pac)
				os.environ["heuristic_func"]			=heuristic_method #"lmcut" # or 'ff'

				if self.is_trivial_pac == 1:
					os.environ["PAC_cond_name"] = "trivial"
				elif self.is_ratio_based_pac == 1:
					os.environ["PAC_cond_name"] = "ratio_based"
				elif self.is_lower_bound_pac == 1:
					os.environ["PAC_cond_name"] = "lower_bound"
				elif self.is_open_based_pac == 1:
					os.environ["PAC_cond_name"] = "open_based"


				for e in self.epsilon:
					for d in self.delta:
						s = "new_exp_" + str(i) + "-e" + str(e) + "-d" + str(d) + "-w" + str(self.weight) + "-l" + str(self.is_lower_bound_pac) + "-c" + str(conditionIndx) + '-h_'+str(heuristic_method)
						self.exp_results_filename.append(BASE_REPO + '/../' + s + '.csv')
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
		with open(BASE_REPO + '/../outfile.csv', 'w') as outfile:
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
