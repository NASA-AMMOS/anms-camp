
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

import os
import re
import datetime
import ace.models
from . import campsettings as cs
from . import camputil as cu


##################### FUNCTIONS FOR COMMENTS AND HEADERS #####################

#
# Writes the standard c file header to the file
#
# fd: open file descriptor to write to
# filepath: the path to the of the file, where the basename will be included
# as part of the header
#
def write_c_file_header(fd, filepath):
    _write_file_header(fd, filepath, "c")

#
# Writes the standard .h file header to the file
#
# fd: open file descriptor to write to
# filepath: the path to the of the file, where the basename will be included
# as part of the header
#
def write_h_file_header(fd, filepath):
    _write_file_header(fd, filepath, "header")

#
# Writes the standard file header to the file
#
# fd: open file descriptor to write to
# filepath: the path to the of the file, where the basename will be included
# as part of the header
# modifier: string indicating type of file this is ('c' or 'header' are common values)
#
def _write_file_header(fd, filepath, modifier):
    standard_header = """\
/****************************************************************************
 **
 ** File Name: {0}
 **
 ** Description: TODO
 **
 ** Notes: TODO
 **
 ** Assumptions: TODO
 **
 ** Modification History:
 **  YYYY-MM-DD  AUTHOR           DESCRIPTION
 **  ----------  --------------   --------------------------------------------
 **  {1}  AUTO             Auto-generated {2} file
 **
 ****************************************************************************/

"""
    fd.write(standard_header.format(os.path.basename(filepath), str(datetime.datetime.now().date()), modifier))



#################### FUNCTIONS FOR #INCLUDES ###########################

#
# Given a list of files, creates the string neccessary to #include all of
# them in a .[ch] file
# Returns the completed string.
#
def make_includes(files):
    out = ""
    for f in files:
        out += "\n#include \"{}\"".format(f)
    out += "\n\n"

    return out

#
# Returns a list of the .h files that need to be included for the 'uses'
# construct in the JSON to work.
# name expected for #include declarations.
# Returns a list of correctly-formatted files, to be passed to make_includes()
#
def get_uses_h_files(retriever):
    uses = retriever.get_uses()
    formatted_uses = [f.lower().replace("/", "_") for f in uses]
    files = ["adm_{}.h".format(f) for f in formatted_uses]
    return files



############################ C-BASED UNTAINTING FUNCTIONS ##################################

#
# Takes the passed string, and adds c comment characters to make it
# print(well as a multi-line comment in a c file)
#
def multiline_comment_format(tainted):
    comment_width = 100

    # replace any comment-ending characters with empty string
    tainted = re.sub(r'\*/', '', tainted)

    # replace newline with newline + comment character
    tainted = re.sub('\\n', '\\n *', tainted)

    # split the lines every x characters to wrap
    tainted_list = tainted.splitlines()
    untainted = []
    for line in tainted_list:
        while len(line) > comment_width:
            left, right = line[:comment_width], line[comment_width:]
            untainted.append("\n * " + left)
            line = right
        untainted.append("\n * " + line)

    # Add opening and closing comment characters
    untainted = ("/*" + "".join(untainted) + "\n */")
    return untainted

#
# Helper function to make and return a string for wide comment headers
#
# name is the string to be put in the comment header
# if c_open is True, adds opening comment indicator (/*) to beginning of returned string
# if c_close is True, adds closing comment indicator (*/) to end of returned string
# When c_open == c_close == True, returns:
# ```
# /*
#  * +-----------+
#  * |    name   +
#  * +-----------+
#  */
# ```
# spaced to 112 characters-wide
#
def make_formatted_comment_header(name, c_open, c_close):
    width_sans_ends = 93

    # This is the `* +---[...]---+` string that can be found at the beginning and end
    envelope_str = "\n * +" + ('-' * width_sans_ends) + "+\n"

    name_len = len(name)
    # This is the `* |   name    +` string to be surrounded by envelope str
    white_space  = (" " * int((width_sans_ends - len(name) ) / 2))

    content_str  = " * |" + white_space + name + white_space
    if(name_len % 2 == 0) :
        content_str +=" "
    content_str += "+"


    out = envelope_str + content_str + envelope_str

    if c_open :
        out = "\n/*" + out
    if c_close:
        out += " */\n"
    return out



