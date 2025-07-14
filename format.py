#from joos.core.utils import is_url

containers = ['\'', '"']
comment_strings = {'/*': '*/', '//': '\n'}


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
	finds hardcoded strings in js code and formats it
	"""
	string = container = comment_end = ''
	state = 'look'
	skip = 0
	comment = False
	all_strings = []
	
	# Use a context stack to handle nested structures
	context_stack = []
	
	# Enhanced context management for regex character classes
	context_type = None  # Track what type of context we are in
	in_regex_char_class = False  # Track if we're inside [..] within a regex
	
	# Template literal state tracking
	template_state = False
	template_content = ''
	brace_count = 0  # Track nested braces within ${}
	
	# Variables for code formatting
	formatted_code = ""
	current_line = ""
	indent_level = 0
	
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
					all_strings.append(template_content[:-1])  # Exclude closing backtick
			
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
					all_strings.append(string)
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
					current_line = '\t' * indent_level
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

		# Check for start of regex
		if char == '/':
			if i > 0:
				prev_char = code[i - 1]
				last_non_space_char = prev_char
				if prev_char.isspace():
					for j in range(i-1, -1, -1):
						if not code[j].isspace():
							last_non_space_char = code[j]
							break
				if last_non_space_char in ('=', '(', '[', '{', ',', ':', '?', '>', '+', '-', '*', '/', '|', '&', '!', ';') or \
				   code[i-6:i] == 'return' or code[i-7:i] == 'return ' or \
				   code[i-5:i] == 'throw' or code[i-6:i] == 'throw ':
					context_stack.append('/')
					current_line += char
					i += 1
					continue
			else: # Regex at start of file
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
				formatted_code += current_line + '\n'
				indent_level += 1
				current_line = '\t' * indent_level
			else:
				current_line += char
		elif char == '}':
			# Only handle formatting braces if not in regex character class
			if not (current_context == '/' and in_regex_char_class):
				if current_line.strip():
					formatted_code += current_line + '\n'
				indent_level = max(0, indent_level - 1)
				current_line = '\t' * indent_level + char
				if i + 1 < code_len and code[i + 1] not in ';}),':
					formatted_code += current_line + '\n'
					current_line = '\t' * indent_level
			else:
				current_line += char
		elif char == ';':
			current_line += char
			formatted_code += current_line + '\n'
			current_line = '\t' * indent_level
		elif char == '\n':
			if current_line.strip():
				formatted_code += current_line + '\n'
			current_line = '\t' * indent_level
		else:
			current_line += char
		i += 1
	
	# Add any remaining content
	if current_line.strip():
		formatted_code += current_line

	return all_strings, formatted_code
