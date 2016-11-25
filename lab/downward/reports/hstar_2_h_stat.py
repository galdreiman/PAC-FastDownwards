#HstarToHRatio extends AbsoluteReport
#it adds a new attirbute - h*/h(s)
#it adds a new statistics table with the coverage, cost, initial-h and h*/h
#it adds a commulative table with h*/h accumulated ratios


from __future__ import division

import logging
import sys
import operator

from lab import reports

from downward.reports.absolute import AbsoluteReport
from lab.reports import Attribute
from lab import tools

NOT_AVAILABLE = None

#Define new attributes for h*/h calculations
def hstar_to_h(problem_runs):
   
    	for run in problem_runs:
		hstar = run.get('cost')
		h = run.get('initial_h_value')
		if hstar is not None and h is not None and h > 0:
	        	run['hstar_to_h'] = hstar / h
		else:
			run['hstar_to_h'] = 0

def statistics(problem_runs):
   
    	for run in problem_runs:
		val = run.get('coverage')
		run['statistics'] = val

def commualtive_hstar_to_h(problem_runs):
   
    	for run in problem_runs:
		run['commualtive_hstar_to_h'] = 0

class HstarToHRatioAndStatistics(AbsoluteReport):



    ATTRIBUTES = dict((str(attr), attr) for attr in [
        Attribute('coverage', absolute=True, min_wins=False),
        Attribute('initial_h_value', min_wins=False),
        Attribute('quality', absolute=True, min_wins=False),
        Attribute('unsolvable', absolute=True, min_wins=False),
        Attribute('search_time', functions=reports.gm),
        Attribute('total_time', functions=reports.gm),
        Attribute('evaluations', functions=reports.gm),
        Attribute('expansions', functions=reports.gm),
        Attribute('generated', functions=reports.gm),
        Attribute('score_*', min_wins=False, functions=[reports.avg, sum]),
		Attribute('hstar_to_h', absolute=True, min_wins=False),#new
		Attribute('statistics', absolute=True, min_wins=False),#new
		Attribute('commualtive_hstar_to_h', absolute=True, min_wins=False),#new
    ])

    def __init__(self, nick, output_file, **kwargs):

        AbsoluteReport.__init__(self, **kwargs)
	#add new attributes to list
	self.derived_properties.append(hstar_to_h)
	self.derived_properties.append(statistics)
	self.derived_properties.append(commualtive_hstar_to_h)
        self.nick = 'WORK-'+nick
	self.outFile = output_file

	#override get_markup so it will add new tables
	#todo, minimize code duplication
    def get_markup(self):

		sections = []
		toc_lines = []

		warnings = self._get_warnings_table()
		if warnings:
		    toc_lines.append('- **[""Unexplained Errors"" #unexplained-errors]**')
		    sections.append(('unexplained-errors', warnings))

		toc_lines.append('- **[""Info"" #info]**')
		sections.append(('info', self._get_general_info()))

		# Index of summary section.
		summary_index = len(sections)

		# Build a table containing summary functions of all other tables.
		# The actual section is added at position summary_index after creating
		# all other tables.
		if self.resolution in ['domain', 'combined']:
		    summary = self._get_empty_table(title='summary')
		    toc_lines.append('- **[""Summary"" #summary]**')

		for attribute in self.attributes:
		    logging.info('Creating table(s) for %s' % attribute)
		    tables = []
		    if self.resolution in ['domain', 'combined']:
		        if self.attribute_is_numeric(attribute):
		            domain_table = self._get_table(attribute)
		            tables.append(('', domain_table))
		            reports.extract_summary_rows(domain_table, summary,
		                                        link='#' + attribute)
		        else:
		            tables.append(('', 'Domain-wise reports only support numeric '
		                'attributes, but %s has type %s.' %
		                (attribute, self._all_attributes[attribute].__name__)))
		    if self.resolution in ['problem', 'combined']:
		        for domain in sorted(self.domains.keys()):
			# add table according to attribute type (this is the only change in get_markup vs the parent
		            if attribute != 'statistics' and attribute != 'commualtive_hstar_to_h':
				tables.append((domain, self._get_table(attribute, domain)))
			    if attribute == 'statistics':
			    	tables.append((domain, self._get_statistics_table(attribute, domain)))
			    if attribute == 'commualtive_hstar_to_h':
					tables.append((domain, self._get_commulative_table(domain)));

	    		parts = []
		    toc_line = []
		    for (domain, table) in tables:
		        if domain:
		            assert table
		            toc_line.append('[""%(domain)s"" #%(attribute)s-%(domain)s]' %
		                            locals())
		            parts.append('== %(domain)s ==[%(attribute)s-%(domain)s]\n'
		                         '%(table)s\n' % locals())
		        else:
		            if table:
		                parts.append('%(table)s\n' % locals())
		            else:
		                parts.append('No task was found where all configurations '
		                             'have a value for "%s". Therefore no '
		                             'domain-wise table can be generated.\n' %
		                             attribute)

		    toc_lines.append('- **[""%s"" #%s]**' % (attribute, attribute))
		    toc_lines.append('  - ' + ' '.join(toc_line))
		    sections.append((attribute, '\n'.join(parts)))

		# Add summary before main content. This is done after creating the main content
		# because the summary table is extracted from all other tables.
		if self.resolution in ['domain', 'combined']:
		    sections.insert(summary_index, ('summary', summary))

		if self.resolution == 'domain':
		    toc = '- ' + ' '.join('[""%s"" #%s]' % (attr, attr)
		                          for (attr, section) in sections)
		else:
		    toc = '\n'.join(toc_lines)

		content = '\n'.join('= %s =[%s]\n\n%s' % (attr, attr, section)
		for (attr, section) in sections)
		return '%s\n\n\n%s' % (toc, content)



    def _get_statistics_table(self, attribute, domain=None):
		#get original table
		table = AbsoluteReport._get_table(self, attribute, domain)
		
		#if attribute is statistics, take also initial-h-value and add a column of the ratio
		if attribute == 'statistics'   :
			h_attr = Attribute('initial_h_value', min_wins=False, absolute=True)
			h_table = AbsoluteReport._get_table(self, h_attr, domain)
			hstar_attr = Attribute('cost', min_wins=False, absolute=True)
			hstar_table = AbsoluteReport._get_table(self, hstar_attr, domain)
			ratio_attr = Attribute('hstar_to_h', min_wins=False, absolute=True)
			ratio_table = AbsoluteReport._get_table(self, ratio_attr, domain)
			ff_h_value_attr = Attribute('initial_ff_h_value', min_wins=False, absolute=True)
			ff_h_value_table = AbsoluteReport._get_table(self, ff_h_value_attr, domain)
			ratio_col = {}
			h_col = {}
			hstar_col = {}
			ff_h_value_col = {}
			h_ff_to_h = []

			for row in table.row_names:
				hstar = hstar_table.get_row(row)
				h = h_table.get_row(row)
				ratio = ratio_table.get(row)
				ratio_col[row] = ratio[self.nick]
				h_col[row] = h[0]
				hstar_col[row] = hstar[0]

				ff_h_val = ff_h_value_table.get_row(row)
				ff_h_value_col[row] = ff_h_val[0]

				# build h-ff/h:
				if(ff_h_val[0] != None and hstar[0] != None):
					if hstar[0] != 0:
						h_ff_to_h.append(hstar[0] / ff_h_val[0])

			table.set_column_order(table.col_names + ['h*'])
			table.add_col('h*/h(s)', ratio_col)
			table.add_col('h(s)', h_col)
			table.add_col('h*', hstar_col)
			table.add_col('ff_h(s)', ff_h_value_col)
			table.min_wins = None
			table.colored = False

			self.save_stat_table_to_file(domain,table)
			self.create_commulative_h_ff_to_h_table(domain, h_ff_to_h)

			return table


    def create_commulative_h_star_table(self, domain):
		#get relevant value from original table
		cost_attr = Attribute('cost', min_wins=False, absolute=True)
		cost_table = AbsoluteReport._get_table(self, cost_attr, domain)

		#define list of costs:
		cost_list = []

		#calculate number of solved problems
		total_solved = 0
		for row in cost_table.row_names:        
			curr_val = cost_table.get(row)
			val = curr_val[self.nick]
			if val > 0:
				total_solved = total_solved + 1
				cost_list.append(val)

		cost_set = list(set(cost_list)) # remove duplicate element
		cost_dict = {}
		for value in sorted(cost_set):
			smaller_than_value_counter = 0;
			for compared_value in cost_list:
				if compared_value <= value:
					smaller_than_value_counter += 1
			cost_dict[value] = smaller_than_value_counter*100 / total_solved


		#write results into .cvs file:
		domain_dir = self.outFile + '/' + domain
		tools.makedirs(domain_dir)
		domain_file = domain_dir + '/' + 'PAC_Commulative_hstar.csv'
		file = open(domain_file, "w")

		sorted_cost_dict_keys = sorted(cost_dict.keys())
		for hstar in sorted_cost_dict_keys: 
			toWrite = str(hstar)+','+str(cost_dict[hstar])+'\n'
			file.write(toWrite)

		file.close()


    def create_commulative_h_ff_to_h_table(self, domain, table):
		print "---------------------------"
		print table
		print "---------------------------"

		#calculate number of solved problems
		total_solved = len(table)

		ratio_set = list(set(table)) # remove duplicate element
		ratio_dict = {}
		for value in sorted(ratio_set):
			smaller_than_value_counter = 0;
			for compared_value in table:
				if compared_value <= value:
					smaller_than_value_counter += 1
			ratio_dict[value] = smaller_than_value_counter*100 / total_solved

		print ratio_dict
		print "---------------------------"

		#write results into .cvs file:
		domain_dir = self.outFile + '/' + domain
		tools.makedirs(domain_dir)
		domain_file = domain_dir + '/' + 'PAC_Commulative_h-ff_to_h-star.csv'
		file = open(domain_file, "w")

		sorted_ratio_dict_keys = sorted(ratio_dict.keys())
		for hstar in sorted_ratio_dict_keys:
			toWrite = str(hstar) + ',' + str(ratio_dict[hstar]) + '\n'
			file.write(toWrite)
		file.close()


    def save_stat_table_to_file(self, domain, table):
		#write results into .cvs file:
		domain_dir = self.outFile + '/' + domain
		tools.makedirs(domain_dir)
		domain_file = domain_dir + '/' + 'PAC_Statistics.csv'
		outfile = open(domain_file, "w")


		first_line = 'Problem,isSolved,h*,ff_h(s),h(s),h*/h(s)\n'
		outfile.write(first_line)
		for prob in table:
			row = table[prob]

			# print '----------------------'
			# print row
			# print '----------------------'

			probName = prob
			isSolved = row['WORK-lmcut']
			h_star = row['h*']
			ff_h = row['ff_h(s)']
			h = row['h(s)']
			ratio = row['h*/h(s)']

			curr_line = str(probName) + ',' + str(isSolved) + ',' + str(h_star) + ',' + str(ff_h) + ',' + str(h) + ',' + str(ratio) + '\n'
			outfile.write(curr_line)
		outfile.close()



