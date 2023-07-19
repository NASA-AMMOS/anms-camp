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
''' This module creates the c file for the manager implementation of the ADM.
'''

import os
from typing import TextIO
from camp.generators.lib import campch
from camp.generators.lib import camputil as cu
from camp.generators.lib import campsettings as cs
from camp.generators.base import AbstractWriter, CHelperMixin
from ace import models


# meta_add_parm() function commonly used by many of the functions in this file
add_parm_template = "\tmeta_add_parm(meta, \"{0}\", {1});\n"

#
# Iterates through all of the parameters passed and returns
# a string with the meta_add_parm(...) calls for all parameters.
# Caller needs to generate `metadata_t *meta` string.
#
def make_add_parms_str(parms):
    add_parms_str = ""
    for parm in parms:
        p_type = cu.make_amp_type_name_from_str(parm.type)
        add_parms_str = add_parms_str + add_parm_template.format(parm.name, p_type)

    return add_parms_str


class Writer(AbstractWriter, CHelperMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._g_var_idx = "g_" + self.adm.norm_namespace.lower() + "_idx"

    def file_path(self) -> str:
        # Interface for AbstractWriter
        return os.path.join(self.out_path, "mgr", f"adm_{self.adm.norm_name}_mgr.c")

    def write(self, outfile: TextIO):
        # Interface for AbstractWriter
        campch.write_c_file_header(outfile, f"adm_{self.adm.norm_name}_mgr.c")

        # calling each of the helper functions to handle the writing of
        # various functions in this file
        self.write_includes(outfile)

        outfile.write("vec_idx_t {}[11];\n\n".format(self._g_var_idx))

        self.write_init_function(outfile)
        self.write_init_metadata(outfile)
        self.write_init_constants(outfile)
        self.write_init_edd_function(outfile)
        self.write_init_ops(outfile)
        self.write_init_variables_function(outfile)
        self.write_init_controls_function(outfile)
        self.write_init_macros(outfile)
        self.write_init_reports(outfile)
        self.write_init_tables(outfile)

    #
    # Writes all of the #includes for this file
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
            "metadata.h",
            "nm_mgr_ui.h"
        ]
        outfile.write(campch.make_includes(files))

        # Adds #includes calls for all of the adms in the "uses"
        # construct of the ADM
        #FIXME: was
        # files = campch.get_uses_h_files(retriever)
        # outfile.write(campch.make_includes(files))

    #
    # Writes the top-level init function that calls all of the other ones
    # c_file is an open file descriptor to write to
    # name is the name returned from get_adm_names()
    #
    def write_init_function(self, outfile):
        campch.write_init_function(outfile, self.adm, self._g_var_idx, True)

    #
    # A lot of the collections in the mgr file follow the same pattern for their init
    # function. This method encapsulates that.
    #
    # c_file is the file to write to, name is the name of the adm,
    # self._g_var_idx is the g_*_idx variable created in the main function
    # coll_type is the type of collection we're working with (cs.META, etc)
    # retriever is the Retriever class instance for this ADM
    #
    # XXX: this is only used by two collections, reconsider breaking this out as a
    # 'standard' (std) method.
    #
    def _write_mgr_std_init_funct(self, outfile, coll_type, objlist):
        body = ""
        coll_decl_str = "\n\tari_t *id = NULL;\n"
        parm_decl_str = "\n\tmetadata_t *meta = NULL;\n"
        add_str_template  = self._make_std_adm_build_add_template(coll_type)
        meta_add_template = campch.make_std_meta_add_coll_template(coll_type, self.adm.norm_namespace)

        added_coll = False
        added_parm = False

        for obj in objlist:
            try:
                # Gather all of the pieces of data we need
                ari      = cu.make_ari_name(self.adm.norm_namespace, coll_type, obj)
                amp_type = cu.make_amp_type_name_from_str(obj.type)
                paramspec = getattr(obj, 'parmspec', None)
                parms    = paramspec.items if paramspec else []

                # format the meta_add_.* template for this item
                meta_add_str = meta_add_template.format(amp_type, obj.name, obj.description)

                # Make the string to add the parms in the function
                add_parms_str = make_add_parms_str(parms)

                # A couple of variables depend on the presence or absence of parms
                parms_tf     = "0"
                if add_parms_str:
                    parms_tf     = "1"
                    meta_add_str = "meta = " + meta_add_str
                    added_parm   = True

                # Add everything to the body of the function
                body += add_str_template.format(parms_tf, ari)
                body += "\n\t" + meta_add_str
                body += add_parms_str

                added_coll = True

            except KeyError as e:
                print("[ Error ] Badly formatted " + cs.get_lname(coll_type) + ". Key not found:")
                print(e)
                raise

        # This ensures that the ari_t *id variable is only declared if it is going to be used.
            # Avoids compiler warnings for unused variables
        if added_parm:
            body = parm_decl_str + body
        if added_coll:
            body = coll_decl_str + body

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, coll_type, body)

    #
    # Writes the init_metadata() function to the open file descriptor passed as c_file
    # name and ns are the values returned from get_adm_names()
    # metadata is a list of the metadata to include
    #
    def write_init_metadata(self, outfile):
        self._write_mgr_std_init_funct(outfile, cs.META, self.adm.mdat)
        return

        body = ""
        coll_decl_str = "\n\tari_t *id = NULL;\n"
        parm_decl_str = "\n\tmetadata_t *meta = NULL;\n"

        meta_add_template = campch.make_std_meta_add_coll_template(cs.CONST, self.adm.norm_namespace)

        # NOTE: this function uses the CONST modifiers for most things, but needs the META IDX here:
        const_idx = cs.get_adm_idx(cs.CONST)
        meta_idx  = cs.get_adm_idx(cs.META)
        add_str_template = self._make_std_adm_build_add_template(cs.CONST).replace(const_idx, meta_idx)

        added_coll = False
        added_parm = False

        for obj in self.adm.mdat:
            # Preliminary; gather all of the pieces of data we need
            ari      = cu.make_ari_name(self.adm.norm_namespace, cs.META, obj)
            amp_type = cu.make_amp_type_name_from_str(obj.type)

            # format the meta_add_.* template for this item
            meta_add_str = meta_add_template.format(amp_type, obj.name, obj.description)

            # Add everything to the body of the function
            body += "\n\t" + meta_add_str

            added_coll = True

        # This ensures that the ari_t *id variable is only declared if it is going to be used.
        # Avoids compiler warnings for unused variables
        if added_parm:
            body = parm_decl_str + body
        if added_coll:
            body = coll_decl_str + body

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, cs.META, body)

    #
    # Writes the init_constants() function to the open file descriptor passed as c_file
    # name is the value returned from get_adm_names()
    # constants is a list of constants to include
    #
    def write_init_constants(self, outfile):
        self._write_mgr_std_init_funct(outfile, cs.CONST, self.adm.const)

    #
    # Writes the init_edds function to the passed open file c_file
    # name and ns are the values returned by get_adm_names()
    # edds is a list of edds to include
    #
    def write_init_edd_function(self, outfile):
        self._write_mgr_std_init_funct(outfile, cs.EDD, self.adm.edd)


    #
    # Writes the init_operators() function to the open file descriptor passed as c_file
    # name is the value returned from get_adm_names()
    # operators is a list of the operators to include
    #
    def write_init_ops(self, outfile):
        body = ""
        coll_decl_str = "\n\tari_t *id = NULL;\n"
        parm_decl_str = "\n\tmetadata_t *meta = NULL;\n"

        add_op_ari_template = "\n\tadm_add_op_ari(id, {}, NULL);"
        build_str_template  = campch.make_adm_build_ari_template(cs.OP, self._g_var_idx, True)
        meta_add_template   = campch.make_std_meta_add_coll_template(cs.OP, self.adm.norm_namespace)

        added_coll = False
        added_parm = False

        for obj in self.adm.oper:
            # Preliminary; gather all of the pieces of data we need
            ari      = cu.make_ari_name(self.adm.norm_namespace, cs.OP, obj)
            amp_type = cu.make_amp_type_name_from_str(obj.result_type)
            in_types = obj.in_type if obj.in_type else []

            # Format the meta_add_.* template for this item
            meta_str = meta_add_template.format(amp_type, obj.name, obj.description)

            # A couple of variables depend on the presence or absence of parms
            parms_tf = "0"
            if in_types:
                parms_tf = "1"
                added_parm = True
                meta_str = "meta = " + meta_str

            # Add formatted strings to the body of the function
            body += build_str_template.format(parms_tf, ari)
            body += add_op_ari_template.format(len(in_types))
            body += "\n\t" + meta_str

            for in_type in in_types:
                parm_type = cu.make_amp_type_name_from_str(in_type.type)
                body += add_parm_template.format("O{}".format(in_type.position + 1), parm_type)

            added_coll = True

        # This ensures that the ari_t *id variable is only declared if it is going to be used.
            # Avoids compiler warnings for unused variables
        if added_parm:
            body = parm_decl_str + body
        if added_coll:
            body = coll_decl_str + body

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, cs.OP, body)

    #
    # Writes the init_variables() function to the open file descriptor passed as c_file
    # name is the value returned from get_adm_names()
    # variables is a list of variables to include
    #
    def write_init_variables_function(self, outfile):
        campch.write_init_var_function(outfile, self.adm, self._g_var_idx, True)

    #
    # Writes the init_controls() function to the open file descriptor passed as c_file
    # name is the value returned from get_adm_names()
    # controls is a list of controls to include
    #
    def write_init_controls_function(self, outfile):
        body = ""
        coll_decl_str = "\n\tari_t *id = NULL;\n"
        parm_decl_str = "\n\tmetadata_t *meta = NULL;\n"

        build_str_template   = campch.make_adm_build_ari_template(cs.CTRL, self._g_var_idx, True)
        add_ctrldef_template = "\n\tadm_add_ctrldef_ari(id, {}, NULL);"
        enum_name            = cu.make_enum_name_from_str(self.adm.norm_namespace)
        meta_add_template    = "meta_add_" + cs.get_sname(cs.CTRL).lower() + "(id, " + enum_name + ", \"{0}\", \"{1}\");\n"

        added_coll = False
        added_parm = False

        for obj in self.adm.ctrl:
            # Gather the pieces of data that we need
            ari   = cu.make_ari_name(self.adm.norm_namespace, cs.CTRL, obj)
            parms = obj.parmspec.items if obj.parmspec else []

            # Format the meta_add_.* template for this item
            meta_str = meta_add_template.format(obj.name, obj.description)

            # A couple of variables depend on the presence or absence of parms
            parms_tf = "0"
            if parms:
                parms_tf = "1"
                added_parm = True
                meta_str = "meta = " + meta_str

            # Add formatted strings to the body of the function
            body += "\n\n\t/* {} */".format(obj.name.upper())
            body += "\n" + build_str_template.format(parms_tf, ari)
            body += add_ctrldef_template.format(len(parms))
            body += "\n\t" + meta_str

            for parm in parms:
                parm_type = cu.make_amp_type_name_from_str(parm.type)
                body += add_parm_template.format(parm.name, parm_type)

            added_coll = True

        # This ensures that the ari_t *id variable is only declared if it is going to be used.
            # Avoids compiler warnings for unused variables
        if added_parm:
            body = parm_decl_str + body
        if added_coll:
            body = coll_decl_str + body

        campch.write_formatted_init_function(outfile, self.adm.norm_namespace, cs.CTRL, body)


    #
    # Writes the init_macros() function to the open file descriptor passed as c_file
    # name is the value returned from get_adm_names()
    # macros is a list of macros to include
    #
    def write_init_macros(self, outfile):
        campch.write_init_macro_function(outfile, self.adm, self._g_var_idx, True)


    #
    # Writes the init_reports() function to the open file descriptor passed as c_file
    # name is the value returned from get_adm_names()
    #
    def write_init_reports(self, outfile):
        campch.write_parameterized_init_reports_function(outfile, self.adm, self._g_var_idx, True)

    #
    # Writes the init_tables() function to the open file descriptor passed as c_file
    # name is the value returns from get_adm_names()
    #
    def write_init_tables(self, outfile):
        campch.write_init_tables_function(outfile, self.adm, self._g_var_idx, True)

    # Builds a template for the
    # ```
    # id = adm_build_ari(...)
    # adm_add_...
    # ```
    # calls with passed collection type and adm name. Should be formatted in the calling
    # function with:
    # return_str.format([0|1](for whether params are present or not), ari_name, ari_amp_type, item[name], item[description])
    #
    # The intention behind this function is to only have to construct these parts once for each
    # collection. Subset of formatted values that need to be substituted for_each_ item in the
    # collection is much smaller.
    #
    def _make_std_adm_build_add_template(self, coll) -> str:
        add_type = 'cnst' if coll == cs.META else cs.get_sname(coll).lower()
        add_str = campch.make_adm_build_ari_template(coll, self._g_var_idx, True)
        add_str = add_str + "\n\tadm_add_"  + add_type + "(id, NULL);"

        return add_str
