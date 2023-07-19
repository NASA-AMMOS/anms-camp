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
import logging
import os
import sys
import unittest
import jinja2
from ace import AdmSet, Checker
from camp.generators.lib.campch_roundtrip import H_Scraper, C_Scraper
from camp.generators import (
    create_sql,
    create_gen_h,
    create_agent_c,
    create_mgr_c,
    create_impl_h,
    create_impl_c,
)
from .util import TmpDir


LOGGER = logging.getLogger(__name__)
#: Directory containing this file
SELFDIR = os.path.dirname(__file__)


class BaseTest(unittest.TestCase):
    ''' Abstract base for generators
    '''

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
        self._admset = AdmSet()

    def tearDown(self):
        del self._dir

    def _get_adm(self, file_name):
        ''' Read an ADM file from the 'tests/data' directory.
        '''
        admfile = os.path.join(SELFDIR, 'data', file_name)
        LOGGER.info("Loading %s ... ", admfile)
        adm = self._admset.load_from_file(admfile)
        errs = Checker(self._admset.db_session()).check(adm)
        self.assertEqual([], errs)
        return adm

    def _today_datestamp(self):
        ''' Get a datestamp for files created today.
        '''
        return datetime.date.today().strftime('%Y-%m-%d')


class TestCreateSql(BaseTest):

    def test_create_sql(self):
        adm = self._get_adm('test_adm.json')
        outdir = os.path.join(os.environ['XDG_DATA_HOME'], 'out')

        writer = create_sql.Writer(self._admset, adm, outdir, dialect='pgsql')
        self.assertEqual(
            os.path.join(outdir, 'amp-sql', 'Agent_Scripts', 'adm_test_adm.sql'),
            writer.file_path()
        )

        buf = io.StringIO()
        writer.write(buf)

        tmpl = self._tmpl_env.get_template('test_adm.pgsql.sql.jinja')
        content = tmpl.render(datestamp=self._today_datestamp())
        self.assertEqual(content, buf.getvalue())


class TestCreateCH(BaseTest):

    def test_create_impl_h_noscrape(self):
        adm = self._get_adm('test_adm.json')
        outdir = os.path.join(os.environ['XDG_DATA_HOME'], 'out')

        writer = create_impl_h.Writer(self._admset, adm, outdir, H_Scraper(None))
        self.assertEqual(
            os.path.join(outdir, 'agent', 'adm_test_adm_impl.h'),
            writer.file_path()
        )

        buf = io.StringIO()
        writer.write(buf)

        tmpl = self._tmpl_env.get_template('gen_ch/agent/adm_test_adm_impl.h.jinja')
        content = tmpl.render(datestamp=self._today_datestamp())
        self.assertEqual(content, buf.getvalue())

    def test_create_impl_c_noscrape(self):
        adm = self._get_adm('test_adm.json')
        outdir = os.path.join(os.environ['XDG_DATA_HOME'], 'out')

        writer = create_impl_c.Writer(self._admset, adm, outdir, C_Scraper(None))
        self.assertEqual(
            os.path.join(outdir, 'agent', 'adm_test_adm_impl.c'),
            writer.file_path()
        )

        buf = io.StringIO()
        writer.write(buf)

        tmpl = self._tmpl_env.get_template('gen_ch/agent/adm_test_adm_impl.c.jinja')
        content = tmpl.render(datestamp=self._today_datestamp())
        self.assertEqual(content, buf.getvalue())

    def test_create_gen_h(self):
        adm = self._get_adm('test_adm.json')
        outdir = os.path.join(os.environ['XDG_DATA_HOME'], 'out')

        writer = create_gen_h.Writer(self._admset, adm, outdir)
        self.assertEqual(
            os.path.join(outdir, 'shared', 'adm', 'adm_test_adm.h'),
            writer.file_path()
        )

        buf = io.StringIO()
        writer.write(buf)

        tmpl = self._tmpl_env.get_template('gen_ch/shared/adm/adm_test_adm.h.jinja')
        content = tmpl.render(datestamp=self._today_datestamp())
        self.assertEqual(content, buf.getvalue())

    def test_create_mgr_c(self):
        adm = self._get_adm('test_adm.json')
        outdir = os.path.join(os.environ['XDG_DATA_HOME'], 'out')

        writer = create_mgr_c.Writer(self._admset, adm, outdir)
        self.assertEqual(
            os.path.join(outdir, 'mgr', 'adm_test_adm_mgr.c'),
            writer.file_path()
        )

        buf = io.StringIO()
        writer.write(buf)

        tmpl = self._tmpl_env.get_template('gen_ch/mgr/adm_test_adm_mgr.c.jinja')
        content = tmpl.render(datestamp=self._today_datestamp())
        self.assertEqual(content, buf.getvalue())

    def test_create_agent_c(self):
        adm = self._get_adm('test_adm.json')
        outdir = os.path.join(os.environ['XDG_DATA_HOME'], 'out')

        writer = create_agent_c.Writer(self._admset, adm, outdir)
        self.assertEqual(
            os.path.join(outdir, 'agent', 'adm_test_adm_agent.c'),
            writer.file_path()
        )

        buf = io.StringIO()
        writer.write(buf)

        tmpl = self._tmpl_env.get_template('gen_ch/agent/adm_test_adm_agent.c.jinja')
        content = tmpl.render(datestamp=self._today_datestamp())
        self.assertEqual(content, buf.getvalue())
