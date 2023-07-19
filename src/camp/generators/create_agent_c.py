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
''' This module creates the c file for the public version of the ADM.
'''

import os
from typing import TextIO
from camp.generators.lib import campch
from camp.generators.lib import camputil as cu
from camp.generators.lib import campsettings as cs
from camp.generators.base import AbstractWriter, CHelperMixin
from ace import models


class Writer(AbstractWriter, CHelperMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._g_var_idx = "g_" + self.adm.norm_namespace.lower() + "_idx"

    def file_path(self) -> str:
        # Interface for AbstractWriter
        return os.path.join(self.out_path, "agent", f"adm_{self.adm.norm_name}_agent.c")

    def write(self, outfile: TextIO):
        # Interface for AbstractWriter
        campch.write_c_file_header(outfile, f"adm_{self.adm.norm_name}_agent.c")
        self.write_includes(outfile)

        outfile.write("vec_idx_t {}[11];\n\n".format(self._g_var_idx))

        self.write_init_function(outfile)

        self.write_init_metadata_function(outfile)
        self.write_init_constant_function(outfile)
        self.write_init_edd_function(outfile)
        self.write_init_op_function(outfile)
        self.write_init_var_function(outfile)
        self.write_init_control_function(outfile)
        self.write_init_macro_function(outfile)
        self.write_init_reports_function(outfile)
        self.write_init_tables_function(outfile)

    #
    # Writes all of the #includes for this c file
    #
    # c_file is an open file descriptor to be written to
    # name is the name provided by get_adm_names()
    # retriever is the Retriever class instance for this data
    #
    def write_includes(self, outfile):
        files = [
            "ion.h",
            "platform.h",
            f"adm_{self.adm.norm_name}.h",
            "shared/utils/utils.h",
            "shared/primitives/report.h",
            "shared/primitives/blob.h",
            f"adm_{self.adm.norm_name}_impl.h",
            "agent/rda.h",
        ]
        outfile.write(campch.make_includes(files))

        # Adds #includes calls for all of the adms in the "uses"
        # construct of the ADM
#        files = campch.get_uses_h_files(retriever)
#        c_file.write(campch.make_includes(files))

    #
    # Constructs and writes the main init function for the agent file
    #
    # c_file is an open file descriptor to write to
    # name is the name returned by the call to get_adm_names()
    # retriever is the Retriever class instance for this ADM
    #
    def write_init_function(self, outfile):
        campch.write_init_function(outfile, self.adm, self._g_var_idx, False)

    #
    # Builds a template for the
    # ```
    # adm_add_...(adm_build_ari(...), ...)
    # ```
    # calls with passed collection type and adm name. Should be formatted in the calling
    # function with:
    # return_str.format([0|1](for whether params are present or not), ari_name, ari_amp_type, item[name], item[description])
    #
    # The intention behind this function is to only have to construct these parts once for each
    # collection. Subset of formatted values that need to be substituted for_each_ item in the
    # collection is much smaller.
    #
    # Only trivially different than the function of the same name in create_mgr_c.py
    #
    def make_std_meta_adm_build_template(self, coll):
        add_type = 'cnst' if coll == cs.META else cs.get_sname(coll).lower()
        build_ari_template = campch.make_adm_build_ari_template(coll, self._g_var_idx, False)
        return "\n\tadm_add_" + add_type + "(" + build_ari_template + ", {2});"

    #
    # Constructs and writes the init metadata function
    #
    # c_file is an open file descriptor to write to
    # name is the name returned by a call to get_adm_names()
    # retriever is the Retriever class instance for this ADM
    #
    def write_init_metadata_function(self, outfile):
        body = ""
        add_str_template = self.make_std_meta_adm_build_template(cs.META)

        for obj in self.adm.mdat:
            _,fname,_ = campch.make_meta_function(self.adm, obj)
            ari       = cu.make_ari_name(self.adm.norm_namespace, cs.META, obj)

            body += add_str_template.format("0", ari, fname)

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, cs.META, body)

    #
    # Constructs and writes the init_constants function
    #
    # c_file is an open file descriptor to write to,
    # name is the value returned from get_adm_names()
    #
    def write_init_constant_function(self, outfile):
        body = ""
        add_str = self.make_std_meta_adm_build_template(cs.CONST)

        for obj in self.adm.const:
            parms_tf = "0"
            _,fname,_ = campch.make_constant_function(self.adm, obj)
            ari       = cu.make_ari_name(self.adm.norm_namespace, cs.CONST, obj)

            #FIXME: can const have parameters?
