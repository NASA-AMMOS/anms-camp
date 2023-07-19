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
''' This module creates PGSQL or MySQL scripts to populate the manager
database.
'''

import logging
import re
import datetime
import os
import fileinput
from typing import TextIO

from camp.generators.lib import camputil as cu
from camp.generators.lib import campsettings as cs
from camp.generators.base import AbstractWriter
from ace import models


LOGGER = logging.getLogger(__name__)

#:FIXME temporary removal until SQL procedures are updated
#USE_UPDATE_RECORD = True


######################################################################
# Helper Functions for the main write_*_functions() method
# TODO: Move broadly-useful helper functions to camputils


# Escape single quotes in a string (to clean SQL input)
# TODO: Currently only used on descriptions; should update to escape all strings
# TODO: switch to using a library to sanitize input more fully
def escape_description_sql(val):
    if val is None:
        return None
    return val.replace("'","''")


class Writer(AbstractWriter):
    ''' The SQL file writer.

    :param dialect: Choice of the SQL dialect to generate.
    '''

    DIALECTS = {
        'mysql',
        'pgsql',
    }

    def __init__(self, admset, adm, out_path, dialect):
        super().__init__(admset, adm, out_path)
        if dialect not in Writer.DIALECTS:
            raise ValueError(f'Bad dialect: {dialect}')
        self.dialect = dialect
        self._var_prefix = "@" if self.dialect == 'mysql' else ''
        self._vars_def = set()
        self._vars_use = set()

        # The first half of the namespace
        ns = self.adm.norm_namespace
        hl_ns = ns.split('/')[0].lower()
        self._sql_ns = self._var_name(f"{hl_ns}_namespace_id")

    def file_path(self) -> str:
        # Interface for AbstractWriter
        return os.path.join(self.out_path, "amp-sql", "Agent_Scripts", f"adm_{self.adm.norm_name}.sql")

    def write(self, outfile: TextIO):
        # Interface for AbstractWriter
        head = []
        body = []
        head += self.write_setup()

        body += self.write_metadata_function()
        body += self.write_mdat_functions()
        body += self.write_edd_functions()
        body += self.write_oper_functions()
        body += self.write_var_functions()
        body += self.write_tblt_functions()
        body += self.write_rptt_functions()
        body += self.write_ctrl_functions()
        body += self.write_const_functions()
        body += self.write_mac_functions()

        head += self.body_pre()
        body += self.body_post()

        for line in head + body:
            outfile.write(line)
            outfile.write("\n")

    def _var_name(self, name, define=True):
        ''' Construct an SQL variable name for a given text name.

        :param name: The name of the variable.
        :param define: True if this use is defining the variable,
            False if it's using the variable, or
            None if it's an external variable name.
        :return: The SQL for the variable.
        '''
        name = name.casefold()

        if define is None:
            pass
        elif define:
            self._vars_def.add(name)
        else:
            self._vars_use.add(name)

        return self._var_prefix + name

    def _make_ari(self, coll, item):
        ''' Generate an augmented ARI for an ADM object usable with
        :method:`make_sql_ids`

        :param coll: collection of the item (EDD, VAR, etc.)
        :param item: object to make the IDs for.
        :return: the augmented ARI text.
        '''
        ns = self.adm.norm_namespace
        ari = cu.make_ari_name(ns, coll, item).lower()
        return ari

    def make_sql_ids(self, ari, define=True):
        ''' Generate a tuple of the (object id, definition id, actual_id) for
        a given object.
        IDs are similar to ARI strings in c/h code, but use only a substring of
        the ari, splitting it at the first instance of an underscore. This is
        in order to help keep variable names under 64 characters for SQL.

        :param ari: The augmented ARI text.
        :param define: If this use is defining the SQL variables.
        :return: The tuple of IDs.
        '''

        # Need to shorten because SQL variables have to be < 64 chard