############################# FUNCTIONS SHARED BY IMPL_C and IMPL_H ###############################

#
# Makes and returns the basename, fullname, and signature tuple for the edd
# collect functions; where basename = edd_<edd-name> and fullname = <name>_<basename>
#
def make_collect_function(adm, edd):
    basename = "get_{}".format(edd.name.lower())
    fullname = "{0}_{1}".format(adm.norm_namespace.lower(), basename)
    signature = "tnv_t *{}(tnvc_t *parms)".format(fullname)
    return basename, fullname, signature

#
# Makes and returns the basename, fullname, and signature tuple for the metadata
# collect functions; where basename = <keyword>_<meta-name> and fullname = <name>_<basename>
#
def make_meta_function(adm, meta):
    keyword = cs.get_sname(cs.META)
    basename = "{0}_{1}".format(keyword, meta.name.lower())
    fullname = "{0}_{1}".format(adm.norm_namespace.lower(), basename)
    signature = "tnv_t *{}(tnvc_t *parms)".format(fullname)
    return basename, fullname, signature

#
# Makes and returns the basename, fullname, and signature tuple for the constant
# function; where basename = <keyword>_<const-name> and fullname = <name>_<basename>
#
def make_constant_function(adm, const):
    keyword = "get"
    basename = "{0}_{1}".format(keyword, const.name.lower())
    fullname = "{0}_{1}".format(adm.norm_namespace.lower(), basename)
    signature = "tnv_t *{}(tnvc_t *parms)".format(fullname)
    return basename, fullname, signature

#
# Makes and returns the basename, fullname, and signature tuple for the control
# functions; where basename = <keyword>_<control-name> and fullname = <name>_<basename>
#
def make_control_function(adm, control):
    keyword = cs.get_sname(cs.CTRL)
    basename = "{0}_{1}".format(keyword, control.name.lower())
    fullname = "{0}_{1}".format(adm.norm_namespace.lower(), basename)
    signature = "tnv_t *{}(eid_t *def_mgr, tnvc_t *parms, int8_t *status)".format(fullname)
    return basename, fullname, signature

#
# Makes and returns the basename, fullname, and signature tuple for the operator
# functions; where basename = <keyword>_<op-name> and fullname = <name>_<basename>
#
def make_operator_function(adm, op):
    keyword = cs.get_sname(cs.OP)
    basename = "{0}_{1}".format(keyword, op.name.lower())
    fullname = "{0}_{1}".format(adm.norm_namespace.lower(), basename)
    signature = "tnv_t *{}(vector_t *stack)".format(fullname)
    return basename, fullname, signature

#
# Makes and returns the basename, fullname, and signature tuple for the table
# functions; where basename = tbl_<tbl-name> and fullname = <name>_<basename>
#
def make_table_function(adm, tbl):
    keyword = cs.get_sname(cs.TBLT)
    basename = "{0}_{1}".format(keyword, tbl.name.lower())
    fullname = "{0}_{1}".format(adm.norm_namespace.lower(), basename)
    signature = "tbl_t *{}(ari_t *id)".format(fullname)
    return basename, fullname, signature



##################### FUNCTIONS SHARED BY CREATE_MGR.PY AND CREATE_AGENT.PY ###################

#
# Makes the adm_build_ari(..) template for the passed collection type and
# g_*_idx
# Caller should format the template with returned_str.format([0|1](whether params are present), ari_name)
#
# standalone is a boolean whether or not the call needs to stand alone. If False, the call should be used
# as an argument to another function.
#
def make_adm_build_ari_template(coll, g_var_idx, standalone):
    amp_type = cs.get_amp_type(coll)
    idx_type = cs.get_adm_idx(coll)

    template = "adm_build_ari("+amp_type+", {0}, " + g_var_idx + "["+idx_type+"], {1})"
    if standalone:
        template = "\n\tid = " + template + ";"
    return template

