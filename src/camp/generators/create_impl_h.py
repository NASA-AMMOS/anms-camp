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
''' This module creates the h file for the implementation version of the ADM.
'''

import os
import re
from typing import TextIO
from camp.generators.lib import campch
from camp.generators.lib.campch_roundtrip import H_Scraper
from camp.generators.lib import camputil as cu
from camp.generators.base import AbstractWriter, CHelperMixin
from ace import models


class Writer(AbstractWriter, CHelperMixin):
    ''' The common header file writer.
    '''

    def __init__(self, admset, adm, out_path, scrape: bool):
        super().__init__(admset, adm, out_path)

        full_path = self.file_path()
        scrape_src = full_path if scrape and os.path.exists(full_path) else None
        self._scraper = H_Scraper(scrape_src)

    def file_path(self) -> str:
        # Interface for AbstractWriter
        return os.path.join(self.out_path, "agent", f"adm_{self.adm.norm_name}_impl.h")

    def write(self, outfile: TextIO):
        # Interface for AbstractWriter
        campch.write_h_file_header(outfile, f"adm_{self.adm.norm_name}_impl.h")

        self.write_defines(outfile)

        self._scraper.write_custom_includes(outfile)
        self.write_includes(outfile)
        outfile.write(campch.make_cplusplus_open())

        self._scraper.write_custom_type_enums(outfile)

        # Write this to divide up the file
        outfile.write(campch.make_formatted_comment_header("Retrieval Functions", True, True))

        # Write any custom functions found
        self._scraper.write_custom_functions(outfile)

        # The setup and clean up functions
        outfile.write("void "+self.adm.norm_namespace+"_setup();\n")
        outfile.write("void "+self.adm.norm_namespace+"_cleanup();\n\n")

        self.write_metadata_functions(outfile)
        self.write_constant_functions(outfile)
        self.write_collect_functions(outfile)
        self.write_control_functions(outfile)
        self.write_operator_functions(outfile)
        self.write_table_functions(outfile)

        outfile.write(campch.make_cplusplus_close())
        self.write_endifs(outfile)

    #
    # Writes the #defines and ifdefs to the file
    # new_h is an open file descriptor to write to
    # name is the name returned from get_adm_names()
    #
    def write_defines(self, outfile):
        name_upper = self.adm.norm_name.upper()
        define_str = """\
#ifndef ADM_{0}_IMPL_H_
#define ADM_{0}_IMPL_H_

"""
        outfile.write(define_str.format(name_upper))

    def write_endifs(self, outfile):
        name_upper = self.adm.norm_name.upper()
        endifs_str = """\

#endif /* ADM_{0}_IMPL_H_ */
"""
        outfile.write(endifs_str.format(name_upper))

    #
    # Writes the #includes for the file
    # new_h is an open file descriptor to write to
    #
    def write_includes(self, outfile):
        files = [
            "shared/utils/utils.h",
            "shared/primitives/ctrl.h",
            "shared/primitives/table.h",
            "shared/primitives/tnv.h"
        ]
        outfile.write(campch.make_includes(files))

    #
    # Writes the metadata functions to the passed new_h file
    # name is the name returned from get_adm_names()
    #
    def write_metadata_functions(self, outfile):
        outfile.write("\n/* Metadata Functions */\n")
        for obj in self.adm.mdat:
            _,_,signature = campch.make_meta_function(self.adm, obj)
            outfile.write(signature + ";\n")

    #
    # Writes the constant functions to the passed new_h file
    # name is the name returned from get_adm_names()
    #
    def write_constant_functions(self, outfile):
        outfile.write("\n/* Constant Functions */\n")
        for obj in self.adm.const:
            _,_,signature = campch.make_constant_function(self.adm, obj)
            outfile.write(signature + ";\n")

    #
    # Writes the edd collect functions to the passed file, new_h
    # name is the value returned from get_adm_names
    # edds is a list of the edds to include
    #
    def write_collect_functions(self, outfile):
        outfile.write("\n/* Collect Functions */\n")
        for obj in self.adm.edd:
            _,_,signature = campch.make_collect_function(self.adm, obj)
            outfile.write(signature + ";\n")

    #
    # Writes the control functions to the passed file, new_h
    # name is the value returned from get_adm_names
    # controls is a list of the controls to include
    #
    def write_control_functions(self, outfile):
        outfile.write("\n\n/* Control Functions */\n")
        for obj in self.adm.ctrl:
            _,_,signature = campch.make_control_function(self.adm, obj)
            outfile.write(signature + ";\n")

    #
    # Writes the operator functions to the passed file, new_h
    # name is the value returned from get_adm_names
    # ops is a list of operators to include
    #
    def write_operator_functions(self, outfile):
        outfile.write("\n\n/* OP Functions */\n")
        for obj in self.adm.oper:
            _,_,signature = campch.make_operator_function(self.adm, obj)
            outfile.write(signature + ";\n")

    #
    # Writes the table functions to the passed file, new_h
    # name is the value returned from get_adm_names
    # tables is a list of tables to include
    #
    def write_table_functions(self, outfile):
        outfile.write("\n\n/* Table Build Functions */\n")
        for obj in self.adm.tblt:
            _,_,signature = campch.make_table_function(self.adm, obj)
            outfile.write(signature + ";\n")
