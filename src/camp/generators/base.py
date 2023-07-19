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
''' Abstract base behavior for all generators.
'''
from typing import TextIO


class AbstractWriter:
    ''' Interface for any generator Writer class.

    :ivar admset: The :class:`AdmSet` to use.
    :ivar adm: The specific ADM to generate for.
    :ivar out_path: The output parent path to be used.
    '''
    def __init__(self, admset, adm, out_path, **kwargs):
        self.admset = admset
        self.adm = adm
        self.out_path = out_path

    def file_path(self) -> str:
        ''' Get the path to the file to be generated.
        This should be derived from :attr:`out_path`.

        :return: The full path for the file.
        '''
        raise NotImplementedError

    def write(self, outfile: TextIO):
        ''' Main function for the program. orchestrates calling all helper
        functions to generate the file text.

        :param outfile: The file object to write to.
        '''
        raise NotImplementedError


class CHelperMixin:
    ''' A mixin class for AbstractWriter to provide C language helpers.
    '''

#    def get_(self) -> str:
