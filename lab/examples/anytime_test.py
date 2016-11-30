#! /usr/bin/env python

"""Solve some tasks with A* and the LM-Cut heuristic."""

import os
import subprocess
import sys

from lab.steps import Step
from lab.environments import LocalEnvironment
from downward.experiment import DownwardExperiment
from downward.reports.absolute import AbsoluteReport
from downward.reports.hstar_2_h_stat import HstarToHRatioAndStatistics
from downward import suites
from downward.reports.MyPlot import ProblemPlotReport
from lab.EnvHandler import BASE_REPO


EXPPATH = os.environ["exp_name"]
REPO = os.path.expanduser(BASE_REPO)
ENV = LocalEnvironment(processes=4)


# os.environ["exp_name"]	='0'
# os.environ["epsilon"]	='0'
# os.environ["delta"]		='0'
# os.environ["weight"]	='0'
heuristic_func = os.environ["heuristic_func"]


# print "anytime_test"
tmp = 'lazy_anytime_wastar({0}(), w={1}, delta={2}, epsilon={3}, rpac_lower_bound={4}, rpac_open_based={5}, trivial_pac={6}, ratio_based={7}, heuristic_func={8})'.format(\
						heuristic_func,\
						os.environ["weight"], \
						os.environ["delta"], \
						os.environ["epsilon"], \
						os.environ["is_lower_bound_pac"], \
						os.environ["is_open_based_pac"],\
						os.environ["is_trivial_pac"],\
						os.environ["is_ratio_based_pac"],\
	                    heuristic_func)

# print tmp

# print 'exiting...'
# sys.exit(0)
# print 'didnt succeed....'

CONFIGS = [(heuristic_func, ['--search', tmp]) ]
ATTRIBUTES = ['coverage', 'expansions','initial_h_value','cost','hstar_to_h','statistics','commualtive_hstar_to_h']


exp = DownwardExperiment(path=EXPPATH, repo=REPO, environment=ENV, limits={'search_time': 300})
#exp.add_suite({'freecell:pfile5'})

#exp.add_suite({'grid:prob_grid_29982290.pddl','grid:prob_grid_58992290.pddl','grid:prob_grid_0101192290.pddl'})
#exp.add_suite({'grid:prob_grid_29982290.pddl'})
#exp.add_suite({'grid','ferry','logistics'})
#exp.add_suite({'rovers:p01.pddl'})
# exp.add_suite({'blocks:probBLOCKS-8-0.pddl','blocks:probBLOCKS-8-1.pddl','blocks:probBLOCKS-9-0.pddl','blocks:probBLOCKS-9-1.pddl', 'blocks:probBLOCKS-11-1.pddl'})
exp.add_suite({'blocks:probBLOCKS-4-1.pddl'})
# exp.add_suite({'gripper','logistics00','openstacks','pathways','rovers','satellite','trucks'})
# exp.add_suite({'schedule','zenotravel','trucks-strips','sokoban-sat11-strips','philosophers'})
# exp.add_suite({'blocks','tpp','storage',})
# exp.add_suite({'gripper','logistics00','openstacks'})
# exp.add_suite({'rovers','satellite'})
#exp.add_suite({'blocks','storage','tpp'})
#exp.add_suite({'blocks','rovers','satellite','schedule','storage','tpp','trucks'})

#exp.add_suite({'blocks','rovers'})
#exp.add_suite({'storage','tpp','trucks'})
#exp.add_suite({'satellite','schedule'})

#exp.add_suite({'tpp','rovers','storage'})

for nick, config in CONFIGS:
    exp.add_config(nick, config)

# Make a report containing absolute numbers (this is the most common report).
file_name_for_report = 'report_' + nick +'.html'
report = os.path.join(exp.eval_dir, file_name_for_report)
file_name_for_preprocess = os.path.join(exp.eval_dir, 'preprocess')
exp.add_report(AbsoluteReport(attributes=ATTRIBUTES), outfile=report)

# Plot 
sub_dir = 'plots_' + nick
exp.add_step(Step('report-plot-cat',
                  ProblemPlotReport(),
                  exp.eval_dir, os.path.join(exp.eval_dir, sub_dir)))

# "Publish" the results with "cat" for demonstration purposes.
# exp.add_step(Step('publish-report', subprocess.call, ['cat', report]))

# Compress the experiment directory.
# exp.add_step(Step.zip_exp_dir(exp))

# Parse the commandline and show or run experiment steps.
exp()
