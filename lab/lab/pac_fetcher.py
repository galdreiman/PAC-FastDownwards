# -*- coding: utf-8 -*-
#
# lab is a Python API for running and evaluating algorithms.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from glob import glob
import logging
import os
import subprocess
import shutil

from lab import tools
from lab.fetcher import Fetcher



class PACFetcher(Fetcher):
    """
    Collect data from the runs of an experiment and store it in an evaluation
    directory.

    Use this class to combine data from multiple experiment or evaluation
    directories into a (new) evaluation directory.

    .. note::

        Using :py:meth:`exp.add_fetcher() <lab.experiment.Experiment.add_fetcher>`
        is more convenient.

    """
    def fetch_dir(self, run_dir, src_dir, copy_all=False, run_filter=None, parsers=None):
        
        logging.info('Now I will copy for PAC')


        run_filter = run_filter or tools.RunFilter()
        parsers = parsers or []
        # Allow specyfing a list of multiple parsers or a single parser.
        if not isinstance(parsers, (tuple, list)):
            parsers = [parsers]
        # Make sure parsers is a list.
        parsers = list(parsers)

        prop_file = os.path.join(run_dir, 'properties')

        # Somehow '../..' gets inserted into sys.path and more strangely the
        # system lab.tools module gets called.
        # TODO: This HACK should be removed once the source of the error is clear.
        props = tools.Properties(filename=prop_file)
        if props.get('search_returncode') is not None and props.get("coverage") is None:
            logging.warning('search_parser.py exited abnormally for %s' % run_dir)
            logging.info('Rerunning search_parser.py')
            parsers.append(os.path.join(run_dir, '../../search_parser.py'))

        logging.info(props.get('domain'))


        for parser in parsers:
            rel_parser = os.path.relpath(parser, start=run_dir)
            subprocess.call([rel_parser], cwd=run_dir)

        props = tools.Properties(filename=prop_file)
        props = run_filter.apply_to_run(props)
        if not props:
            return None, None
        run_id = props.get('id')
        # Abort if an id cannot be read.
        if not run_id:
            logging.critical('id is not set in %s.' % prop_file)


        #dest_dir = os.path.join(run_dir, *run_id)
        src_dir_hstar2h = src_dir + '/' + props.get('domain') + '/' + 'PAC_Commulative_ratio.csv'
        src_dir_hstar = src_dir + '/' + props.get('domain') + '/' + 'PAC_Commulative_hstar.csv'
        src_dir_stats = src_dir + '/' + props.get('domain') + '/' + 'PAC_Statistics.csv'
        src_dir_hffToh = src_dir + '/' + props.get('domain') + '/' + 'PAC_Commulative_h-ff_to_h-star.csv'
        run_dir_hstar2h = run_dir + '/' + 'PAC_Commulative_ratio.csv'
        run_dir_hstar = run_dir + '/' + 'PAC_Commulative_hstar.csv'
        run_dir_stats = run_dir + '/' + 'PAC_Statistics.csv'
        run_dir_hffToh = run_dir + '/' + 'PAC_Commulative_h-ff_to_h-star.csv'

        logging.info("run_dir: " + run_dir)
        logging.info("src_dir: " + src_dir)
        shutil.copy2(src_dir_hstar2h, run_dir_hstar2h)
        shutil.copy2(src_dir_hstar, run_dir_hstar)
        shutil.copy2(src_dir_stats, run_dir_stats)
        shutil.copy2(src_dir_hffToh, run_dir_hffToh)

        

        return run_id, props

    def __call__(self, src_dir, dest_dir=None, copy_all=False, write_combined_props=True,
                 filter=None, parsers=None, **kwargs):
 
        
        if os.path.isdir(src_dir):
            
            

            run_filter = tools.RunFilter(filter, **kwargs)


            logging.info('Fetching files from %s -> %s' % (src_dir, dest_dir))

            # Get all run_dirs. None will be found if we fetch from an eval dir.
            run_dirs = sorted(glob(os.path.join(dest_dir, 'runs-*-*', '*')))
            total_dirs = len(run_dirs)
            logging.info('Scanning properties from %d run directories' % total_dirs)
            unxeplained_errors = 0
            for index, run_dir in enumerate(run_dirs, start=1):
                loglevel = logging.INFO if index % 100 == 0 else logging.DEBUG
                logging.log(loglevel, 'Scanning: %6d/%d' % (index, total_dirs))
                run_id, props = self.fetch_dir(run_dir, src_dir, copy_all=copy_all,
                                               run_filter=run_filter, parsers=parsers)
                if props is None:
                    continue

                assert run_id, 'Dir %s has no id' % props.get('run_dir')
                if write_combined_props:
                    combined_props['-'.join(run_id)] = props
                if props.get('error', '').startswith('unexplained'):
                    logging.warning('Unexplained error in {run_dir}: {error}'.format(**props))
                    unxeplained_errors += 1

            if unxeplained_errors:
                logging.warning('There were %d runs with unexplained errors.'
                                % unxeplained_errors)
            #tools.makedirs(eval_dir)

        else:
            logging.info('%s is not a valid directory, not using PAC commulative info' % src_dir)
