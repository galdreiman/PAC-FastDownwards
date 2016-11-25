#HstarToHRatio extends AbsoluteReport
#it adds a new attirbute - h*/h(s)
#it expands the coverage table with cost, initial-h and h*/h


#has a bug in which the summary table also have the additional columns

from __future__ import division

import logging
import sys

from lab import reports

from downward.reports.absolute import AbsoluteReport
from lab.reports import Attribute

NOT_AVAILABLE = None

def hstar_to_h(problem_runs):
   
    	for run in problem_runs:
		hstar = run.get('cost')
		h = run.get('initial_h_value')
		if hstar is not None and h is not None:
	        	run['hstar_to_h'] = hstar / h
		else:
			run['hstar_to_h'] = 0

class HstarToHRatio(AbsoluteReport):
    

   

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
	Attribute('hstar_to_h', absolute=True, min_wins=False),
    ])

    def __init__(self, **kwargs):

        AbsoluteReport.__init__(self, **kwargs)
	self.derived_properties.append(hstar_to_h)

    

    def _get_table(self, attribute, domain=None):
	#get original table
	table = AbsoluteReport._get_table(self, attribute, domain)
	
	#if table is coverage, and in problem resolution, take also initial-h-value and add a column of the ratio
	if attribute == 'coverage'   :
		h_attr = Attribute('initial_h_value', min_wins=False, absolute=True)
		h_table = AbsoluteReport._get_table(self, h_attr, domain)
		hstar_attr = Attribute('cost', min_wins=False, absolute=True)
		hstar_table = AbsoluteReport._get_table(self, hstar_attr, domain)
		ratio_attr = Attribute('hstar_to_h', min_wins=False, absolute=True)
		ratio_table = AbsoluteReport._get_table(self, ratio_attr, domain)
        	ratio_col = {}
		h_col = {}
		hstar_col = {}

        	# Filter those rows which have no significant changes
        	for row in table.row_names:
			hstar = hstar_table.get_row(row)
			h = h_table.get_row(row)
			ratio = ratio_table.get(row)
			print ratio
            		ratio_col[row] = ratio['WORK-lmcut']
			h_col[row] = h[0]
			hstar_col[row] = hstar[0]

		table.set_column_order(table.col_names + ['h*'])
        	table.add_col('h*/h(s)', ratio_col)
		table.add_col('h(s)', h_col)
		table.add_col('h*', hstar_col)
 		table.min_wins = None
        	table.colored = False
       
        return table