#
# Writes an init function to the passed c_file.
# name is the name returned by a call to initialize_names,
# coll is the collection to make the init function for. Can be None
# body is the body of the function.
#
def write_formatted_init_function(c_file, name, coll, body):
    ttype = None
    if coll is not None:
        ttype = "_" + cs.get_sname(coll).replace("-","_")
    else:
        ttype = ""

    init_funct_string = (
        "void {0}_init{1}()"
        "\n{{"
        "\n{2}"
        "\n}}"
        "\n\n")

    c_file.write(init_funct_string.format(name, ttype, body))

#
# Builds the new parm format
# d is a definition of a macro or rptt
#
def _make_adm_build_ari_parm(adm, item, params):
    item_ns,item_coll,item_name = cu.ari_get_names(item)
    item_ari = cu.make_ari_name_from_str(item_ns, item_coll, item_name)
    item_g_var_idx = cu.get_g_var_idx(item_ns)

    # These two variables only used if aps or fps present
    # notice not replacing {0} yet; it's formatted later with len of aps or fps
    ari_parm_template = "ADM_BUILD_ARI_PARM_{0}({1}, {2}[{3}], {4}"
    ari_parm_str = ari_parm_template.format("{0}", cs.get_amp_type(item_coll), item_g_var_idx,
                        cs.get_adm_idx(item_coll), item_ari)

    #FIXME: propagate parameters
    aps = []
    fps = []
    types = []

    if aps:
        ari_parm_str = ari_parm_str.format(len(aps))

        for idx, a in enumerate(aps):
            amp_type = cu.make_amp_type_name_from_str(types[idx])
            pidx     = retriever.get_index_ap(a, params)
            ari_parm_str += ", tnv_from_map({0}, {1})".format(amp_type, pidx)

        return ari_parm_str + ")"

    # formal params
    elif fps:
        ari_parm_str = ari_parm_str.format(len(fps))

        for idx, f in enumerate(fps):
            ftype = types[idx].lower()
            ari_parm_str += ", tnv_from_{0}({1})".format(ftype, f)

        return ari_parm_str + ")"

    # no params
    else:
        return make_adm_build_ari_template(item_coll, item_g_var_idx, False).format("0", item_ari)

#
# constructs and writes the init_macros function
#
# c_file is an open file descriptor to write to,
# name is the name of the adm from the caller; g_var_idx is the
# g_var_idx value in the calling function.
#
def write_init_macro_function(c_file, adm, g_var_idx, mgr):
    body = ""
    meta_decl_str   = "\n\tmetadata_t *meta = NULL;\n"
    macdef_decl_str = "\n\tmacdef_t *def = NULL;\n"
    added_meta   = False
    added_macdef = False

    macdef_create_template = "macdef_create({0}, {1});"
    add_macdef_ctrl_str    = "\n\tadm_add_macdef_ctrl(def, {});"
    adm_add_macdef_str     = "\n\tadm_add_macdef(def);"
    meta_add_parm_template = "\n\tmeta_add_parm(meta, \"{0}\", {1});"

    enum_name = cu.make_enum_name_from_str(adm.norm_namespace)
    meta_add_macro_template = "\n\tmeta = meta_add_macro" + "(def->ari, " + enum_name + ", \"{0}\", \"{1}\");"
    build_ari_str_template  = make_adm_build_ari_template(cs.MACRO, g_var_idx, False)

    for obj in adm.mac:
        # Preliminaries
        ari = cu.make_ari_name(adm.norm_namespace, cs.MACRO, obj)
        mac_name    = obj.name
        description = obj.description or ''

        acts  = obj.action.items if obj.action else []
        parms = obj.parmspec.items if obj.parmspec else []

        defs_str = ""
        parms_tf = "0"
        if parms:
            parms_tf = "1"

        # Use templates to make calls specific to this macro
        build_ari_str     = build_ari_str_template.format(parms_tf, ari)
        macdef_create_str = macdef_create_template.format(len(defs), build_ari_str)
        if defs:
            macdef_create_str = "\n\tdef = " + macdef_create_str
            added_macdef = True
        else:
            macdef_create_str = "\n\t" + macdef_create_str


        # Create necessary strings for each definition
        for item in acts:
            def_build_ari_parm_str = _make_adm_build_ari_parm(adm, item, parms);
            defs_str += add_macdef_ctrl_str.format(def_build_ari_parm_str)

        # Add all the formatted strings to the body
        body += "\n\n\t/* {} */".format(mac_name.upper())
        body += macdef_create_str
        body += defs_str
        body += adm_add_macdef_str

        # Additional strings to be added if this the the manager code
        if mgr:
            body += meta_add_macro_template.format(mac_name, description)
            added_meta = True
            for parm in parms:
                amp_type = cu.make_amp_type_name_from_str(parm.type)
                body += meta_add_parm_template.format(parm.name, amp_type)

    # only add these declarations if the variables will be used; to avoid compiler warnings in C code
    if added_macdef:
        body = macdef_decl_str + body
    if added_meta:
        body = meta_decl_str + body

    write_formatted_init_function(c_file, adm.norm_namespace, cs.MACRO, body)

