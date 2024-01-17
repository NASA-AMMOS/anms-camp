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
''' This module creates the h file for the public portions of an ADM.
'''

import os
from typing import TextIO
from camp.generators.lib import campch
from camp.generators.lib import camputil as cu
from camp.generators.lib import campsettings as cs
from camp.generators.base import AbstractWriter, CHelperMixin
from ace import models


class Writer(AbstractWriter, CHelperMixin):
    ''' The common header file writer.
    '''

    def file_path(self) -> str:
        # Interface for AbstractWriter
        return os.path.join(self.out_path, "shared", "adm", f"adm_{self.adm.norm_name}.h")

    def write(self, outfile: TextIO):
        # Interface for AbstractWriter

        campch.write_h_file_header(outfile, f"adm_{self.adm.norm_name}.h")

        self.write_defines(outfile)
        self.write_includes(outfile)
        outfile.write(campch.make_cplusplus_open())
        self.write_adm_template_documentation(outfile)

        self.write_agent_nickname_definitions(outfile)
        self.write_metadata_definitions(outfile)

        self.write_edd_definitions(outfile)
        self.write_variable_definitions(outfile)
        self.write_rptt_definitions(outfile)
        self.write_tblt_definitions(outfile)
        self.write_ctrl_definitions(outfile)
        self.write_const_definitions(outfile)
        self.write_macro_definitions(outfile)
        self.write_op_definitions(outfile)

        self.write_initialization_functions(outfile)

        outfile.write(campch.make_cplusplus_close())
        self.write_endifs(outfile)

    #
    # Writes the #defines for the generated file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned from get_adm_names
    #
    def write_defines(self, outfile):
        name_upper = self.adm.norm_name.upper()
        ns_upper = self.adm.norm_namespace.upper()
        defines_str = """\

#ifndef ADM_{0}_H_
#define ADM_{0}_H_
#define _HAVE_{1}_ADM_
#ifdef _HAVE_{1}_ADM_
"""
        outfile.write(defines_str.format(name_upper, ns_upper))

    #
    # Writes the end ifs for at the end of the file
    # h_file is an open file desciptor to write to
    # name and ns are the names returned by get_adm_names()
    #
    def write_endifs(self, outfile):
        name_upper = self.adm.norm_name.upper()
        ns_upper = self.adm.norm_namespace.replace("/", "_").upper()
        endifs_str = """\

#endif /* _HAVE_{1}_ADM_ */
#endif /* ADM_{0}_H_ */
"""
        outfile.write(endifs_str.format(name_upper, ns_upper))

    #
    # Writes the includes statements for this generated file
    # h_file is an open file descriptor to write to
    # ns is the ns returned from get_adm_names()
    #
    def write_includes(self, outfile):
        files = ["shared/utils/nm_types.h", "shared/adm/adm.h" ]

        outfile.write(campch.make_includes(files))

    #
    # Writes the ADM template documentation for this generated file
    # h_file is an open file descriptor to write to
    # name is the colon-deliminated name returned from get_adm_names()
    #
    def write_adm_template_documentation(self, outfile):
        header_str = campch.make_formatted_comment_header("ADM TEMPLATE DOCUMENTATION", True, False)
        documentation_str = """\
{} *
 * ADM ROOT STRING:{}
 */
"""
        outfile.write(documentation_str.format(header_str, self.adm.norm_namespace))

        g_var_idx = "g_" + self.adm.norm_namespace.replace("/", "_").lower() + "_idx"
        outfile.write("extern vec_idx_t {}[11];\n".format(g_var_idx))

    #
    # Writes the agent nickname #defines enum to the file
    #
    def write_agent_nickname_definitions(self, outfile):
        header_str = campch.make_formatted_comment_header("AGENT NICKNAME DEFINITIONS", True, True)
        outfile.write(header_str)

        ns = self.adm.norm_namespace.lower()
        enum_name = cu.make_enum_name_from_str(ns)
        outfile.write("#define {0} {1}\n".format(enum_name, self.adm.enum))

    #
    # Function for formatting the description field in the tables.
    # Wraps the description nicely and fills other cells in the
    # row with empty spaces. Returns the string result
    #
    # descr is the string to format as a description.
    # desc_col_sz is the size of the description column to fit to
    # col_sizes_before is an array of the sizes for the columns to the left of the description column
    # col_sizes_after is an array of the sizes for the columns to the right of the description column
    #
    def format_table_description(self, descr, desc_col_sz, col_sizes_before, col_sizes_after):
        result = []
        descr = descr.strip()

        # make the format for the description based on the size of the description column
        desc_fmt = '%-' + str(desc_col_sz) + '.' + str(desc_col_sz) + 's'

        # create string that will fill columns to the left of the description column with white space
        start_next_row = " * |"
        for col_sz in col_sizes_before:
            start_next_row = (start_next_row + (" " * col_sz) + "|")

        # create string that will fill columns to the right of the description column with white space
        fill_this_row = "|"
        for col_sz in col_sizes_after:
            fill_this_row = (fill_this_row + (" " * col_sz) + "|")
        fill_this_row = fill_this_row + "\n"

        # split the description because descriptions may contain new lines
        lines = descr.splitlines()
        num_lines = len(lines)

        # For each line of the description, cut it to the right length,
        # and fill the columns before and after with empty space
        for line_idx in range(0, num_lines):

            # This to wrap nicely inside the column
            line = lines[line_idx].strip()

            while len(line) > desc_col_sz:
                left, right = line[:desc_col_sz], line[desc_col_sz:]

                result.append(desc_fmt % (left))
                result.append(fill_this_row)
                result.append(start_next_row)
                line = right

            result.append(desc_fmt % (line))

            # If there are still lines to write, fill the row and start a new one
            if(line_idx < num_lines-1):
                result.append(fill_this_row)
                result.append(start_next_row)

        return "".join(result)

    #
    # Formats and returns a table entry (with following divider line) with
    # the passed name, ari, description, and type (ttype)
    #
    # XXX: ari isn't currently part of the table. Keeping as a parameter to this
    # function because we might want to include it again in the future
    #
    # Centered is True if the entries should be centered in their columns, False
    # if not.
    #
    # XXX: should update this function to be a general helper function that operates independent
    # XXX- of the columns present (pass a list of values and sizes for columns, it creates the table)
    # XXX- This would be straightforward, except the description column is treated differently for wrapping.
    #
    def format_table_entry(self, centered, name, desc, ttype, value):

        columns = [name, desc, ttype]
        col_sizes = [21, 38, 7]
        if value:
            columns.append(value)
            col_sizes.append(24)

        desc_idx = 1 # index of the description column, since it needs to be treated slightly differently

        entry_row = " * |"
        divider   = " * +"
        for idx,item in enumerate(columns):
            item = str(item) if item is not None else ''
            col_sz = col_sizes[idx]
            item_len = len(item)

            # if it's bigger than the column, we need to truncate it
            if(item_len > col_sz):
                entry = item[:col_sz]

                # Need to treat description differently unfortunately
                if (idx == desc_idx):
                    entry = self.format_table_description(item, col_sz, col_sizes[:desc_idx], col_sizes[desc_idx+1:])

            # if the caller wanted it centered, calculate and add the whitespace for that
            elif centered:
                total_ws_sz = col_sz - item_len
                half_ws = (" " * int(total_ws_sz / 2))

                entry = half_ws + item + " " + half_ws

            # smaller than column and not centered
            else:
                trailing_ws = (" " * (col_sz - item_len))
                entry = item + trailing_ws

            entry_row = entry_row + entry + "|"
            divider = divider + ('-' * col_sz) + "+"

        entry_row = entry_row + "\n"
        divider   = divider   + "\n"

        return entry_row + divider

    #
    # Calls helper functions to write the header for a definition table to the
    # passed fd with the passed definitions string in the center area
    # results in:
    # ```
    #  * +---------------------+
    #  * |  definitions_str    +
    #  * +---------------------+
    #  * +----+-----------+----+
    #  * |NAME|DESCRIPTION|TYPE|
    #  * +----+-----------+----+
    # ```
    # but spaced to standard width for this file (defined in campch.py)
    #
    # If value_present is True, adds the VALUE column on the right of the TYPE column
    #
    def write_definition_table_header(self, fd, definitions_str, value_present):

        fd.write(campch.make_formatted_comment_header(definitions_str, True, False))

        if value_present:
            fd.write(self.format_table_entry(True, "NAME", "DESCRIPTION", "TYPE", "VALUE"))
        else:
            fd.write(self.format_table_entry(True, "NAME", "DESCRIPTION", "TYPE", ""))

    #
    # Writes the metadata definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names
    # metadata is a list of the metadata to include
    #
    def write_metadata_definitions(self, outfile):
        table   = ""  # the commented table of all metadata (string)
        defines = ""  # the #defines and for all metadata (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.mdat:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace, cs.META, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, obj.type, obj.value)

            defines = defines + "// \"{}\"\n".format(obj.name)
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # Write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper()+" META-DATA DEFINITIONS", True)
        outfile.write(table   + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the edd definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names
    # edds is a list of edds to include
    #
    def write_edd_definitions(self, outfile):
        table   = ""  # the commented table of all edds (string)
        defines = ""  # the #defines and for all edds (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.edd:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace, cs.EDD, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, obj.type, "")
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # Write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper()+" EXTERNALLY DEFINED DATA DEFINITIONS", False)
        outfile.write(table   + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the variable definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names
    # variables is a list of variables to include
    #
    def write_variable_definitions(self, outfile):
        table   = ""  # the commented table of all variables (string)
        defines = ""  # the #defines and for all variables (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.var:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace, cs.VAR, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, obj.type, "")
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # Write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper()+" VARIABLE DEFINITIONS", False)
        outfile.write(table + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the report template definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names()
    # templates is a list of report templates to include
    #
    def write_rptt_definitions(self, outfile):
        table   = ""  # the commented table of all reports (string)
        defines = ""  # the #defines and for all reports (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.rptt:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace, cs.RPTT, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, "TNVC", "")
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # Write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper()+" REPORT DEFINITIONS", False)
        outfile.write(table   + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the table definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names()
    # tbls is a list of tabels to include
    #
    def write_tblt_definitions(self, outfile):
        table   = ""  # the commented table of all tables (string)
        defines = ""  # the #defines and for all tables (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.tblt:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace, cs.TBLT, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, "", "")
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # Write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper()+" TABLE DEFINITIONS", False)
        outfile.write(table + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the control definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names()
    # controls is a list of controls to include
    #
    def write_ctrl_definitions(self, outfile):
        table   = ""  # the commented table of all controls (string)
        defines = ""  # the #defines and for all controls (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.ctrl:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace, cs.CTRL, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, "", "")
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper()+" CONTROL DEFINITIONS", False)
        outfile.write(table + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the constants definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names()
    # constants is a list of constants to include
    #
    def write_const_definitions(self, outfile):
        table   = ""  # the commented table of all controls (string)
        defines = ""  # the #defines and for all controls (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.const:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace, cs.CONST, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, obj.type, obj.value)
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper() + " CONSTANT DEFINITIONS", True)
        outfile.write(table   + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the operator definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names()
    # operators is a list of operators to include
    #
    def write_op_definitions(self, outfile):
        table   = ""  # the commented table of all ops (string)
        defines = ""  # the #defines and for all ops (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.oper:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace,  cs.OP, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, obj.result_type, "")
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper()+" OPERATOR DEFINITIONS", False)
        outfile.write(table   + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the macro definitions and #defines to the file
    # h_file is an open file descriptor to write to
    # name and ns are the values returned by get_adm_names()
    # macros is a list of macros to include
    #
    def write_macro_definitions(self, outfile):
        table   = ""  # the commented table of all macros (string)
        defines = ""  # the #defines and for all macros (string)

        # Create the strings for the #defines and preceeding commented table
        for obj in self.adm.mac:
            hex_str = format(obj.enum, '#04x')
            ari_str = cu.make_ari_name(self.adm.norm_namespace, cs.MACRO, obj)

            table   = table   + self.format_table_entry(False, obj.name, obj.description, "mc", "")
            defines = defines + "#define {0} {1}\n".format(ari_str, hex_str)

        # write everything to file
        self.write_definition_table_header(outfile, self.adm.norm_namespace.upper()+" MACRO DEFINITIONS", False)
        outfile.write(table   + " */\n")
        outfile.write(defines + "\n")

    #
    # Writes the initialization functions' forward declars to the file
    # h_file is an open file descriptor to write to
    # name is the name returned by get_adm_names()
    #
    def write_initialization_functions(self, outfile):
        name = self.adm.norm_namespace
        body = 	(
            "/* Initialization functions. */\n"
            "void {0}_init();\n"
            ).format(name)

        outfile.write(body.format(name))