#accumulated ratios 
    def _get_commulative_table(self, domain):
		#init new table
		title = 'Commulative'
		columns = {'Percentage','h*/h(s)'}
		min_wins = False
		colored = True
		table = reports.Table(title=title, min_wins=min_wins, colored=colored)
		table.set_column_order(columns)
		link = '#%s' % title
		formatter = reports.CellFormatter(link=link)
		table.cell_formatters[table.header_row][table.header_column] = formatter
		domain_dir = self.outFile + '/' + domain 
		tools.makedirs(domain_dir)	
		domain_file = domain_dir + '/' + 'PAC_Commulative_ratio.csv'
		file = open(domain_file, "w")
		
		#get relevant value from original table
		ratio_attr = Attribute('hstar_to_h', min_wins=False, absolute=True)
		ratio_table = AbsoluteReport._get_table(self, ratio_attr, domain)
		#define arrays to work
		ratios = [0.75,0.8,0.85,0.9,0.95,1,1.05,1.1,1.15,1.2,1.25,1.3,1.35,1.4,1.45,1.5,1.55,1.6,1.65,1.7,1.75,1.8,1.85,1.9,1.95,2,2.05,2.1,2.15,2.2,2.25,2.3,2.35,2.4,2.45,2.5,2.55,2.6,2.65,2.7,2.75,2.8,2.85,2.9,2.95,3.0,3.05,3.1,3.15,3.2,3.25,3.3,3.35,3.4,3.45,3.5,3.55,3.6,3.65,3.7,3.75,3.80,3.85,3.9,3.95,4.0,4.05,4.1,4.15,4.2,2.25,4.3,4.35,4.4,4.45,4.5]
		names = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','za','zb','zc','zd','ze','zf','zg','zh','zi','zj','zk','zl','zm','zn','zo','aa','ab','ac','ad','ae','af','ag','ah','ai','aj','ak','al','am','an','ao','ap','aq','ar','as','at',  'au','av','aw','ax','ay','az','ba','bb','bc','bd','be','bf','bg','bh','bi']
		counter = 0
		
		#calculate number of solved problems
		total_solved = 0
		for row in ratio_table.row_names:        
				curr_val = ratio_table.get(row)
				val = curr_val[self.nick]
				if val > 0:
					total_solved = total_solved + 1
		
		#for each ratio (1,1.05...), find the number of problems with this ratio, calc percentage and add row
		for ratio in ratios:
			_sum = 0
			for row in ratio_table.row_names:        
				curr_val = ratio_table.get(row)
				val = curr_val[self.nick]
				if val <= ratio and val > 0:
					_sum = _sum + 1

			if total_solved == 0:
				_sum_percent = 0
			else:
				_sum_percent = _sum*100 / total_solved
			
			#add new row
			row_to_add = {}
			row_to_add['Percentage'] = _sum_percent
			row_to_add['h*/h(s)'] = ratio
			table.add_row(names[counter],row_to_add)
			counter = counter + 1
			#TODO - save only one ratio per percentage
			toWrite = str(ratio)+','+str(_sum_percent)+'\n'
			file.write(toWrite)

		file.close()

		self.create_commulative_h_star_table(domain)

		return table
	
