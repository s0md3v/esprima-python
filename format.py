#from joos.core.utils import is_url

containers = ['\'', '"']
comment_strings = {'/*': '*/', '//': '\n'}


def _detect_indentation(code):
	"""
	Detects the indentation style used in the given code.
	Returns a tuple (indent_type, indent_size) where:
	- indent_type is 'tab' or 'space'
	- indent_size is the number of spaces per indentation level (or 1 for tabs)
	"""
	lines = code.split('\n')
	space_indents = []
	tab_count = 0
	
	for line in lines:
		if not line.strip():  # Skip empty lines
			continue
			
		# Count leading whitespace
		leading_spaces = 0
		leading_tabs = 0
		for char in line:
			if char == ' ':
				leading_spaces += 1
			elif char == '\t':
				leading_tabs += 1
			else:
				break
		
		if leading_tabs > 0:
			tab_count += 1
		elif leading_spaces > 0:
			space_indents.append(leading_spaces)
	
	# Determine indentation style
	if tab_count > len(space_indents):
		return ('tab', 1)
	elif space_indents:
		# Calculate the most common indentation size for spaces
		# Find the GCD of all indentation levels to get the base unit
		from math import gcd
		from functools import reduce
		
		if len(space_indents) == 1:
			return ('space', space_indents[0])
		
		indent_size = reduce(gcd, space_indents)
		if indent_size == 0:
			indent_size = 2  # Default to 2 spaces if we can't determine
		return ('space', indent_size)
	
	# Default to tabs if no indentation detected
	return ('tab', 1)