#            if obj.parmspec:
#                parms_tf = "1"

            body += add_str.format(parms_tf, ari, fname)

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, cs.CONST, body)

    #
    # Constructs and writes the init_edd function
    #
    # c_file is an open file descriptor to write to
    # name is the value returned from get_adm_names()
    #
    def write_init_edd_function(self, outfile):
        body = ""
        add_str = self.make_std_meta_adm_build_template(cs.EDD)

        for obj in self.adm.edd:
            parms_tf = "0"
            _,fname,_ = campch.make_collect_function(self.adm, obj)
            ari       = cu.make_ari_name(self.adm.norm_namespace, cs.EDD, obj)

            if obj.parmspec and obj.parmspec.items:
                parms_tf = "1"

            body += add_str.format(parms_tf, ari, fname)

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, cs.EDD, body)


    #
    # Constructs and writes the init_operators function
    #
    # c_file is an open file descriptor to write to,
    # name is the value returned from get_adm_names()
    # operators is a list of operators to add
    #
    def write_init_op_function(self, outfile):
        body = ""
        adm_add_op_template = "\n\tadm_add_"+cs.get_sname(cs.OP)+"(" + self._g_var_idx + "["+cs.get_adm_idx(cs.OP)+"], {0}, {1}, {2});"

        for obj in self.adm.oper:
            ari      = cu.make_ari_name(self.adm.norm_namespace, cs.OP, obj)
            in_types = obj.in_type if obj.in_type else []

            body += adm_add_op_template.format(ari, len(in_types), ari.lower())

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, cs.OP, body)

    #
    # Writes the init_variables body
    # for each variable creates a lyst for its postfix-expr and writes
    # its appropriate adm_add_var function
    #
    def write_init_var_function(self, outfile):
        campch.write_init_var_function(outfile, self.adm, self._g_var_idx, False)

    #
    # Constructs and writes the init_controls function
    #
    # c_file is an open file descriptor to write to,
    # name is the value returned from get_adm_names()
    # controls is a list of controls to add
    #
    def write_init_control_function(self, outfile):
        body = ""
        adm_add_template = "\n\tadm_add_ctrldef(" + self._g_var_idx + "["+cs.get_adm_idx(cs.CTRL)+"], {0}, {1}, {2});"

        for obj in self.adm.ctrl:
            ari = cu.make_ari_name(self.adm.norm_namespace, cs.CTRL, obj)
            parms = obj.parmspec.items if obj.parmspec else []
            body += adm_add_template.format(ari, len(parms), ari.lower())

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, cs.CTRL, body)

    #
    # Constructs and writes the init_macros function
    #
    # c_file is an open file descriptor to write to,
    # name is the value returned from get_adm_names()
    # macros is a list of macros to add
    #
    def write_init_macro_function(self, outfile):
        campch.write_init_macro_function(outfile, self.adm, self._g_var_idx, False)

    #
    # Constructs and writes the init reports function
    #
    # c_file is an open file descriptor to write to
    # name is the name returned by the call to get_adm_names()
    # retriever is the Retriever class instance for this ADM
    #
    def write_init_reports_function(self, outfile):
        campch.write_parameterized_init_reports_function(outfile, self.adm, self._g_var_idx, False)

    #
    # Constructs and writes the init tables function
    #
    # c_file is an open file descriptor to write to
    # name is the name returned by the call to get_adm_names()
    # retriever is the Retriever class instance for this ADM
    #
    def write_init_tables_function(self, outfile):
        campch.write_init_tables_function(outfile, self.adm, self._g_var_idx, False)

