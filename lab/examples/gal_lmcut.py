#! /usr/bin/env python

"""Solve some tasks with A* and the LM-Cut heuristic."""

import os
import subprocess

from lab.steps import Step
from lab.environments import LocalEnvironment
from downward.experiment import DownwardExperiment
from downward.reports.absolute import AbsoluteReport
from downward import suites
from downward.reports.hstar_2_h import HstarToHRatio

EXPPATH = 'exp-lmcut-no-timeout'
REPO = os.path.expanduser('~/downward')
#Run with 6 processes
ENV = LocalEnvironment(processes=6)
CONFIGS = [('lmcut', ['--search', 'astar(lmcut())'])]

ATTRIBUTES = ['coverage', 'expansions','initial_h_value','cost','hstar_to_h']

#All with timeout
#exp = DownwardExperiment(path=EXPPATH, repo=REPO, environment=ENV, limits={'search_time': 100})
#exp.add_suite(suites.suite_all())

#Only lmcut domains without timeout
exp = DownwardExperiment(path=EXPPATH, repo=REPO, environment=ENV)
exp.add_suite(suites.suite_lmcut_domains())

for nick, config in CONFIGS:
    exp.add_config(nick, config)

# Make a report containing absolute numbers with h*/h values.
report = os.path.join(exp.eval_dir, 'report.html')
exp.add_report(HstarToHRatio(attributes=ATTRIBUTES), outfile=report)

# "Publish" the results with "cat" for demonstration purposes.
exp.add_step(Step('publish-report', subprocess.call, ['cat', report]))

# Compress the experiment directory.
exp.add_step(Step.zip_exp_dir(exp))

# Parse the commandline and show or run experiment steps.
exp()
