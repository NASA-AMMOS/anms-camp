#
# Copyright (c) 2023 The Johns Hopkins University Applied Physics
# Laboratory LLC.
#
# This file is part of the Asynchronous Network Managment System (ANMS).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This work was performed for the Jet Propulsion Laboratory, California
# Institute of Technology, sponsored by the United States Government under
# the prime contract 80NM0018D0004 between the Caltech and NASA under
# subcontract 1658085.
#
''' Verify behavior of the "camp" command tool.
'''
import argparse
import datetime
import io
import jinja2
import logging
import os
import sys
from typing import List
import unittest
import camp.tools.camp
from .util import TmpDir


LOGGER = logging.getLogger(__name__)
#: Directory containing this file
SELFDIR = os.path.dirname(__file__)


class TestCamp(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tmpl_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(SELFDIR, 'data')),
            keep_trailing_newline=True
        )

    def setUp(self):
        self.maxDiff = None
        #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        self._dir = TmpDir()

    def tearDown(self):
        del self._dir

    def _walk_files(self, path: str) -> List[str]:
        ''' Print out a list of file contents for test writer use and
        return the full set of relative paths found.
        '''
        relpaths = []
        for root_path, dirs, files in os.walk(path):
            for file_name in files:
                file_path = os.path.join(root_path, file_name)
                relpaths.append(os.path.relpath(file_path, path))
                LOGGER.info('Contents of %s', file_path)
                with open(file_path, 'r') as infile:
                    LOGGER.info('\n%s', infile.read())
        return sorted(relpaths)

    def _today_datestamp(self):
        ''' Get a datestamp for files created today.
        '''
        return datetime.date.today().strftime('%Y-%m-%d')

    def test_parser(self):
        parser = camp.tools.camp.get_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)

    def test_run_sql(self):
        args = argparse.Namespace()
        args.admfile = os.path.join(SELFDIR, 'data', 'test_adm.json')
        args.out = os.path.join(os.environ['XDG_DATA_HOME'], 'out')
        args.only_sql = True
        args.only_ch = False
        args.nickname = 9999
        try:
            exitcode = camp.tools.camp.run(args)
            self.assertEqual(0, exitcode)
        finally:
            got_files = self._walk_files(args.out)
        expect_files = [
            'amp-sql/Agent_Scripts/adm_test_adm.sql',
        ]
        self.assertEqual(expect_files, got_files)

        with open(os.path.join(args.out, 'amp-sql', 'Agent_Scripts', 'adm_test_adm.sql'), 'r') as out:
            tmpl = self._tmpl_env.get_template('test_adm.pgsql.sql.jinja')
            content = tmpl.render(datestamp=self._today_datestamp())
            self.assertEqual(content, out.read())

    def test_run_ch_new(self):
        args = argparse.Namespace()
        args.admfile = os.path.join(SELFDIR, 'data', 'test_adm.json')
        args.out = os.path.join(os.environ['XDG_DATA_HOME'], 'out')
        args.only_sql = False
        args.only_ch = True
        args.nickname = 9999
        args.scrape = False
        try:
            exitcode = camp.tools.camp.run(args)
            self.assertEqual(0, exitcode)
        finally:
            got_files = self._walk_files(args.out)
        expect_files = [
            'agent/adm_test_adm_agent.c',
            'agent/adm_test_adm_impl.c',
            'agent/adm_test_adm_impl.h',
            'mgr/adm_test_adm_mgr.c',
            'shared/adm/adm_test_adm.h',
        ]
        self.assertEqual(expect_files, got_files)