# Builds a template for the
# ```
# meta_add_...
# ```
# calls with passed collection type and adm name. Should be formatted in the calling
# function with:
# return_str.format(ari_amp_type, item[name], item[description])
#
# The intention behind this function is to only have to construct these parts once for each
# collection. Only a subset of values that need to be substituted for_each_ item in the
# collection, formatting ones related to coll and name here.
#
def make_std_meta_add_coll_template(coll, name):
    enum_name = cu.make_enum_name_from_str(name)
    coll_name = 'cnst' if coll == cs.META else cs.get_sname(coll).lower()
    return "meta_add_" + coll_name + "({0}, id, " + enum_name + ", \"{1}\", \"{2}\");\n"

#
# Writes the init_variables body
# for each variable creates a lyst for its postfix-expr and writes
# its appropriate adm_add_var function
#
# TODO: cur_ari in generated function is unused
#
def write_init_var_function(c_file, adm, g_var_idx, mgr):
    body = ""
    coll_decl_str = "\n\tari_t *id = NULL;\n"
    expr_decl_str = "\n\texpr_t *expr = NULL;\n"

    expr_create_str   = "\n\texpr = expr_create({});"
    expr_add_str      = "\n\texpr_add_item(expr, {});"
    add_var_from_expr = "\n\tadm_add_var_from_expr(id, {}, expr);"

    # gives you the adm_build_ari(...)
    build_str_template = "\n" + make_adm_build_ari_template(cs.VAR, g_var_idx, True)
    # gives you the meta_add_var(... )
    meta_add_template = make_std_meta_add_coll_template(cs.VAR, adm.norm_namespace)

    added_coll = False
    added_expr = False

    for obj in adm.var:
        # Preliminaries
        ari      = cu.make_ari_name(adm.norm_namespace, cs.VAR, obj)
        amp_type = cu.make_amp_type_name_from_str(obj.type)

        var_name    = obj.name
        description = obj.description or ''

        expr_str = ""

        # Add to the expr str for each postfix
        pfxs = obj.initializer.postfix.items if obj.initializer else []
        for pfx in pfxs:
            pfx_ns,pfx_coll,pfx_name = cu.ari_get_names(pfx)
            pfx_ari = cu.make_ari_name_from_str(pfx_ns, pfx_coll, pfx_name)
            pfx_g_var_idx = cu.get_g_var_idx(pfx_ns)
            #FIXME: _,param_flag  = retriever.postfix_has_params(pfx)
            param_flag = "0"

            pfx_build_ari = make_adm_build_ari_template(pfx_coll, pfx_g_var_idx, False).format(param_flag, pfx_ari)

            expr_str += expr_add_str.format(pfx_build_ari)

        # If postfixs are present, append the expr_create string, and prepend
        # the adm_add_var_from_expr stringq
        if pfxs:
            init_type = cu.make_amp_type_name_from_str(obj.initializer.type)

            expr_str = expr_create_str.format(init_type) + expr_str
            expr_str += add_var_from_expr.format(init_type)

            added_expr = True

        # Add formatted strings to body
        body += "\n\n\t/* {} */".format(var_name.upper())
        body +=  build_str_template.format("0", ari)
        body += expr_str

        # Additional meta_add function needs to be called if this is the mgr code generation
        if mgr:
            body += "\n\t" + meta_add_template.format(amp_type, var_name, description)

        added_coll = True

    # only add these declarations if the variables will be used; to avoid compiler warnings
    if added_expr:
        body = expr_decl_str + body
    if added_coll:
        body = coll_decl_str + body

    write_formatted_init_function(c_file, adm.norm_namespace, cs.VAR, body)


