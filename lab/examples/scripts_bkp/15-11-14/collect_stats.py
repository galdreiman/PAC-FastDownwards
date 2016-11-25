#! /usr/bin/env python


import os
import sys
import glob
import csv
import re

class collect_statistics(object):
	def __init__ (self):
		print ("init...")
		self.table_of_data = [] # algo	weight	domain	instance (problem)	epsilon	delta	PAC condition	expanded	generated	cost	time out
		head_line = ['algo','domain','problem' ,'optimal solution',	'PAC_condition','expanded','generated'	,'epsilon','delta','weight_search','pac_ratio', 'pac_condition','total iterations','num of iteration','search time(sec)', 'time_out']
		self.table_of_data.append(head_line)

	def collect_stats(self):
		print("listing all dirs")
		
		# get all properties files into a list
		result_dirs = glob.glob("/home/shahar/downward/lab/examples/exp_1-e0.5-d0.5-w30/runs-*/*")
		result_dirs.sort()
		

		i =1
		for dir in result_dirs:
			p_file = open(os.path.join(dir,"properties"),'r')
			lines = p_file.read().splitlines()
			
			expansions_all = False
			cost_all	   = False
			new_row = []

			heuristic = ""
			domain = ""
			problem = ""
			epsilon_delta_w = ""
			expansions_all_data = ""
			epsilon = ""
			delta = ""
			weight_search = ""
			generated = ""
			cost_all_data = ""
			search_time = ""
			time_out = ""
			pac_ratio = ""
			pac_condition = []

			#--------------------
			# properties parser
			#--------------------
			for line in lines:
				

				if not cost_all and not expansions_all and "id_string" in line: #   "id_string": "WORK-lmcut:freecell:pfile1",
					pair = line.split()
					#print ("pair = %s"  % pair)
					tupple = pair[1].split(':')
					heuristic = self.clean_string_from_chars(tupple[0])
					domain	= self.clean_string_from_chars(tupple[1])
					problem	= self.clean_string_from_chars(tupple[2])

				if not cost_all and not expansions_all and "experiment_name" in line: #  "experiment_name": "exp-test-e0.25-d0.1-w30",
					pair_2 = line.split(':')
					epsilon_delta_w = self.clean_string_from_chars(pair_2[1]) #  ['exp-test-e0.25-d0.1-w30']

					#get epsilon
					str = epsilon_delta_w[0]
					start = str.index("-e")
					end   = str.index('-d')
					epsilon = str[start+2:end]

					#get delta
					start = str.index('-d')
					end   = str.index('-w')
					delta = str[start+2:end]

					#get weight
					weight_search = str[end+2:]

									
				
				if not cost_all and "expansions_all" in line or expansions_all:  # "expansions_all": [	185 #],
					expansions_all = True
					if "expansions_all" not in line:
						if "translator_total_queue_pushes" in line:
							expansions_all_data = "-1"
							time_out = "time_out"
						else:
							expansions_all_data = self.clean_string_from_chars(line)
  						expansions_all = False



  				if not cost_all and not expansions_all and "generated" in line:    #  "generated": 1367,
  					pair_2 = line.split(':')
					generated = self.clean_string_from_chars(pair_2[1])


  					
  				if not expansions_all and "cost_all" in line or cost_all: #  "cost_all": [	#	10	#],
  					cost_all = True
					if "cost_all" not in line:
						tmp = line.split()
						if "parse-preprocess_wall_clock_time" in tmp[0]:
							cost_all_data = "-1"
						else:
							cost_all_data = self.clean_string_from_chars(tmp[0])
  						cost_all = False
  					
  				if not cost_all and not expansions_all and "search_time" in line and not "search_time_all" in line: #  "search_time": 0.1,
  					pair_2 = line.split(':')
					search_time = self.clean_string_from_chars(pair_2[1])


			#-----------------------------------
			#get PAC results (AWA* improvements)
			#-----------------------------------
			log_file = open(os.path.join(dir,"run.log"),'r')
			lines = log_file.read().splitlines()

			for line in lines:
				if "m_pac_ratio_h" in line: #m_pac_ratio_h      =   2.7
					pac_ratio = line[23:]

				if "U / (m_Initial_H * w)" in line: #U / (m_Initial_H * w)  10/4*1.25 = 2
					tmp = line[23:]
					pac_condition.append(tmp)


			

			#-------------------------
			#fill new row in the table
			#-------------------------
			for k in range(len(pac_condition)):
				#if k > 0:	
				new_row = ["AWA*", domain[0], problem[0], cost_all_data[0], "hstar_to_h", expansions_all_data[0], generated[0], epsilon, delta, weight_search, pac_ratio, pac_condition[0] if pac_condition else "None",len(pac_condition),k+1, search_time[0], time_out ]

				#new_row = ["*", "", "", "", "", "", "", "", "","","", pac_condition[k], "" ]
				self.table_of_data.append(new_row)
			

			p_file.close()
			log_file.close()


	def write_to_file(self, filename):
		with open(filename, 'w') as fp:
		    a = csv.writer(fp, delimiter=',')
		    a.writerows(self.table_of_data)


	def clean_string_from_chars(self,str):
		res = ""

		if (("\"" in str) and ("," in str)):
			res =str.replace("\"", "").replace(",", "")
		elif "\"" in str:
			res =str.replace("\"", "")
		elif "," in str:
			res =str.replace(",", "")
		elif " " in str:
			res =str.replace(" ", "")
		else: 
			res =str

		return res.split()


if __name__ == '__main__':
	cs = collect_statistics()
	cs.collect_stats()
	cs.write_to_file("/home/shahar/exp_1-e0.5-d0.5-w30.csv")
