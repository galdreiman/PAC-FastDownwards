#! /usr/bin/env python

"""Solve some tasks with A* and the LM-Cut heuristic."""

import os
import subprocess

from lab.steps import Step
from lab.environments import LocalEnvironment
from downward.experiment import DownwardExperiment
from downward.reports.absolute import AbsoluteReport
from downward.reports.hstar_2_h_stat import HstarToHRatioAndStatistics
from downward import suites
from downward.reports.MyPlot import ProblemPlotReport


EXPPATH = 'PAC_Preprocess_Output'
REPO = os.path.expanduser('~/gal-dreiman/downward')
ENV = LocalEnvironment(processes=4)

CONFIGS = [('lmcut', ['--search', 'astar(lmcut())']) ]
ATTRIBUTES = ['coverage', 'expansions','initial_h_value','cost','hstar_to_h','statistics','commualtive_hstar_to_h']


exp = DownwardExperiment(path=EXPPATH, repo=REPO, environment=ENV, limits={'search_time': 300})
# exp.add_suite({'grid','ferry','logistics'})
#exp.add_suite({'grid:prob_grid_29982290.pddl'})
# exp.add_suite({'airport:p45-domain.pddl'})
# exp.add_suite({'blocks'})
#exp.add_suite({'blocks','tpp','storage',})
# exp.add_suite({'blocks','tpp','schedule','storage'})
#exp.add_suite({'blocks','tpp','storage','schedule','logistics00','rovers','satellite','trucks'})


#exp.add_suite({'blocks', 'tpp','storage', 'schedule','rovers'})
#exp.add_suite({'satellite','trucks',})
exp.add_suite({'tpp','storage','rovers'})


# exp.add_suite({'blocks:probBLOCKS-8-0.pddl','blocks:probBLOCKS-8-1.pddl','blocks:probBLOCKS-4-0.pddl','blocks:probBLOCKS-5-1.pddl'})
#exp.add_suite({'gripper:prob02.pddl'})
# exp.add_suite({'zenotravel','trucks-strips','sokoban-sat11-strips','philosophers'})


for nick, config in CONFIGS:
    exp.add_config(nick, config)

# Make a report containing absolute numbers (this is the most common report).
file_name_for_report = 'report_' + nick +'.html'
report = os.path.join(exp.eval_dir, file_name_for_report)
file_name_for_preprocess = os.path.join(exp.eval_dir, 'preprocess')
exp.add_report(HstarToHRatioAndStatistics(nick,file_name_for_preprocess,attributes=ATTRIBUTES), outfile=report)

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
