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

import camp.generators.lib.camputil as cu


#### NOTICE: These values are the area enumerations for nn as outlined in the new AMP
CONST  = 0
CTRL   = 1
EDD    = 2
MACRO  = 3
OP     = 4
RPTT   = 5
SBR    = 6
TBLT   = 7
TBR    = 8
VAR    = 9
META   = 10

# NOTE: sname and lname are often essentially the same, expect for CONST, OP, RPTT, and META
# NOTE: amp_type is often same as sname, except for OP and META
# NOTE: adm_idx is often the same as lname, except for META
# XXX: ensure these differences are necessary, or change if all could use same keyword.
collections = {}
collections[CONST] = {"sname":"cnst",   "lname":"Const", "ari_type":"0", "amp_type":"cnst",   "adm_idx":"Const"} # CONST = 0
collections[CTRL]  = {"sname":"ctrl",   "lname":"Ctrl",  "ari_type":"1", "amp_type":"ctrl",   "adm_idx":"Ctrl"}  # CTRL  = 1
collections[EDD]   = {"sname":"edd",    "lname":"Edd",   "ari_type":"2", "amp_type":"edd",    "adm_idx":"Edd"}   # EDD   = 2
collections[MACRO] = {"sname":"mac",    "lname":"Mac",   "ari_type":"4", "amp_type":"mac",    "adm_idx":"Mac"}   # MACRO = 3
collections[OP]    = {"sname":"op",     "lname":"Oper",  "ari_type":"5", "amp_type":"Oper",   "adm_idx":"Oper"}  # OP    = 4
collections[RPTT]  = {"sname":"rpttpl", "lname":"Rptt",  "ari_type":"7", "amp_type":"rpttpl", "adm_idx":"Rptt"}  # RPTT  = 5
collections[SBR]   = {"sname":"sbr",    "lname":"Sbr",   "ari_type":"8", "amp_type":"sbr",    "adm_idx":"Sbr"}   # SBR   = 6
collections[TBLT]  = {"sname":"tblt",   "lname":"Tblt",  "ari_type":"a", "amp_type":"tblt",   "adm_idx":"Tblt"}  # TBLT  = 7
collections[TBR]   = {"sname":"tbr",    "lname":"Tbr",   "ari_type":"b", "amp_type":"tbr",    "adm_idx":"Tbr"}   # TBR   = 8
collections[VAR]   = {"sname":"var",    "lname":"Var",   "ari_type":"c", "amp_type":"var",    "adm_idx":"Var"}   # VAR   = 9
collections[META]  = {"sname":"meta",   "lname":"Mdat",  "ari_type":"0", "amp_type":"cnst",   "adm_idx":"Meta"}  # META  = 10

# these last three are not needed for nn, but are filled in for use with ari_type_enum function
LIT    = 11
RPT    = 12
TBL    = 13
collections[LIT]   = {"ari_type":"3"}
collections[RPT]   = {"ari_type":"6"}
collections[TBL]   = {"sname":"tbl", "ari_type":"9"}


#
# Returns the area of the data type and its enumeration
# enumerations from sec 8 in ama
#
def ari_type_enum(coll):
    return collections[coll]["ari_type"]

#
# Area enumerations for nn as outlined in the new AMP
# The layout of the enums and collection above are in line with the area enumerations for nn.
#
def nn_type_enum(coll):
    # XXX: should check that coll < META, since only first 10 in the nn types?
    return coll

#
# Returns the short name for the passed collection type
# TODO: handle out of range
#
def get_sname(coll):
    return collections[coll]["sname"]

#
# Returns the long name for the passed collection type
# TODO: handle out of range
#
def get_lname(coll):
    return collections[coll]["lname"]

#
# Returns the amp_type variable name for the passed collection type
# TODO: handle out of range
#
def get_amp_type(coll):
    return cu.make_amp_type_name_from_str(collections[coll]["amp_type"])

#
#
#
def get_raw_amp_type(coll):
    return collections[coll]["amp_type"]

#
# Returns the ADM_XX_IDX variable name for the passed collection type
# TODO: handle out of range
#
def get_adm_idx(coll):
    return "ADM_"+collections[coll]["adm_idx"].upper()+"_IDX"

#
# Returns the collection type with the passed long or short name.
# Returns None if the name is not present
#
def name_get_coll(name):
    for key, value in collections.items():
        if(value["lname"].upper() == name.upper() or value["sname"].upper() == name.upper()):
            return key
    return None