def _normalize_line_indentation(line, detected_style):
	"""
	Strips existing indentation from a line and returns the cleaned line
	and the logical indentation level.
	"""
	if not line.strip():
		return '', 0
	
	indent_type, indent_size = detected_style
	leading_spaces = 0
	leading_tabs = 0
	
	for char in line:
		if char == ' ':
			leading_spaces += 1
		elif char == '\t':
			leading_tabs += 1
		else:
			break
	
	# Calculate logical indentation level
	if indent_type == 'tab':
		# If using tabs, count tabs primarily, convert spaces to tab equivalents
		logical_level = leading_tabs + (leading_spaces // 4)  # Assume 4 spaces = 1 tab
	else:
		# If using spaces, count spaces primarily, convert tabs to space equivalents
		logical_level = (leading_spaces + leading_tabs * 4) // indent_size
	
	# Return the line without leading whitespace and the logical level
	return line.lstrip(), logical_level


def _is_escaped(string):
	"""
	checks if given string can escape a suffix
	returns bool
	"""
	count = 0
	for char in reversed(string):
		if char == '\\':
			count += 1
		else:
			break
	return count % 2


def _if_comment_started(string, comment_strings):
	"""
	checks if given string starts a comment
	returns string required to close the comment and length of string that started the comment
	returns False on failure
	"""
	for comment_start, comment_end in comment_strings.items():
		if string.startswith(comment_start):
			return (comment_end, len(comment_start))


def format(code):
	"""
	finds hardcoded strings in js code and formats it with formatting awareness
	"""
	string = container = comment_end = ''
	state = 'look'
	skip = 0
	comment = False
	all_strings = {}
	
	# Use a context stack to handle nested structures
	context_stack = []
	
	# Enhanced context management for regex character classes
	context_type = None  # Track what type of context we are in
	in_regex_char_class = False  # Track if we're inside [..] within a regex
	
	# Enhanced state tracking for better regex vs division detection
	last_meaningful_token = None  # Track the last meaningful token we encountered
	paren_stack = []  # Track parentheses to understand if we're in control structures
	
	# Template literal state tracking
	template_state = False
	template_content = ''
	brace_count = 0  # Track nested braces within ${}
	
	# Detect existing indentation style and formatting level
	detected_style = _detect_indentation(code)
	indent_type, indent_size = detected_style
	
	# Check if code is already reasonably formatted
	lines = code.split('\n')
	has_reasonable_formatting = any(line.strip() and (line.startswith('\t') or line.startswith(' ')) for line in lines[1:])
	
	# Variables for code formatting
	formatted_code = ""
	current_line = ""
	indent_level = 0
	formatted_line_number = 1  # Track current line number in formatted code
	
	def _generate_indent(level):
		"""Generate indentation string based on detected style"""
		if indent_type == 'tab':
			return '\t' * level
		else:
			return ' ' * (level * indent_size)
	
	def _clean_line_start():
		"""Clean existing indentation from current_line and apply proper indentation"""
		nonlocal current_line
		stripped = current_line.lstrip()
		if stripped != current_line:  # There was indentation to remove
			current_line = _generate_indent(indent_level) + stripped
		elif not current_line and indent_level > 0:  # Empty line, need indentation
			current_line = _generate_indent(indent_level)
	
	i = 0
	code_len = len(code)
	while i < code_len:
		char = code[i]
		if skip > 0:
			skip -= 1
			i += 1
			continue

		buff = code[i:i+4]
		current_context = context_stack[-1] if context_stack else None

		# --- Template literal handling ---
		if template_state:
			# Check for expression braces within template
			if char == '$' and i + 1 < code_len and code[i+1] == '{':
				template_content += '${'
				current_line += '${'
				brace_count += 1
				i += 2  # Skip both $ and {
				continue
			else:
				# Always add character to template content
				template_content += char
				current_line += char
				
				if char == '{' and brace_count > 0:
					brace_count += 1
				elif char == '}' and brace_count > 0:
					brace_count -= 1
				# Check for end of template literal (only if not within expression)
				elif char == '`' and brace_count == 0 and not _is_escaped(code[:i]):
					template_state = False
					all_strings[template_content[:-1]] = formatted_line_number  # Use current line number
			
			i += 1
			continue  # Always continue when in template state

		# --- Normal parsing below ---
		# Handle regex
		if current_context == '/':
			# Check for character class start/end within regex
			if char == '[' and not _is_escaped(code[:i]):
				in_regex_char_class = True
			elif char == ']' and in_regex_char_class and not _is_escaped(code[:i]):
				in_regex_char_class = False
			elif char == '/' and not in_regex_char_class and not _is_escaped(code[:i]):
				# Only end regex if we're not in a character class
				context_stack.pop()
				in_regex_char_class = False
			current_line += char
			i += 1
			continue

		# Handle strings
		elif current_context in ('"', "'"):
			if char == current_context and not _is_escaped(code[:i]):
				context_stack.pop()
				if string:
					all_strings[string] = formatted_line_number  # Use current line number
				string = ''
			else:
				string += char
			current_line += char
			i += 1
			continue

		# Handle comments
		if comment:
			if buff.startswith(comment_end):
				current_line += comment_end
				skip = len(comment_end) - 1
				comment = False
				if comment_end == '\n':
					formatted_code += current_line
					formatted_line_number += 1
					current_line = _generate_indent(indent_level)
				i += 1
				continue
			current_line += char
			i += 1
			continue

		started = _if_comment_started(buff, comment_strings)
		if started:
			comment = True
			comment_end = started[0]
			current_line += buff[:started[1]]
			skip = started[1] - 1
			i += 1
			continue

		# --- Context-free parsing logic ---

		# Check for start of template literal
		if char == '`':
			# Only start template literal if not in regex character class
			if not (current_context == '/' and in_regex_char_class):
				template_state = True
				template_content = ''
			current_line += char
			i += 1
			continue

		# Track parentheses for control structure detection
		if char == '(':
			paren_stack.append(i)
		elif char == ')' and paren_stack:
			paren_stack.pop()

		# Check for start of regex
		if char == '/':
			is_regex = False
			
			if i > 0:
				# Get the last non-space character
				prev_char = code[i - 1]
				last_non_space_char = prev_char
				last_non_space_pos = i - 1
				
				if prev_char.isspace():
					for j in range(i-1, -1, -1):
						if not code[j].isspace():
							last_non_space_char = code[j]
							last_non_space_pos = j
							break
				
				# Basic regex detection: characters that typically precede regex
				if last_non_space_char in ('=', '(', '[', '{', ',', ':', '?', '>', '+', '-', '*', '/', '|', '&', '!', ';'):
					is_regex = True
				
				# Check for keywords that precede regex
				elif (code[i-6:i] == 'return' or code[i-7:i] == 'return ' or 
					  code[i-5:i] == 'throw' or code[i-6:i] == 'throw '):
					is_regex = True
				
				# Enhanced detection: check for control structures like if(...), while(...), for(...)
				elif last_non_space_char == ')':
					# Look backwards to see if this ) closes a control structure
					# We need to find the matching ( and see what precedes it
					control_keywords = ['if', 'while', 'for', 'switch']
					paren_count = 1
					j = last_non_space_pos - 1
					
					# Find the matching opening parenthesis
					while j >= 0 and paren_count > 0:
						if code[j] == ')':
							paren_count += 1
						elif code[j] == '(':
							paren_count -= 1
						j -= 1
					
					if paren_count == 0:  # Found matching (
						# Look for control keywords before the (
						keyword_start = j + 1
						while keyword_start > 0 and code[keyword_start - 1].isspace():
							keyword_start -= 1
						
						for keyword in control_keywords:
							keyword_len = len(keyword)
							if (keyword_start >= keyword_len and 
								code[keyword_start - keyword_len:keyword_start] == keyword and
								(keyword_start == keyword_len or not code[keyword_start - keyword_len - 1].isalnum())):
								is_regex = True
								break
			else:
				# Regex at start of file
				is_regex = True
			
			if is_regex:
				context_stack.append('/')
				current_line += char
				i += 1
				continue

		# Check for start of strings
		if char in containers:
			context_stack.append(char)
			string = '' # Reset string for ' and "
			current_line += char
			i += 1
			continue

		# Handle formatting
		if char == '{':
			# Only handle formatting braces if not in regex character class
			if not (current_context == '/' and in_regex_char_class):
				current_line += char
				# Only add newline if not already reasonably formatted or next char isn't already a newline
				if not has_reasonable_formatting or (i + 1 < code_len and code[i + 1] != '\n'):
					formatted_code += current_line + '\n'
					formatted_line_number += 1
					indent_level += 1
					current_line = _generate_indent(indent_level)
				else:
					formatted_code += current_line
					formatted_line_number += current_line.count('\n')
					indent_level += 1
					current_line = ""
			else:
				current_line += char
		elif char == '}':
			# Only handle formatting braces if not in regex character class
			if not (current_context == '/' and in_regex_char_class):
				if current_line.strip():
					formatted_code += current_line + '\n'
					formatted_line_number += 1
				indent_level = max(0, indent_level - 1)
				current_line = _generate_indent(indent_level) + char
				if i + 1 < code_len and code[i + 1] not in ';}),\n':
					formatted_code += current_line + '\n'
					formatted_line_number += 1
					current_line = _generate_indent(indent_level)
			else:
				current_line += char
		elif char == ';':
			current_line += char
			# Only handle formatting semicolons if not in regex character class and not inside parentheses (for loops)
			if not (current_context == '/' and in_regex_char_class) and not paren_stack:
				# Only add newline if not already reasonably formatted or next char isn't already a newline
				if not has_reasonable_formatting or (i + 1 < code_len and code[i + 1] != '\n'):
					formatted_code += current_line + '\n'
					formatted_line_number += 1
					current_line = _generate_indent(indent_level)
				else:
					formatted_code += current_line
					formatted_line_number += current_line.count('\n')
					current_line = ""
		elif char == '\n':
			if current_line.strip():
				formatted_code += current_line + '\n'
				formatted_line_number += 1
			else:
				formatted_code += '\n'
				formatted_line_number += 1
			current_line = ""  # Start fresh, will add indentation when needed
		else:
			# If this is the first non-whitespace character on a new line, handle indentation
			if not current_line and char not in ' \t':
				current_line = _generate_indent(indent_level) + char
			elif not current_line and char in ' \t':
				# Skip existing indentation at the start of a line
				pass  # Don't add it to current_line
			else:
				# Add the character if we're continuing a line or if it's meaningful whitespace
				if current_line or char not in ' \t':
					current_line += char
		i += 1
	
	# Add any remaining content
	if current_line.strip():
		formatted_code += current_line
		formatted_line_number += current_line.count('\n')

	return all_strings, formatted_code
