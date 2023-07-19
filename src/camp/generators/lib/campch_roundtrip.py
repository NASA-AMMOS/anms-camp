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

import re

#
# Class to handle scraping files, and writing custom tags and code to
# newly-generated files.
#
class Scraper(object):
	
	################## HELPER FUNCTIONS TO MAKE \CUSTOM\ TAGS FOR FILE #############

	#
	# Returns a tuple of the custom includes start and end markers
	#
	def _make_custom_includes_markers(self):
		return "/*   START CUSTOM INCLUDES HERE  */", "/*   STOP CUSTOM INCLUDES HERE  */"

	#
	# Returns a tuple of the custom functions start and end markers
	#
	def _make_custom_functions_markers(self):
		return "/*   START CUSTOM FUNCTIONS HERE */", "/*   STOP CUSTOM FUNCTIONS HERE  */"


	######## HELPER FUNCTIONS FOR PARSING INTERNAL DATA STRUCT FOR CUSTOM CODE ##########

	
	#
	# Pops items off of the passed queue (list) structure, searching
	# for the custom includes tags. Returns all lines encompassed in these tags
	#
	# lines: lines to search
	# Returns: (list, list) tuple that is 1) list of strings from between the custom
	# includes tags and 2) updated 'lines' queue (evaluated lines are popped off)
	#
	# NOTICE: since this is treating lines as a queue, it will evaluate lines in
	# reverse order (popping off the end of the list).
	#	
	def _find_custom_includes_in_queue(self, lines):
		includes = []
		line = ""
		
		start, end = self._make_custom_includes_markers()
		
		# find the start
		while (len(lines) != 0 and line.strip() != start):
			line = lines.pop()

		# Append until we find the end
		while(len(lines) != 0):
			line = lines.pop()
			if(line.strip() == end):
				break
			includes.append(line)
		
		return includes, lines	

	#
	# Pops items off of the passed queue (list) structure, searching
	# for the custom functions tags. Returns all lines encompassed in these tags
	#
	# lines: lines to search
	# Returns: (list, list) tuple that is 1) list of strings from between the custom
	# function tags and 2) updated 'lines' queue (evaluated lines are popped off)
	#
	# NOTICE: since this is treating lines as a queue, it will evaluate lines in
	# reverse order (popping off the end of the list).
	#
	def _find_custom_functions_in_queue(self, lines):
		custom_func = []
		line = ""

		start, end = self._make_custom_functions_markers()
	
		# find the start
		while (len(lines) != 0 and line.strip() != start):
			line = lines.pop()

		# Append until we find the end
		while(len(lines) != 0):
			line = lines.pop()
			if(line.strip() == end):
				break
			custom_func.append(line)
		
		return custom_func, lines

	
	############ FUNCTIONS TO WRITE SCRAPED CUSTOM CODE TO FILE, WITH SURROUNDING TAGS ###########

	#
	# Write the standard 'CUSTOM' tag for the includes at the top of a file
	# Adds any passed custom content between the start and stop tags
	# file: open file descriptor to write to
	# custom: array of lines to add as custom content (from scraping)
	# if custom is empty, will just write the tags to the file
	#
	def write_custom_includes(self, file):
		start, end = self._make_custom_includes_markers()
	
		file.write(start + "\n")
		for line in self.includes:
			file.write(line);
		file.write(end + "\n\n")
	
	#
	# Write the standard 'CUSTOM' tag for custom functions
	# Adds any passed custom content between the start and stop tags
	#
	# file: open file descriptor to write to
	# custom: array of lines to add as custom content (from scraping)
	# if custom is empty, will just write the tags for custom content to the file
	#
	def write_custom_functions(self, file):
		start, end = self._make_custom_functions_markers()
	
		file.write(start + "\n")
		for line in self.functions:
			file.write(line)
		file.write(end + "\n\n")

	
####################### CHILD CLASSES FOR H- or C-files ############################

