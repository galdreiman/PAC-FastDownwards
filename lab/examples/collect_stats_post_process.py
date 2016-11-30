#! /usr/bin/env python


import os
import sys
import glob
import csv
from pathlib import Path
import shutil
from lab.EnvHandler import BASE_REPO


class collect_statistics(object):
	def __init__ (self):
		print ("init...")
		self.exp_name_env = os.environ["exp_name"]
		self.table_of_data = [] # algo	weight	domain	instance (problem)	epsilon	delta	PAC condition	expanded	generated	cost  stop cause	time out
		head_line = ['algo','domain','problem' ,'optimal solution',	'PAC_condition','expanded','generated'	,'epsilon','delta','weight_search','search time(sec)', 'stop cause', 'time_out','heuristic','first_solution','PAC_solution','suboptimality']
		self.table_of_data.append(head_line)

	def collect_stats(self):
		print("listing all dirs")
		
		# get all properties files into a list
		#result_dirs = glob.glob("/home/shahar/downward/lab/examples/%s/runs-*/*" % self.exp_name_env)
		result_dirs = glob.glob(BASE_REPO + "/lab/examples/*/runs-*/*")

		#result_dirs=['/home/shahar/downward/lab/examples/new_exp_lower_11-e0.5-d0.5-w30-l0/runs-00001-00100/00008']
		#result_dirs = glob.glob("/home/shahar/downward/lab/examples/new_exp_lower_11-e0.1-d0.1-w30-l0/runs-00001-00100/*")
		result_dirs.sort()
		#print (result_dirs)
		

		i =1
		for dir in result_dirs:
			if self.exp_name_env not in dir:
				
				continue
			


			p_file = open(os.path.join(dir,"properties"),'r')
			lines = p_file.read().splitlines()
			
			expansions_all = False
			cost_all	   = False
			override_pac_cost = False
			new_row = []

			heuristic = ""
			domain = ""
			problem = ""
			epsilon_delta_w = ""
			expansions_all_data = "-1"
			epsilon = ""
			delta = ""
			weight_search = ""
			generated = "-1"
			cost_all_data = "-1"
			search_time = ""
			time_out = ""
			pac_ratio = ""
			stop_cause = "PAC"
			first_incumbent_sol = "-1"
			optimal_cost = "-1"
			problem_name = ""
			pac_condition = []
			cost = "-1";

			pac_algo = "not-initialized"
			if "1" in os.environ["is_lower_bound_pac"]:
				pac_algo = "lower_bound_pac"
			elif "1" in os.environ["is_open_based_pac"]:
				pac_algo = "open_based_pac"
			elif "1" in os.environ["is_trivial_pac"]:
				pac_algo = "trivial_pac"
			elif "1" in os.environ["is_ratio_based_pac"]:
				pac_algo = "ratio_based_pac"
			

			#--------------------
			# properties parser
			#--------------------
			for line in lines:
				#print line

				if not cost_all and not expansions_all and "id_string" in line: #   "id_string": "WORK-lmcut:freecell:pfile1",
					pair = line.split()
					#print ("pair = %s"  % pair)
					tupple = pair[1].split(':')
					heuristic = self.clean_string_from_chars(tupple[0])[0]
					domain	= self.clean_string_from_chars(tupple[1])
					problem	= self.clean_string_from_chars(tupple[2])

				if not cost_all and not expansions_all and "experiment_name" in line: #  "experiment_name": "exp-test-e0.25-d0.1-w30",
					#print line
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
					start = str.index('-w')
					end   = str.index('-l')
					weight_search = str[start+2:end]

									
				
				if not cost_all and ("expansions_all" in line or "Expanded" in line or expansions_all):  # "expansions_all": [	185 #],
					expansions_all = True
					if "expansions_all" not in line:
						if "translator_total_queue_pushes" in line:
							expansions_all_data = "-1"
							time_out = "time_out"
						else:
							expansions_all_data = self.clean_string_from_chars(line)
  						expansions_all = False



  				if not cost_all and not expansions_all and ('generated\":' in line or 'Generated' in line):    #  "generated": 1367,
  					#print line
  					pair_2 = line.split(':')
					generated = self.clean_string_from_chars(pair_2[1])
					#print generated
				#else: 
					#if not cost_all and not expansions_all and 'generated\":' not in line:
						#generated = '-1'

  					
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
			#get PAC Open Based results (AWA* improvements)
			#-----------------------------------
			log_file = open(os.path.join(dir,"run.log"),'r')
			lines = log_file.read().splitlines()

			for line in lines:
				if "m_pac_ratio_h" in line: #m_pac_ratio_h      =   2.7
					pac_ratio = line[23:]

				if "U / (m_Initial_H * w)" in line: #U / (m_Initial_H * w)  10/4*1.25 = 2
					tmp = line[23:]
					pac_condition.append(tmp)

				if "$$$ basic condition" in line:
					stop_cause = "U/max_g_min <= error"
				if "$$ U[" in line:
					i = line.find(']')
					cost = line[5:i]
					override_pac_cost = True
					print '--------------------- cost: %s ---------------------------' %    cost

				if "new f_incumbent" in line:
					first_incumbent_sol = line[25:-1]
				
				try:
					if problem[0] in line:
						problem_name = problem[0]
						optimal_cost = line.split(':')[1]
						print '%%%%%%%%%%%%%%%%%%%%%%%%%%%% optimal_cost: %' % optimal_cost 
				except:
					print 'Failed to get problem name'



			

			#-------------------------
			#fill new row in the table
			#-------------------------
			# for k in range(len(pac_condition)):
				#if k > 0:	
			k=0
			#print expansions_all_data
			expantions = -1;
			if expansions_all_data[0]:
				expansions = expansions_all_data[0]

			#print cost_all_data
			
			if cost_all_data != None and not override_pac_cost:
			 	if cost_all_data[0] != "":
					cost = cost_all_data[0]


			#eliminate time-out runs:
			if( (generated[0] != "-") and (expansions_all_data[0] != "-")):
				new_row = ["AWA*", domain[0], problem[0], \
						optimal_cost,\
						pac_algo,\
						expansions_all_data[0],\
						generated[0] if generated[0] != None  else generated, \
						epsilon, delta, weight_search,\
						search_time[0], stop_cause, time_out, heuristic, first_incumbent_sol,cost, float(optimal_cost)/float(cost) ]
			
				self.table_of_data.append(new_row)
			

			p_file.close()
			log_file.close()



		parent_dirs = glob.glob(BASE_REPO + "/lab/examples/%s*" % self.exp_name_env)
		for dir in parent_dirs:
			print '-------- deleting: %s --------' % (dir)
			shutil.rmtree(dir)


	def write_to_file(self, filename):
		with open(filename, 'w') as fp:
		    a = csv.writer(fp, delimiter=',')
		    a.writerows(self.table_of_data)


	def clean_string_from_chars(self,str):
		res = str

		if (("\"" in str) and ("," in str)):
			res =res.replace("\"", "").replace(",", "")
		if "\"" in str:
			res =res.replace("\"", "")
		if "," in str:
			res =res.replace(",", "")
		if " " in str:
			res =res.replace(" ", "")
		if "[" in str:
			res =res.replace("[", "")
		if "]" in str:
			res =res.replace("]", "")
		if "\'" in str:
			res =res.replace("\'", "")
		if "WORK-" in str: # to clean heuristic info
			res =res.replace("WORK-", "")
		if "\n" in str:
			res =res.replace("\n", "")
		# else:
		# 	res =str

		return res.split()


if __name__ == '__main__':

	# print "collect_statistics"
	# print "exp_name = %s" % os.environ["exp_name"]
	# sys.exit(0)

	cs = collect_statistics()
	cs.collect_stats()
	cs.write_to_file(BASE_REPO + "../%s.csv" % os.environ["exp_name"] ) #os.environ["exp_name"])