#        first_underscore = ari.find("_")
#        if(first_underscore != -1):
#            ari = ari[first_underscore+1:]

        obj_id = self._var_name(ari, define)
        def_id = self._var_name(ari + "_did", define)
        act_id = self._var_name(ari + "_aid", define)

        for name in (obj_id, def_id, act_id):
            if len(name) > 64:
                LOGGER.error("[ ERROR ] Auto-generated SQL variable is longer than 64 characters ("+str(len(name))+"): "+ name)

        return obj_id, def_id, act_id

    # Helper function for SP__insert_obj_metadata template creation
    # retriever is the retriever object loaded with the ADM
    # obj_type is the type of the object (EDD, VAR, etc.)
    # Returns template, which should be formatted with name of the object and id of the object
    def create_insert_obj_metadata_template(self, obj_type):
        ''' format with 0=object type enum, 1={} (to be filled by caller), 2=highlevel namespace, 3={} (to be filled by caller)
        '''
        general_template = "CALL SP__insert_obj_metadata({}, '{}', {}, {});"

        # convert to object type enumeration to decimal for function
        obj_type_enum = str(int(cs.ari_type_enum(obj_type), 16))
        formatted = general_template.format(obj_type_enum, "{}", self._sql_ns, "{}")
        return formatted


    # Helper function for the parmspec entry template
    # description is description format for the entries (default is '{}')
    # Returns a tuple of the (insert_formal_parmspec function template, insert_formal_parmspec_entry function template)
    # Format the former with number of parmspec, fp_id, format the latter with fp_id, enum of the entry, entry name, entry type
    def create_insert_formal_parmspec_templates(self, desc_template="{}"):
        basic_template = "CALL SP__insert_formal_parmspec({}, '{}', {});"
        entry_template = "CALL SP__insert_formal_parmspec_entry({}, {}, '{}', '{}', null, " + self._var_name("r_fp_ent") + ");"

        return basic_template.format("{}", desc_template, "{}", {}), entry_template

    # Helper function for insert_tnvc_collection template and insert_tnvc_entry template
    # obj_type is the type of object in the collection (OP, etc.)
    # Returns tuple of (insert_tnvc_collection template, insert_tnvc_entry_template, insert_tnvc_unk_entry_template)
    # Format the first with description, the second with entry type, and argument fields, the third with argument fields
    def create_insert_tnvc_templates(self, obj_type, num_entries):
        obj_type_str = cs.get_sname(obj_type).lower()
        tnvc_var = self._var_name(f"{obj_type_str}_tnvc_id")

        collection_template = "CALL SP__insert_tnvc_collection('{}', " + tnvc_var + ");"

        # XXX: unsure how useful this is, because only one {} is formatted here, rest are left for user.
        entry_template = "CALL SP__insert_tnvc_{}_entry(" + tnvc_var + ", {}, {}, null, " + self._var_name("tnvc_entry", None) + "{});"

        # One fewer argument than all other insert_tnvc_.*_entry() functions
        unk_entry_template = "CALL SP__insert_tnvc_unk_entry(" + tnvc_var + ", {}, null, " + self._var_name("tnvc_entry", None) + "{});"

        # preallocate names
        for idx in range(num_entries):
            self._var_name(f"tnvc_entry{idx+1}")

        return collection_template, entry_template, unk_entry_template

    # Helper function for insert_ac functions
    # obj_type is the type of object (OP, MACRO, etc.)
    # description_format is any formatting you wish to impose on the description
    # Returns template for insert_ac_id function, format with number of acs and the description
    def create_insert_ac_id_template(self, obj_type, description_format="{}"):
        function_template = "CALL SP__insert_ac_id({0}, '{1}', {2});"
        obj_id_template = "{}_ac_id"

        obj_type_str = cs.get_lname(obj_type).lower()
        obj_id = self._var_name(obj_id_template.format(obj_type_str))
        return function_template.format("{}", description_format, obj_id)


    # Returns a tuple of the (definition id,object id) of the passed definition object
    # retriever: a Retriever object loaded with the ADM
    # d: the definition list entry from the ADM
    def make_definition_ids(self, item):
        lines = ""
        #FIXME: this needs to be made consistent with earlier behavior
        # if the object is rom a differnt namesapce need to create select smnt


        name = item.nm
        if name.casefold().startswith('mdat.'):
            name = 'meta' + name[4:]
        elif name.casefold().startswith('oper.'):
            name = 'op' + name[4:]
        name = name.replace('.', '_').split('(', 1)[0]

        ari_str = '_'.join([item.ns, name]).replace("/", "_")
        fx_obj_id, pfx_def_id, pfx_act_id = self.make_sql_ids(ari_str)
        
        if item.ns != self.adm.adm_ns:
            stmnt = f"{pfx_act_id} = (select obj_id FROM public.vw_ari_union WHERE obj_name = \'{name.split('_',1)[1]}\' and adm_name = (select adm_name from public.vw_namespace where name_string = \'{item.ns}\')  and actual = true);"
            lines = stmnt

        return fx_obj_id, pfx_def_id, pfx_act_id, lines

    # Returns the fp id, given the passed string representing the
    # id of the object.
    # obj_id: string representation of the definition id of an object
    def make_fp_id(self, obj_id):
        return obj_id + "_fp"

    ##################################################################################
    # Functions to format and write stored procedures to the SQL file based on the ADM

    def write_setup(self):
        ''' Genreate lines for the introductory material for the sql file
        '''
        lines = [
            "-- -------------------------------------------------------------------",
            "--",
            "-- File Name: adm_{}.sql".format(self.adm.norm_name),
            "--",
            "-- Description: TODO",
            "--",
            "-- Notes: TODO",
            "--",
            "-- Assumptions: TODO",
            "--",
            "-- Modification History:",
            "-- YYYY-MM-DD    AUTHOR          DESCRIPTION",
            "-- ----------    --------------  ------------------------------------",
            "-- {}    AUTO            Auto-generated SQL file".format(str(datetime.datetime.now().date())),
            "--",
            "-- -------------------------------------------------------------------",
            "",
            "-- ADM: '{}'".format(self.adm.norm_namespace),
            "",
        ]

        return lines

    def body_pre(self):
        ''' Genreate lines before the SQL body.
        '''
        undef = self._vars_use - self._vars_def
        
        if undef:
            raise RuntimeError(f"There are {len(undef)} undefined variables in this ADM SQL: {undef}")

        lines = []
        if self.dialect == 'mysql':
            lines +=  [
                "",
                "use amp_core;",
                "",
                "SET @adm_enum = {};".format(self.adm.enum)
            ]
        elif self.dialect == 'pgsql':
            lines += [
                "DO",
                "$do$",
                "DECLARE adm_enum INTEGER := {};".format(self.adm.enum),
            ]
            for name in sorted(self._vars_def):
                lines.append(f"DECLARE {name} INTEGER;")
            lines += [
                "BEGIN",
                "",
            ]

        return lines

    def body_post(self):
        ''' Generate liens after the SQL body.
        '''
        lines = []
        if self.dialect == 'pgsql':
            lines += [
                "",
                "END",
                "$do$",
            ]

        return lines

    def write_metadata_function(self):
        ''' Genreate lines for the ADM metadata
        '''
        # format with org, namespace, version, name, description from namespace, ns from get_highlevel_ns
        meta_template = "CALL SP__insert_adm_defined_namespace('{}', '{}', '{}', '{}', {}, NULL, '{}', {});"

        def val_or_none(obj, attr='value'):
            if obj is None:
                return ''
            return getattr(obj, attr)

        name = val_or_none(self.admset.get_child(self.adm, models.Mdat, 'name'))
        ns = val_or_none(self.admset.get_child(self.adm, models.Mdat, 'namespace'))
        version = val_or_none(self.admset.get_child(self.adm, models.Mdat, 'version'))
        org = val_or_none(self.admset.get_child(self.adm, models.Mdat, 'organization'))
        desc = escape_description_sql(val_or_none(self.admset.get_child(self.adm, models.Mdat, 'namespace'), 'description'))

        adm_enum = self._var_name("adm_enum", None)

        formatted_template = meta_template.format(org, ns, version, name, adm_enum, desc, self._sql_ns)
        return [
            "",
            formatted_template
        ]

    def write_edd_functions(self):
        ''' Genreate lines for all of the EDDs in the ADM
        '''
        lines = [
            "",
            "",
            "-- EDD",
            "",
        ]

        insert_obj_template = self.create_insert_obj_metadata_template(cs.EDD)
        insert_formal_parmspec_template, insert_entry_template = self.create_insert_formal_parmspec_templates("parms for {}")

        # Format with edd obj id, edd description, edd type, edd def id
        edd_formal_def_template = "CALL SP__insert_edd_formal_definition({}, '{}', {}, '{}', {});"
        # Format with edd obj id and edd name (only used if no parmspec)
        edd_actual_def_template = "CALL SP__insert_edd_actual_definition({}, 'The singleton value for {}', NULL, {});"

        for edd in self.adm.edd:
            edd_obj_id, edd_def_id, edd_act_id = self.make_sql_ids(self._make_ari(cs.EDD, edd))
            edd_fp_id = self.make_fp_id(edd_obj_id)

            name = edd.name
            etype = edd.type
            desc = escape_description_sql(edd.description)
            parmspec = edd.parmspec.items if edd.parmspec else []
            num_parmspec = len(parmspec)
            lines += [
                "",
                insert_obj_template.format(name, edd_obj_id),
            ]

            if parmspec:
                self._var_name(edd_fp_id)
                lines += [insert_formal_parmspec_template.format(num_parmspec, name, edd_fp_id, edd_obj_id)]

                for parm in parmspec:
                    lines += [insert_entry_template.format(edd_fp_id, parm.position + 1, parm.name, parm.type)]

            # Only put actual definition here if no parmspec
            if not parmspec:
                self._var_name(edd_act_id)
                lines += [
                    edd_formal_def_template.format(edd_obj_id, desc, "NULL", etype, edd_def_id),
                    edd_actual_def_template.format(edd_obj_id, name, edd_act_id),
                ]
            else:
                lines += [edd_formal_def_template.format(edd_obj_id, desc, edd_fp_id, etype, edd_def_id)]

        return lines

    def write_oper_functions(self):
        ''' Genreate lines for all of the OPERs in the ADM
        '''
        lines = [
            "",
            "",
            "-- OPER",
        ]

        oper_template = self.create_insert_obj_metadata_template(cs.OP)

        # format with formatted obj_id, description, result-type, number of parameters, formatted opr_def_id_template
        actual_def_template = "CALL SP__insert_operator_actual_definition({}, '{}', '{}', {}, " + self._var_name("op_tnvc_id") + ", {});"

        for oper in self.adm.oper:
            oper_name = oper.name
            oper_desc = escape_description_sql(oper.description)
            result_type = oper.result_type

            oper_obj_id, oper_def_id, oper_act_id = self.make_sql_ids(self._make_ari(cs.OP, oper))
            tnvc_collection_template,tnvc_entry_template,tnvc_unk_entry_template = self.create_insert_tnvc_templates(cs.OP, len(oper.in_type))

            lines += [
                "",
                oper_template.format(oper_name, oper_obj_id),
                tnvc_collection_template.format("operands for "+ oper_name),
            ]

            for in_type in oper.in_type:
                t = in_type.type.lower()

                # UNK has one fewer parameter
                if t == "unk":
                    lines += [tnvc_unk_entry_template.format(in_type.position + 1, in_type.position + 1)]
                else:
                    lines += [tnvc_entry_template.format(t, in_type.position + 1, "null", in_type.position + 1)]

            # TODO: UNK is not a valid type, comment the actual_def for this out for now until ADM resolved
            if result_type.upper() == 'UNK':
                lines += ["-- " + actual_def_template.format(oper_obj_id, oper_desc, result_type, len(oper.in_type), oper_act_id)]
            else:
                lines += [actual_def_template.format(oper_obj_id, oper_desc, result_type, len(oper.in_type), oper_act_id)]

        return lines

    def write_var_functions(self):
        ''' Genreate lines for all of the VARs in the ADM
        '''
        lines = [
            "",
            "",
            "-- VAR",
        ]

        ac_comment = "-- create ac for expression"

        var_template = self.create_insert_obj_metadata_template(cs.VAR)
        insert_ac_id_template = self.create_insert_ac_id_template(cs.VAR)

        # format with entry id, enumeration of entry in this var
        insert_actual_entry_template = "CALL SP__insert_ac_actual_entry(" + self._var_name("var_ac_id") + ", {0}, {1}, " + self._var_name("r_ac_entry_id_", None) + "{1} );"

        # format with var id, description, var def id
        # TODO: should be encoding the out type of the variable instead of passing hardcoded '20' for all
        var_def_template = "CALL SP__insert_variable_definition({}, '{}', 20, " + self._var_name("var_ac_id") + ", {});"
        for var in self.adm.var:
            var_name = var.name
            var_desc = escape_description_sql(var.description)
            postfix = var.initializer.postfix.items

            var_id, var_def_id, var_act_id = self.make_sql_ids(self._make_ari(cs.VAR, var))
            ac_description = f"ac for the expression used by {var_id}"
            lines += [
                "",
                ac_comment,
                var_template.format(var_name, var_id),
                insert_ac_id_template.format(len(postfix), ac_description, var_id),
            ]

            for item in postfix:
                pfx_obj_id, pfx_def_id, pfx_act_id, line = self.make_definition_ids(item)
                lines += [line]
                lines += [insert_actual_entry_template.format(pfx_act_id, item.position + 1)]
                # preallocate names
                self._var_name(f"r_ac_entry_id_{item.position + 1}")

            lines += [
                var_def_template.format(var_id, var_desc, var_act_id),
            ]
        
        return lines

    def write_tblt_functions(self):
        ''' Genreate lines for all of the TBLTs in the ADM
        '''
        lines = [
            "",
            "",
            "-- TBLT",
        ]

        insert_obj_template = self.create_insert_obj_metadata_template(cs.TBLT)

        # Format with table object id (above), table description, tblt definition id
        insert_def_template = "CALL SP__insert_table_template_actual_definition({}, '{}', " + self._var_name("tbl_tnvc_id") + ", {});"

        for tblt in self.adm.tblt:
            tblt_name = tblt.name
            tblt_desc = escape_description_sql(tblt.description)

            tblt_id, tblt_def_id, tblt_act_id = self.make_sql_ids(self._make_ari(cs.TBLT, tblt))
            add_tnvc_coll_template,insert_column_template,_ = self.create_insert_tnvc_templates(cs.TBL, len(tblt.columns.items))

            lines += [
                "",
                insert_obj_template.format(tblt_name, tblt_id),
                add_tnvc_coll_template.format('columns for the '+tblt_name+' table'),
            ]

            for col in tblt.columns.items:
                lines += [insert_column_template.format(col.type.lower(), col.position + 1, "'" + col.name + "'", col.position + 1)]

            lines += [insert_def_template.format(tblt_id, tblt_desc, tblt_def_id)]

        return lines

    def handle_report_fp_ap(self, item, lines, report_id):
        ''' Helper function to handle creation of stored procedures for the
        fps and aps within the reports templates in the ADM

        :param item: definition object to produce the stored procedures for.
        :param lines: The lines array to add to
        :return: a string that is a concatenation of all of the stored
            procedures necessary for the definition's aps and fps, to be
            written to the SQL file by the caller.
        '''
        meta_id_template = "p_lit_meta_{0}_id"
        actual_id_template = "r_lit_{0}_id"

        # Format with def_id, enumeration, description
        insert_actual_parmspec_template = "CALL SP__insert_actual_parmspec({}, {}, '{}', " + self._var_name("ap_spec_id") + ");"
        # format with value, meta_id
        insert_obj_metadata_template = self.create_insert_obj_metadata_template(cs.LIT).format("Literal value {}", '{}')

        # Format with meta_id, value, type, actual id
        insert_actual_def_template = "CALL SP__insert_literal_actual_definition({}, '{}', '{}', '{}', {});".format("{0}", "literal value {1}", '{2}', '{1}','{3}')
        # Format with enumeration, type, actual_id
        insert_actual_parms_obj_template = "CALL SP__insert_actual_parms_object(" + self._var_name("ap_spec_id") + ", {}, '{}', {});"

        # Format with coll, obj_id, enum
        # TODO: This likely only works for edd.. do we need it for other object types?
        insert_coll_actual_def_template = "CALL SP__insert_{0}_actual_definition({1}, NULL, " + self._var_name("ap_spec_id") + ", {2});"

        # Formal with enumeration, type, fp_spec_id
        insert_actual_name_template = "CALL SP__insert_actual_parms_names(" + self._var_name("ap_spec_id") + ", {}, '{}', {});"

        def_id,obj_id,act_id,_ = self.make_definition_ids(item)
        fp_id = self.make_fp_id(def_id)
        def_ns,def_coll,def_name = cu.ari_get_names(item)

        import ace.ari
        from ace.util import get_ident, find_ident
        def_ident = get_ident(item)
        fp = def_ident.strip_name()
        found_ref = find_ident(self.admset.db_session(), def_ident)
        if not found_ref:
            raise RuntimeError('No reference found for object ' + str(def_ident))

        # Parameter types of referenced object, if there are any
        types = (
            [parm.type for parm in found_ref.parmspec.items]
            if hasattr(found_ref, 'parmspec') and found_ref.parmspec
            else []
        )

        fp_spec_id = self._var_name("fp_spec_id")
        result = act_id

        ####### Handle aps
        aplist = item.ap
        if aplist:
            formal_parmspec_template, fp_entry_template = self.create_insert_formal_parmspec_templates("parms for {}")
            num_ap = len(aplist)
            lines += [formal_parmspec_template.format(num_ap, def_name, fp_spec_id, report_id)]

            for ap_obj in aplist:
                enum = ap_obj.position + 1
                a_type = types[ap_obj.position]

                aid = f"{act_id}_{ap_obj.value.lower()}_{enum}"
                self._var_name(aid)
                lines += [
                    fp_entry_template.format(fp_spec_id, enum, def_name, a_type),
                    "",
                    insert_actual_parmspec_template.format(fp_id, enum, ''),
                    insert_actual_name_template.format(enum, a_type, 'r_fp_ent'),
                    insert_coll_actual_def_template.format(cs.get_sname(def_coll).lower(), def_id, aid),
                ]
                result = aid

        ####### Handle fps
        if fp:
            # For each fp
            for i, p in enumerate(fp):
                lit_meta_id = self._var_name(meta_id_template.format(p))
                lit_actual_id = self._var_name(actual_id_template.format(p))
                enum = i+1
                p_type = types[i]
                aid = f"{act_id}_{enum}_{p}"
                self._var_name(aid)

                lines += [
                    "",
                    insert_actual_parmspec_template.format(fp_id, enum, "actual parms for "+def_name+" passed "+p),

                    insert_obj_metadata_template.format(p, lit_meta_id),
                    insert_actual_def_template.format(lit_meta_id, p, p_type, lit_actual_id),
                    insert_actual_parms_obj_template.format(enum, p_type, lit_actual_id),
                    insert_coll_actual_def_template.format(cs.get_sname(def_coll).lower(), def_id, aid),
                ]
            result = aid

        return result

    def write_rptt_functions(self):
        ''' Genreate lines for all of the RPTTs in the ADM
        '''
        lines = [
            "",
            "",
            "-- RPTT",
        ]

        insert_report_template = self.create_insert_ac_id_template(cs.RPTT, "ac for report template {}")
        insert_obj_template = self.create_insert_obj_metadata_template(cs.RPTT)

        # Format with entry id name and enum of entry
        insert_entry_template = "CALL SP__insert_ac_actual_entry(" + self._var_name("rptt_ac_id") + ", {0}, {1}, " + self._var_name("r_ac_rpt_entry_", None) + "{1});"

        # Format with report id, report description, report_def_id
        insert_formal_def_template = "CALL SP__insert_report_template_formal_definition({}, '{}', {}, " + self._var_name("rptt_ac_id") + ", {});"
        # Format with report id, report name
        insert_actual_def_template = "CALL SP__insert_report_actual_definition({0}, null, null, 'Singleton value for {1}', {2});"
        for rptt in self.adm.rptt:
            report_name = rptt.name
            report_desc = escape_description_sql(rptt.description)
            definitions = rptt.definition.items if rptt.definition else []
            parmspec = rptt.parmspec.items if rptt.parmspec else []

            report_id, report_def_id, report_act_id = self.make_sql_ids(self._make_ari(cs.RPTT, rptt))

            lines +=  [
                "",
                insert_obj_template.format(report_name, report_id),
            ]

            # For each definition in the rptt template
            defn_lines = [
                insert_report_template.format(len(definitions), report_name, report_id),
            ]
            for item in definitions:
                item_id = self.handle_report_fp_ap(item, lines, report_id)

                # preallocate names
                self._var_name(item_id, False)
                self._var_name(f"r_ac_rpt_entry_{item.position + 1}")
                # Keeping this in a separate list because it has to happen
                # after all of the calls to handle_report_fp_ap()
                defn_lines += [insert_entry_template.format(item_id, item.position + 1)]

            lines += defn_lines

            # check if has formal parameter
            if parmspec:
                fp_spec_id = self._var_name("fp_spec_id")
            else:
                fp_spec_id = "null"

            self._var_name(report_def_id)
            lines += [
                "",
                insert_formal_def_template.format(report_id, report_desc, fp_spec_id, report_def_id),
                ]
            if not parmspec:
                lines += [
                    "",
                    insert_actual_def_template.format(report_id, report_name, report_act_id),
                ]

        return lines

    def write_ctrl_functions(self):
        ''' Genreate lines for all of the CTRLs in the ADM
        '''
        lines = [
            "",
            "",
            "-- CTRL",
        ]

        insert_obj_template = self.create_insert_obj_metadata_template(cs.CTRL)
        insert_formal_parmspec_template,insert_entry_template = self.create_insert_formal_parmspec_templates("parms for the {} control")

        # Format with ctrl id, ctrl description, fp_spec_id or null, ctrl definition id
        insert_ctrl_formal_def_template = "CALL SP__insert_control_formal_definition({} , '{}', {}, {});"
        for ctrl in self.adm.ctrl:
            ctrl_name = ctrl.name
            ctrl_desc = escape_description_sql(ctrl.description)
            parmspec = ctrl.parmspec.items if ctrl.parmspec else []

            ctrl_id, ctrl_def_id, ctrl_act_id = self.make_sql_ids(self._make_ari(cs.CTRL, ctrl))
            lines += [
                "",
                insert_obj_template.format(ctrl_name, ctrl_id),
            ]

            if parmspec:
                fp_spec_id = self._var_name("fp_spec_id")
                lines += [insert_formal_parmspec_template.format(len(parmspec), ctrl_name, fp_spec_id, ctrl_id)]
                for parm in parmspec:
                    lines += [insert_entry_template.format(fp_spec_id, parm.position + 1, parm.name, parm.type)]
            else:
                fp_spec_id = "null"

            lines += [insert_ctrl_formal_def_template.format(ctrl_id, ctrl_desc, fp_spec_id, ctrl_def_id)]

        return lines

    def write_gen_const_functions(self, objects, coll):
        ''' Helper function for the META and CONST objects to allow
        code reuse since they use the same stored procedures.

            Genreate lines for all of the passed objects.

        :param objects: list of objects (CONSTs or METAs) to write the stored procedures for
        :param coll: type of collection (cs.CONST or cs.META)
        '''
        insert_obj_template = self.create_insert_obj_metadata_template(coll)

        # Format with const id, definition, type, value, and const def id
        insert_const_actual_def_template = "CALL SP__insert_const_actual_definition({}, '{}', '{}', '{}', {});"

        lines = []
        for obj in objects:
            c_name = obj.name
            c_desc = escape_description_sql(obj.description)

            const_id, const_def_id, const_act_id = self.make_sql_ids(self._make_ari(coll, obj))

            lines += [
                "",
                insert_obj_template.format(c_name, const_id),
                insert_const_actual_def_template.format(const_id, c_desc, obj.type, obj.value, const_act_id),
            ]

        return lines

    def write_const_functions(self):
        ''' Genreate lines for all of the CONSTs in the ADM
        '''
        lines = [
            "",
            "",
            "-- CONST",
        ]
        return lines + self.write_gen_const_functions(self.adm.const, cs.CONST)

    def write_mdat_functions(self):
        ''' Genreate lines for all of the MDATs in the ADM
        '''
        lines = [
            "",
            "",
            "-- MDAT",
        ]
        return lines + self.write_gen_const_functions(self.adm.mdat, cs.META)


    def write_mac_functions(self):
        ''' Genreate lines for all of the MACs in the ADM
        '''
        lines = [
            "",
            "",
            "-- MAC",
        ]

        insert_obj_template = self.create_insert_obj_metadata_template(cs.MACRO)
        insert_formal_parmspec_template, insert_ac_formal_parmspec_entry_template = self.create_insert_formal_parmspec_templates("parms for the {} macro")
        insert_ac_id_template = self.create_insert_ac_id_template(cs.MACRO, "ac for {} macro")

        # Format with def id, def enumeration in this macro
        insert_ac_formal_entry_template = "CALL SP__insert_ac_formal_entry(" + self._var_name("mac_ac_id") + ", {}, {}, " + self._var_name("r_ac_entry_id") + ");"

        # Format with mac id, description, fp_spec_id, number of parmspec (?), and mac def id
        insert_mac_formal_def_template = "\nCALL SP__insert_macro_formal_definition({}, '{}', {}, {}, " + self._var_name("mac_ac_id") + ", {});"

        for mac in self.adm.mac:
            mac_name = mac.name
            mac_desc = escape_description_sql(mac.description)
            parmspec = mac.parmspec.items if mac.parmspec else []
            num_parmspec = len(parmspec)
            definition = mac.action.items if mac.action else []

            mac_id, mac_def_id, mac_act_id = self.make_sql_ids(self._make_ari(cs.MACRO, m))
            lines += [
                "",
                insert_obj_template.format(mac_name, mac_id),
            ]

            if parmspec:
                fp_spec_id = self._var_name("fp_spec_id")
                lines += [insert_formal_parmspec_template.format(len(parmspec), mac_name, fp_spec_id)]
                for parm in parmspec:
                    lines += [insert_ac_formal_parmspec_entry_template.format(fp_spec_id, parm.position + 1, parm.name, parm.type)]

                lines += [insert_ac_id_template.format(num_parmspec, mac_name)]

            for item in definition:
                def_id,_,_,_ = self.make_definition_ids(item)
                lines += [insert_ac_formal_entry_template.format(def_id, item.position + 1)]

            #lines += [insert_mac_formal_def_template.format(mac_id, mac_desc, fp_spec_id, num_parmspec, mac_def_id)]
            # according to the comment in all_routines.sql,
            # num_parmspec at this line is p_max_call_depth int(10) unsigned - max call depth of the macro
            # however, we don't know how to specify that
            max_call_depth = 0
            lines += [insert_mac_formal_def_template.format(mac_id, mac_desc, fp_spec_id, max_call_depth, mac_def_id)]

        return lines

    # If the setup.mysql file exists in the output dir, and this
    # file is not already sourced in the setup script, add it to
    # the file.
    # setup_path: full expected path to the setup script
    # rel_path: relative path of the new sql file to add (path from setup script)
    def add_to_setup_mysql(setup_path, rel_path_sql):
        line_to_add = "source " + rel_path_sql +"\n"

        # method will use this keyword to figure out where to append the line_to_add
        end_agent_comment = "End Insert Agent Scripts"

        # If the file doesn't exist, do nothing
        if (not os.path.exists(setup_path)):
            return

        LOGGER.info("\tAttempting to add SQL file to " + setup_path + " ...",)
        try:
            # If it doesn't find the line_to_add before the end_agent_comment, add the line
            # right before the end_agent_comment
            already_present = False
            for line in fileinput.input(files=setup_path, inplace=True):
                if line_to_add in line:
                    already_present = True
                if end_agent_comment in line and not already_present:
                    print(line_to_add,)
                print(line,)

            if already_present:
                LOGGER.info("\n\t\t"+rel_path_sql + " already present in setup.mysql, skipping.")
            LOGGER.info("[ DONE ]")

        except Exception as e:
            LOGGER.error(e)
            return

    # If the dockerfile exists in the output dir, and this file is not
    # already listed in the dockerfile, add it to the file.
    # dockerfile_path: full expected path to the dockerfile
    # rel_path_sql: relative path of the new sql file to add (path from the dockerfile)
    def add_to_dockerfile(dockerfile_path, rel_path_sql):
        sqlfile_name = os.path.basename(rel_path_sql)
        line_to_add = "      - ${PWD}/"+rel_path_sql+":/docker-entrypoint-initdb.d/30-"+sqlfile_name+"\n"

        # method will use this keyword to figure out where to append the line_to_add
        end_agent_comment = "End Insert Agent Scripts"

        # If the file doesn't exist, do nothing
        if (not os.path.exists(dockerfile_path)):
            return

        LOGGER.info("\tAttempting to add SQL file to " + dockerfile_path + " ...",)
        try:
            # If it doesn't find the line_to_add before the end_agent_comment, add the line
            # right before  the end_agent_comment
            already_present = False
            for line in fileinput.input(files=dockerfile_path, inplace=True):
                if line_to_add in line:
                    already_present = True
                if end_agent_comment in line and not already_present:
                    print(line_to_add, )
                print(line,)

            if already_present:
                LOGGER.info("\n\t\t"+rel_path_sql+" already present in dockerfile, skipping.")
            LOGGER.info("[ DONE ]")

        except Exception as e:
            LOGGER.error(e)
            return
