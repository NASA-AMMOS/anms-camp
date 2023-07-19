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
''' This module creates the c file for the implementation version of the ADM.
'''

import os
from typing import TextIO
from camp.generators.lib import campch
from camp.generators.lib.campch_roundtrip import C_Scraper
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
        self._scraper = C_Scraper(scrape_src)

    def file_path(self) -> str:
        # Interface for AbstractWriter
        return os.path.join(self.out_path, "agent", f"adm_{self.adm.norm_name}_impl.c")

    def write(self, outfile: TextIO):
        # Interface for AbstractWriter
        campch.write_c_file_header(outfile, f"adm_{self.adm.norm_name}_impl.c")

        # Custom includes tag
        self._scraper.write_custom_includes(outfile)
        outfile.write(campch.make_includes([
            "shared/adm/adm.h",
            "adm_{}_impl.h".format(self.adm.norm_name.lower())
        ]))

        # Add any custom functions scraped
        self._scraper.write_custom_functions(outfile)

        self.write_setup(outfile)
        self.write_cleanup(outfile)

        self.write_metadata_functions(outfile)
        self.write_constant_functions(outfile)
        self.write_table_functions(outfile)
        self.write_edd_functions(outfile)
        self.write_control_functions(outfile)
        self.write_operator_functions(outfile)

    #
    # function for writing the setup function and
    # custom body if present
    #
    # scraper is the Scraper class object for this ADM
    #
    def write_setup(self, outfile):
        outfile.write("void {}_setup()\n{{\n\n".format(self.adm.norm_namespace.lower()))

        self._scraper.write_custom_body(outfile, "setup")

        outfile.write("}\n\n")

    #
    # function for writing the cleanup function and
    # custom body if present
    #
    # scraper is the Scraper class object for this ADM
    #
    def write_cleanup(self, outfile):
        outfile.write("void {}_cleanup()\n{{\n\n".format(self.adm.norm_namespace.lower()))

        self._scraper.write_custom_body(outfile, "cleanup")

        outfile.write("}\n\n")

    #
    # Writes the metadata functions to the file passed
    # outfile is an open file descriptor to write to
    # name is the value returned from get_adm_names()
    # metadata is a list of metadata to include
    #
    def write_metadata_functions(self, outfile):
        outfile.write("\n/* Metadata Functions */\n\n")

        metadata_funct_str = (
            "\n{0}"
            "\n{{"
            "\n\treturn tnv_from_str(\"{1}\");"
            "\n}}"
            "\n\n")

        for obj in self.adm.mdat:
            _,_,signature = campch.make_meta_function(self.adm, obj)
            outfile.write(metadata_funct_str.format(signature, obj.value))

    #
    # Writes the constant functions to the file passed
    # outfile is an open file descriptor to write to
    # name is the value returned from get_adm_names()
    # constants is a list of constants to include
    #
    def write_constant_functions(self, outfile):
        outfile.write("\n/* Constant Functions */")

        const_function_str = (
            "\n{0}"
            "\n{{"
            "\n\treturn tnv_from_uvast({1});"
            "\n}}"
            "\n")

        for obj in self.adm.const:
            _,_,signature = campch.make_constant_function(self.adm, obj)
            outfile.write(const_function_str.format(signature, getattr(obj, 'value', '')))

    #
    # writes the table functions to the file passed
    # outfile is an open file descriptor to write to
    # name is the value returned from get_adm_names()
    # table is a list of tables to include
    # scraper is the Scraper object associated with this ADM
    #
    def write_table_functions(self, outfile):
        outfile.write("\n/* Table Functions */\n\n")
        table_function_begin_str = (
            "\n{0}"
            "\n{1}"
            "\n{{"
            "\n\ttbl_t *table = NULL;"
            "\n\tif((table = tbl_create(id)) == NULL)"
            "\n\t{{"
            "\n\t\treturn NULL;"
            "\n\t}}"
            "\n\n")
        conditional_body_str = (
            "\n\t{"
            "\n\t\treturn NULL;"
            "\n\t}"
            "\n\n")
        table_function_end_str = "\treturn table;\n}\n\n"

        for obj in self.adm.tblt:
            basename,_,signature = campch.make_table_function(self.adm, obj)
            description          = campch.multiline_comment_format(obj.description or '')

            outfile.write(table_function_begin_str.format(description, signature))

            # Add custom body tags and any scrapped lines found
            self._scraper.write_custom_body(outfile, basename)

            # Close out the function
            outfile.write(table_function_end_str)

    #
    # Writes the edd functions to the file passed
    # outfile is an open file descriptor to write to
    # name is the value returned from get_adm_names()
    # edds is a list of edds to include
    # custom is a dictionary of custom function bodies to include, in the
    # form {"function_name":["line1", "line2",...], ...}
    # scraper is the Scraper object for the current ADM
    #
    def write_edd_functions(self, outfile):
        outfile.write("\n/* Collect Functions */")

        edd_function_begin_str = (
            "\n{0}"
            "\n{1}"
            "\n{{"
            "\n\ttnv_t *result = NULL;"
            "\n")
        edd_function_end_str = "\treturn result;\n}\n\n"

        for obj in self.adm.edd:
            basename,_,signature = campch.make_collect_function(self.adm, obj)
            description          = campch.multiline_comment_format(obj.description or '')
            outfile.write(edd_function_begin_str.format(description, signature))

            # Add custom body tags and any scrapped lines found
            self._scraper.write_custom_body(outfile, basename)

            # Close out the function
            outfile.write(edd_function_end_str)

    #
    # Writes the control functions to the file passed
    # outfile is an open file descriptor to write to
    # name is the value returned from get_adm_names
    # controls is a list of controls to include
    # custom is a dictionary of custom function bodies to include, in the
    # form {"function_name":["line1", "line2",...], ...}
    # scraper is the Scraper class object for this ADM
    #
    def write_control_functions(self, outfile):
        outfile.write("\n\n/* Control Functions */\n")

        ctrl_function_begin_str = (
            "\n{0}"
            "\n{1}"
            "\n{{"
            "\n\ttnv_t *result = NULL;"
            "\n\t*status = CTRL_FAILURE;"
            "\n")
        ctrl_function_end_str = "\treturn result;\n}\n\n"

        for obj in self.adm.ctrl:
            basename,_,signature = campch.make_control_function(self.adm, obj)
            description          = campch.multiline_comment_format(obj.description or '')
            outfile.write(ctrl_function_begin_str.format(description, signature))

            self._scraper.write_custom_body(outfile, basename)

            outfile.write(ctrl_function_end_str)

    #
    # Writes the operator functions to the file passed
    # outfile is an open file descriptor to write to
    # name is the value returned from get_adm_names
    # operators is a list of operators to include
    # custom is a dictionary of custom function bodies to include, in the
    # form {"function_name":["line1", "line2",...], ...}
    # scraper is the Scraper class object for this ADM
    #
    def write_operator_functions(self, outfile):
        outfile.write("\n\n/* OP Functions */\n")

        op_function_begin_str = (
            "\n{0}"
            "\n{1}"
            "\n{{"
            "\n\ttnv_t *result = NULL;"
            "\n")
        op_function_end_str = "\treturn result;\n}\n\n"

        for obj in self.adm.oper:
            basename,_,signature = campch.make_operator_function(self.adm, obj)
            description          = campch.multiline_comment_format(obj.description or '')
            outfile.write(op_function_begin_str.format(description, signature))

            self._scraper.write_custom_body(outfile, basename)

            outfile.write(op_function_end_str)