#
# writes the init_reports() function to the open file descriptor passed as c_file
# name is the value returned from get_adm_names()
# g_var_idx is the g_var_idx variable for the caller. Retriever is the retriever
# class instance to be used to populate the reports.
# mgr is a boolean value which will result in the addition of the meta_add_*()
# function for every report if == True
#
def write_parameterized_init_reports_function(c_file, adm, g_var_idx, mgr):
    body = ""
    rpt_decl_str  = "\n\trpttpl_t *def = NULL;\n"
    meta_decl_str =	"\n\tmetadata_t *meta = NULL;\n"
    added_rpt  = False
    added_meta = False

    rpt_create_template = "rpttpl_create_id({});"
    build_ari_str_template = make_adm_build_ari_template(cs.RPTT, g_var_idx, False)

    add_item_template = "\n\trpttpl_add_item(def, {});"
    adm_add_str       = "\n\tadm_add_rpttpl(def);"

    enum_name = cu.make_enum_name_from_str(adm.norm_namespace)
    meta_add_rpt_template  = "meta_add_rpttpl(def->id, " + enum_name + ", \"{0}\", \"{1}\");"
    meta_add_parm_template = "\n\tmeta_add_parm(meta, \"{0}\", {1});"

    for obj in adm.rptt:
        # Preliminaries
        rpt_name    = obj.name
        description = obj.description or ''

        ari    = cu.make_ari_name(adm.norm_namespace, cs.RPTT, obj)
        params = obj.parmspec.items if obj.parmspec else []
        defs   = obj.definition.items if obj.definition else []

        defs_str  = ""
        params_tf = "0"
        if params:
            params_tf = "1"

        # The rpt_create template is slightly different depending on presence of defs
        rpt_create_str = rpt_create_template.format(build_ari_str_template.format(params_tf, ari))
        if defs:
            rpt_create_str = "\n\tdef = " + rpt_create_str
            added_rpt = True
        else:
            rpt_create_str = "\n\t" + rpt_create_str

        # Add to the defs string for each definition found
        for item in defs:
            def_build_ari_str = _make_adm_build_ari_parm(adm, item, params)
            defs_str += add_item_template.format(def_build_ari_str)

        # Add all formatted strings to the body
        body += "\n\t/* {} */".format(obj.name.upper())
        body += rpt_create_str
        body += defs_str
        body += adm_add_str

        added_rpt = True

        # If this is the mgr code generation, need meta_add_rpt strings also
        if mgr:
            meta_add_rpt_str = meta_add_rpt_template.format(rpt_name, description)

            meta_add_parm_str = ""
            if params:
                meta_add_rpt_str = "meta = " + meta_add_rpt_str
                added_meta = True

            # Create meta_add_parm string for each parameter found
            for parm in params:
                amp_type = cu.make_amp_type_name_from_str(parm.type)
                meta_add_parm_str += meta_add_parm_template.format(parm.name, amp_type)

            # Add to body string
            body += "\n\t" + meta_add_rpt_str + meta_add_parm_str

    # only declare variables if they're going to be used
    if added_rpt:
        body = rpt_decl_str + body
    if added_meta:
        body = meta_decl_str + body

    write_formatted_init_function(c_file, adm.norm_namespace, cs.RPTT, body)