#
# C-file scraper class is a child of the Scraper class
#
class C_Scraper(Scraper):
	#
	# Helper function that returns the indicator and custom tag used by the custom bodies.
	# TODO: This is split out differently than the others and is not ideal because of how 
	# the scraper deals with multi-line tags. Try to simplify.
	#
	def _get_custom_body_pieces(self):
		indicator = "* +-------------------------------------------------------------------------+"
		marker  = '|{} CUSTOM FUNCTION {} BODY'
		return indicator, marker

	#
	# Returns a tuple of the (indicator, start marker, end marker) strings for use with a
	# regex search for custom function bodies. 
	#
	def _get_custom_body_re_markers(self):
		indicator, marker = self._get_custom_body_pieces()
		
		marker = '\* \\' + marker
		function_string_matcher = '(.+)'
	
		return indicator, marker.format('START', function_string_matcher), marker.format('STOP', function_string_matcher)
	
	#
	# Pops items off of the passed queue (list) structure, searching
	# for the function custom body tags. Returns all dictonary of key:value pairs for
	# lines encompassed in these tags, where the key is the function name, and value
	# is the list of custom lines for that function
	# This exhausts the entire passed queue, so unlike the other find*_custom_*() functions,
	# it does not return a list of remaining lines in the queue
	#
	# lines: lines to search
	#
	# NOTICE: since this is treating lines as a queue, it will evaluate lines in
	# reverse order (popping off the end of the list).
	#
	def _find_func_custom_body_in_queue(self, lines):
		func_bods = {}
		func = None

		indicator, start_re, end_re = self._get_custom_body_re_markers()

		# While lines remain in the queue, pop one off and evaluate it
		while len(lines) != 0:
			line = lines.pop()
			clean_line = line.strip()

			# If we're inside one of the custom function bodies
			# keep appending until end
			if(func is not None):

				# Append to this function's dictionary entry until you reach
				# another indicator with an end tag
				if(clean_line == indicator):
					line = lines.pop()
					clean_line = line.strip()
				
					if(re.match(end_re, clean_line) != None):
						func_bods[func].pop()
						func = None
					else:		
						continue			
				else:
					if(not func in func_bods):
						func_bods[func] = []
					func_bods[func].append(line)
				
			# Check if this line is the start of a new custom function body
			else:
				s = re.search(start_re, clean_line)
				if s != None:
					func = s.group(1)

		return func_bods		

	#
	# Returns a tuple of the custom body's start and end markers
	#
	def _make_custom_body_markers(self, function):
		indicator, marker = self._get_custom_body_pieces()

		template = ("\t/*\n"
			    "\t {0}\n"
			    "\t * {1}\n"
			    "\t {0}\n"
			    "\t */\n")

		start_marker = marker.format("START", function)
		end_marker = marker.format("STOP", function)

		return template.format(indicator, start_marker), template.format(indicator, end_marker)

		
	#
	# Write the standard 'CUSTOM' tag for the body of a standard function
	#
	# file: open file descriptor to write to
	# function: function name
	# custom: array of lines to add as custom function body content (from scraping)
	# if custom is empty, will just write the tags for custom content to the file
	#
	def write_custom_body(self, file, function):
		custom = self.func_bods.get(function, [])
		start, end = self._make_custom_body_markers(function)
		
		file.write(start)
		for line in custom:
			file.write(line)
		file.write(end)

		
	#
	# Constructor for the C_Scraper Class
	#
	# In the function custom bodies dictionary, the name of the function serves
	# as the key, and the value is a list of strings that make up the custom body
	# of that function.
	#
	def __init__(self, f):
		self.filename  = f
		self.includes  = ["/*             TODO              */\n"]
		self.functions = ["/*             TODO              */\n"]
		self.func_bods = {}
	
		if self.filename is None:
			return
		
		print("Scraping ", self.filename, " ... ",)

		c = []
		# Insert each line into a queue
		# NOTE: this results in the first line of the file being last in c
		# (find_* functions appropriately pop off the end of c).
		try:
			for line in open(self.filename).readlines(): 
				c.insert(0,line)
		except IOError as e:
			print("[ Error ] Failed to open ", self.filename, " for scraping.")
			print(e)

		self.includes,  c = self._find_custom_includes_in_queue(c)
		self.functions, c = self._find_custom_functions_in_queue(c)
		self.func_bods    = self._find_func_custom_body_in_queue(c)

		print("\t[ DONE ]")
		
		# Sanity Check. If scraping was requested and returned nothing, let the user know
		if (len(self.includes) == 0 and len(self.functions) == 0 and len(self.func_bods) == 0):
			print("\t[ Warning ] No custom input found to scrape in ", self.filename)

		
#
# h-file scraper class is a child of the Scraper class.
#
class H_Scraper(Scraper):
	#
	# Returns a tuple of the custom type_enum start and end markers
	#
	def _make_custom_type_enum_markers(self):
		return "/*   START typeENUM */", "/*   STOP typeENUM  */"

	#
	# Pops items off of the passed queue (list) structure, searching
	# for the type_enum tag. Returns all lines encompassed in these tags
	# lines: lines to search
	# Returns: (list, list) tuple that is 1) list of strings from between the custom
	# function tags and 2) updated 'lines' queue (evaluated lines are popped off)
	#
	# NOTICE: since this is treating lines as a queue, it will evaluate lines in
	# reverse order (popping off the end of the list).
	#
	def _find_type_enums_in_queue(self, lines):
		enums = []
		line = ""
		
		start, end = self._make_custom_type_enum_markers()
			
		# find the start
		while (len(lines) != 0 and line.strip() != start):
			line = lines.pop()
			
		# Append until we find the end
		while(len(lines) != 0):
			line = lines.pop()
			
			if(line.strip() == end):
				break
			enums.append(line)
			
		return enums, lines

	
	# Writes the type enum tags and if scraping was required any 
	# typeENUMS that were found
	#
	def write_custom_type_enums(self, file):
		start, end = self._make_custom_type_enum_markers()
	
		file.write(start + "\n")
		for line in self.type_enums:
			file.write(line)
		file.write(end + "\n\n")

	#
	# Constructor for the H_Scraper class
	#
	def __init__(self, f):
		self.filename   = f
		self.includes   = ["/*             TODO              */\n"]
		self.functions  = ["/*             TODO              */\n"]
		self.type_enums = ["/*             TODO              */\n"]

		h = []

		if self.filename is None:
			return

		print("Scraping ", self.filename, " ... ",)

		# Insert each line into a queue
		# NOTE: this results in the first line of the file being last in h
		# (find_* functions appropriately pop off the end of h).
		try:
			for line in open(self.filename).readlines(): 
				h.insert(0,line)
		except IOError as e:
			print("[ Error ] Failed to open ", fd, " for scraping.")
			print(e)
			
		self.includes,    h = self._find_custom_includes_in_queue(h)
		self.type_enums,  h = self._find_type_enums_in_queue(h)
		self.functions, h = self._find_custom_functions_in_queue(h)

		print("\t[ DONE ]")

		# Sanity Check. If scraping was requested and returned nothing, let the user know
		if (len(self.includes) == 0 and len(self.functions) == 0 and len(self.type_enums) == 0):
			print("\t[ Warning ] No custom input found to scrape in ", self.filename)

				

		



