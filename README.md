<!--
Copyright (c) 2023 The Johns Hopkins University Applied Physics
Laboratory LLC.

This file is part of the Asynchronous Network Managment System (ANMS).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

This work was performed for the Jet Propulsion Laboratory, California
Institute of Technology, sponsored by the United States Government under
the prime contract 80NM0018D0004 between the Caltech and NASA under
subcontract 1658085.
-->
# CAmpPython
This is the C code generator for the DTN Management Architecture (DTNMA).
It is part of the larger Asynchronous Network Managment System (ANMS) managed for [NASA AMMOS](https://ammos.nasa.gov/).



           (                 ,&&&.
             )                .,.&&
            (  (              \=__/
                )             ,'-'.
          (    (  ,,      _.__|/ /|
           ) /\ -((------((_|___/ |
         (  // | (`'      ((  `'--|
       _ -.;_/ \\--._      \\ \-._/.
      (_;-// | \ \-'.\    <_,\_\`--'|
      ( `.__ _  ___,')      <_,-'__,'
       `'(_ )_)(_)_)'


This tool uses the JSON representation of an Application Data Model (ADM) to
generate code for various purposes. CAmp generates:

- C code for usage in NASA ION (Interplanetary Overlay Network)
  - This generation can also carry over custom functions in existing C files for
    the ADM, if indicated appropriately in the existing code (see the
    Round-tripping Section). 
- SQL code, also for usage in NASA ION

Additional generators may be added to account for use cases outside of the reference DTNMA Agent.
Please contact the developers for more information or suggestions. The
Architecture Section also provides some explanation of the components of CAmp,
and how to incorporate additional generators.

**NOTE**
CAmp largely assumes that the ADM JSON input can be trusted (i.e., CAmp does not
go to great lengths to fully sanitize all strings found within the ADM). CAmp
does properly escape necessary sequences found in the ADMs tested during
development (e.g., apostrophes in object descriptions).

## Development

To install development and test dependencies for this project, run from the root directory (possibly under sudo if installing to the system path):
```sh
pip3 install -r <(python3 -m piptools compile --extra test pyproject.toml 2>&1)
```

To install the project itself from source run:
```
pip3 install .
```

### View Usage Options for CAmp

```
    camp -h
```

### Basic Usage

The camp tool takes a JSON representation of an ADM for a network protocol as
input and calls each of the included generators to generate files for the ADM.

> The included `template.json` provides an example of how a JSON ADM should be
> formatted. For more information on this data model, please consult the AMA
> Application Data Model IETF draft.

Given the JSON representation of the ADM, run camp with:

```
   camp <adm.json>
```

### Name Registry

If you're generating files for a new ADM, you may see an error similar to the
following: 

```
[Error] this ADM is not present in the name registry. Pass integer value via
command line or set manually in name_registry.cfg
```

This is because the name of the ADM is not yet present in the camp Name
Registry. To solve this, pass the nickname value for the ADM to camp via the
`-n` command line option:

```
    camp <adm.json> -n <value>
```

You can also use the `-n` option to make camp use a different nickname for an
ADM that is present in the camp Name Registry. For example,

```
    camp bp_agent.json -n 23
```

Will generate bp_agent files with a nickname of `23` instead of the registered
value of `2`. To make these changes permanent (or to add a new ADM to the
name registry), pass the `-u` flag to camp:

```
    camp <adm.json> -n <value> -u
```

### Output

During a successful camp execution, output similar to the following will be
printed to STDOUT.

```
Loading  <path_to_json_file>/<adm.json>  ... 
[ DONE ]
Generating files ...
Working on  .//agent/adm_<adm>_impl.h 	[ DONE ]
Working on  .//agent/adm_<adm>_impl.c 	[ DONE ]
Working on  .//adm_<adm>.sql 		[ DONE ]
Working on  .//shared/adm_<adm>.h 	[ DONE ]
Working on  .//mgr/adm_<adm>_mgr.c 	[ DONE ]
Working on  .//agent/adm_<adm>_agent.c 	[ DONE ]
[ End of CAmpPython Execution ]
```

This output shows that camp completed a successful generation of each of the
files listed. If they don't already exist, camp will create the following
directories in the current directory:

- agent
- shared
- mgr

and put generated files into the appropriate created directory. Use the `-o`
flag with camp to redirect output to a different directory.

```
    camp <adm.json> -o <output_directory>
```

If the path at <output_directory> does not already exist, camp will create it,
and will create the directories listed above within <output_directory>.

> Camp will not delete any existing directory structure, but files present in
> the output directories with the same name as generated files will be
> overwritten. 

Custom Code and Round-tripping
------------------------------

The `adm_<adm>_impl.c` and `adm_<adm>_impl.h` files generated for NASA ION
contain functions whose bodies cannot be automatically generated with knowledge
of the ADM alone. When generated, these fuctions are marked with tags similar to
the following:

```
    /*
     * +----------------------------------------------------------------------+
     * |START CUSTOM FUNCTION <function_name> BODY
     * +----------------------------------------------------------------------+
     */	
    /*
     * +----------------------------------------------------------------------+
     * |STOP CUSTOM FUNCTION <function_name> BODY	
     * +----------------------------------------------------------------------+
     */	
```

Additionally, the user may wish to add additional custom functions and/or header
files to these generated files. To allow re-generation of camp files with
minimal re-work for custom code in these files, camp has a 'roundtripping'
feature that allows preservation of these custom additions in subsequent file
generations. 

The roundtripping feature in camp will save any code in the file that falls
between camp custom tags, and will add it to the newly-generated version of the
file. Example usage:

```
    camp <adm.json> -c <path_to_existing_impl.c> -h <path_to_existing_impl.h>
```

The resulting generated impl.c and impl.h files will contain the custom code
from the impl.c and impl.h files passed to camp. 

Current acceptable custom tags are:

- custom function body (example above)
- custom includes (`/* [START|STOP] CUSTOM INCLUDES HERE */`)
- custom functions (`/* [START|STOP] CUSTOM FUNCTIONS HERE */`)

For custom function bodies, the <function_name> included in the custom function
tag must be the same as the one used in the ADM for the custom function to be
copied over to the correct area of the new file. 

### CAmp Architecture

- template.json   - Example JSON ADM template
- src/camp/     - contains all of the source code for camp
  - tools/camp.py - Main script of camp. This script calls all necessary 
                    generators and handles user input
  - data/name_registry.cfg - Initial name registry configuration file installed 
                             with camp.
  - generators/   - All generator scripts and their utility functions
    - create_agent_c.py  - Generates agent file (C code) for usage in NASA ION
    - create_gen_h.py  - Generates the shared header file needed for NASA ION
    - create_impl_c.py - Generates the implementation file (C code) for usage in
                         NASA ION
    - create_impl_h.py - Generates the header file for the implementation file
                         created by create_impl_c.py
    - create_mgr_c.py  - Generates the manager file for usage in NASA ION
    - create_sql.py  - Generates an SQL file for usage with NASA ION stored
                         procedures
    - lib/        - Library functions for generating commonly-used patterns and 
                    accessing portions of the ADM.
      - campch.py - library functions commonly needed specifically for C code 
                    generators. 
      - campch_roundtrip.py - round-tripping functions
      - common/             - Library functions helpful to all generators. 
        - campsettings.py   - initializes various global variables for camp 
                              (enumerations for portions of the ADM, etc.)
        - camputil.py       - utility functions for parsing the JSON input file 
                              and creating ARIs. Contains the Retriever class, 
                              which is used by all generators to access ADM data
        - jsonutil.py       - utility functions to validate JSON input.
                    

### Adding Generators

To add a new generator to camp, create a python script that creates the file
and add it to the `CAmpPython/generators/` directory. Then, in CAmpPython.py, 
import the new generator and add it to the file generation code of the `main()`
function (starting at line 105).

All generators should: 
- define a `create()` method as their main function, which takes as its first 
  and second argument:
    1. a Retriever object (pre-populated with the ADM passed to camp)
    2. a string that represents the path to the output directory
- utilize the Retriever object to access fields of the JSON ADM
- place generated file(s) in the output directory passed as the second argument
  to the `create()` function (the generator may choose to make a sub-directory 
  in the output directory)


## Contributing

To contribute to this project, through issue reporting or change requests, see the [CONTRIBUTING](CONTRIBUTING.md) document.
