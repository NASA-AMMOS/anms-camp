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

import json
import re
import os
import errno

import camp.generators.lib.campsettings as cs


######################## GENERAL FUNCTIONS ####################

# XXX: these functions could be updated and put into the retriever class.

def get_g_var_idx(ns):
    ns = ns.lower().replace("/", "_")
    return "g_" + ns + "_idx"

def ari_get_names(jari):
    adm_ns = jari.ns
    coll, name = jari.nm.split('.')

    coll = cs.name_get_coll(coll)
    name = name.split('(')[0]

    return adm_ns, coll, name

#
# Formats and returns a string for the ari
# name is the value returned from a call to initialize_names, coll is the
# collection the item belongs to (cs.[EDD|VAR|...]), item is the item to
# make the ari for i_name is the name of the item
#
def make_ari_name_from_str(name, coll, i_name):
    name = name.replace("/", "_")
    template = "{0}_{1}_{2}"
    return template.format(name.upper(), cs.get_sname(coll).upper(), i_name.upper())

#
# Formats and returns a string for the ari
# name is the value returned from a call to initialize_names, coll is the
# collection the item belongs to (VAR, EDD, etc), item is the item to make
# the ari for
# Assumes that the passed item has a valid "name" field
#
def make_ari_name(name, coll, item):
    return make_ari_name_from_str(name, coll, item.name)

#
# Makes and returns the amp type string for the passed item
# t_name is the name of the type
#
def make_amp_type_name_from_str(t_name):
    return "AMP_TYPE_{}".format(t_name.upper())

#
# Makes and returns the adm enum type string for the passed
# item. name is the name of the item
#
def make_enum_name_from_str(name):
    return "ADM_ENUM_{}".format(name.upper())