#
# Writes the init_tables funtion for the passed adm name and
# retriever class instance.
#
def write_init_tables_function(c_file, adm, g_var_idx, mgr):
    body = ""
    tbl_decl_str        = "\n\ttblt_t *def = NULL;"
    tbl_create_template = "\n\tdef = tblt_create({0}, {1});"

    build_ari_template = make_adm_build_ari_template(cs.TBLT, g_var_idx, False)
    enum_name = cu.make_enum_name_from_str(adm.norm_namespace)

    add_tblt_str      = "\n\tadm_add_tblt(def);"
    meta_add_template = "\n\tmeta_add_tblt(def->id, " + enum_name + ", \"{0}\", \"{1}\");"
    add_col_template  = "\n\ttblt_add_col(def, {0}, \"{1}\");"

    added_table = False

    for obj in adm.tblt:
        # Preliminaries
        ari = cu.make_ari_name(adm.norm_namespace, cs.TBLT, obj)
        tbl_name    = obj.name
        description = obj.description or ''

        cols = obj.columns.items if obj.columns else []
        cols_str = ""

        # Format the templates needed for the tables function
        tbl_build_ari_str = build_ari_template.format("0", ari)

        # The appearance of this template depends on whether this is the mgr code or not
        if mgr:
            tbl_create_str = tbl_create_template.format(tbl_build_ari_str, "NULL")
        else:
            tbl_create_str = tbl_create_template.format(tbl_build_ari_str, ari.lower())

        # Add to the cols string for each column present
        for col in cols:
            c_amp_type = cu.make_amp_type_name_from_str(col.type)
            cols_str += add_col_template.format(c_amp_type, col.name)

        # Add formatted strings to the body
        body += "\n\n\t/* {} */\n".format(tbl_name.upper())
        body += tbl_create_str
        body += cols_str
        body += add_tblt_str

        added_table = True

        # If this the the mgr code generation, also need to call meta_add function
        if mgr:
            body += meta_add_template.format(tbl_name, description)

    # tbl variable is only declared if needed; in order to avoid C compiler warnings for unused variable
    if added_table:
        body = tbl_decl_str + body

    write_formatted_init_function(c_file, adm.norm_namespace, cs.TBLT, body)

#
# Writes the init function to c_file
#
def write_init_function(c_file, adm: ace.models.AdmFile, g_var_idx: str, mgr: bool):
    enum_name = cu.make_enum_name_from_str(adm.norm_namespace)

    vdb_adds            = "\tadm_add_adm_info(\"" + adm.norm_namespace + "\", " + enum_name + ");\n"
    vdb_add_template    = "\n\tVDB_ADD_NN(((" + enum_name + " * 20) + {0}), &({1}[{0}]));"
    init_decl_template = "static void " + adm.norm_namespace + "_init_{0}(void);\n"
    init_call_template = "\n\t" + adm.norm_namespace + "_init_{0}();"

    # order of init functions matters
    obj_types = {
        cs.META: 'mdat',
        cs.CONST: 'const',
        cs.EDD: 'edd',
        cs.OP: 'oper',
        cs.VAR: 'var',
        cs.CTRL: 'ctrl',
        cs.MACRO: 'mac',
        cs.RPTT: 'rptt',
        cs.TBLT: 'tblt',
    }

    init_decls = ""
    init_calls = ""
    if not mgr:
        init_calls = "\n\t" + adm.norm_namespace + "_setup();"

    for coll, attrname in obj_types.items():
        init_decls += init_decl_template.format(cs.get_sname(coll).lower())

        # only generate NN's for elements that appear in the ADM
        if getattr(adm, attrname):
            vdb_adds += vdb_add_template.format(cs.get_adm_idx(coll), g_var_idx)

        init_calls += init_call_template.format(cs.get_sname(coll).lower())

    body = vdb_adds + "\n\n" + init_calls

    c_file.write(init_decls + "\n")
    write_formatted_init_function(c_file, adm.norm_namespace, None, body)

def make_cplusplus_open():
    ''' Open an "extern C" block for C++ inclusion. '''
    return """\
#ifdef __cplusplus
extern "C" {
#endif

"""

def make_cplusplus_close():
    ''' Close  an "extern C" block for C++ inclusion. '''
    return """\

#ifdef __cplusplus
}
#endif
"""