import re
from typing import List, Tuple, Optional

class LatexTranspiler:
    def __init__(self):
        # --- Settings Defaults ---
        self.section_id = "##"
        self.subsection_id = "###"
        self.include_title = True
        
        # 1. Text Mode: Characters that must be escaped in normal prose
        self.text_special_chars = {
            '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
            '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\^{}'
        }
        
        # 2. Math Mode: Unicode -> LaTeX Command Map
        self.math_map = {
            # Greek, Operators, etc.
            'α': r'\alpha', 'β': r'\beta', 'γ': r'\gamma', 'δ': r'\delta', 'ϵ': r'\epsilon', 
            'ε': r'\varepsilon', 'ζ': r'\zeta', 'η': r'\eta', 'θ': r'\theta', 'ι': r'\iota', 
            'κ': r'\kappa', 'λ': r'\lambda', 'μ': r'\mu', 'ν': r'\nu', 'ξ': r'\xi', 
            'π': r'\pi', 'ρ': r'\rho', 'σ': r'\sigma', 'τ': r'\tau', 'υ': r'\upsilon', 
            'φ': r'\phi', 'χ': r'\chi', 'ψ': r'\psi', 'ω': r'\omega',
            'Γ': r'\Gamma', 'Δ': r'\Delta', 'Θ': r'\Theta', 'Λ': r'\Lambda', 
            'Ξ': r'\Xi', 'Π': r'\Pi', 'Σ': r'\Sigma', 'Φ': r'\Phi', 'Ψ': r'\Psi', 'Ω': r'\Omega',
            '⊕': r'\oplus', '⊗': r'\otimes', '⊖': r'\ominus', '⊙': r'\odot',
            '×': r'\times', '·': r'\cdot', '÷': r'\div', '±': r'\pm',
            '≤': r'\le', '≥': r'\ge', '≠': r'\neq', '≈': r'\approx', '≡': r'\equiv',
            '→': r'\to', '←': r'\gets', '⇒': r'\Rightarrow', '⇔': r'\Leftrightarrow', '↦': r'\mapsto',
            '∀': r'\forall', '∃': r'\exists', '¬': r'\neg', '∧': r'\land', '∨': r'\lor',
            '∈': r'\in', '∉': r'\notin', '⊂': r'\subset', '⊃': r'\supset', 
            '⊆': r'\subseteq', '⊇': r'\supseteq', '∪': r'\cup', '∩': r'\cap', 
            '∅': r'\emptyset', '∞': r'\infty', '∂': r'\partial', '∇': r'\nabla', 
            '∑': r'\sum', '∏': r'\prod', '∫': r'\int', '...':r'\ldots', '◦':r'\circ',
            '*': r'\times', '{': r'\{', '}': r'\}'
        }

        # 3. English Anchor Words (Base Set)
        self.english_anchors = {
            'the', 'and', 'for', 'is', 'are', 'this', 'that', 'with', 'from', 'to', 'in', 'on', 'by', 'send', 'sends', 'single', 'response',
            'an', 'as', 'at', 'be', 'or', 'we', 'our', 'it', 'if', 'then', 'of', 'can', 'has', 'have','security',
            'result', 'method', 'using', 'given', 'where', 'let', 'assume', 'note', 'function', 'define','fundamental',
            'suppose', 'hence', 'thus', 'therefore', 'show', 'prove', 'prover', 'such', 'valid', 'check', 'random', 'no', 'input',
            'am', 'do', 'go', 'he', 'me', 'my', 'ok', 'so', 'up', 'us', 'we', 'ip'
        }

    def update_settings(self, settings_dict):
        """Updates internal parameters based on GUI input."""
        if 'anchors' in settings_dict and settings_dict['anchors']:
            # Combine default anchors with user provided ones
            self.english_anchors.update(set(settings_dict['anchors']))
            
        self.section_id = settings_dict.get('section_id', self.section_id)
        self.subsection_id = settings_dict.get('subsection_id', self.subsection_id)
        self.include_title = settings_dict.get('include_title', self.include_title)

    def sanitize_text(self, text: str) -> str:
        for char, escaped in self.text_special_chars.items():
            text = text.replace(char, escaped)
        return text

    def transpile_math(self, text: str) -> str:
        """Converts raw string to LaTeX math, including subscript injection."""

        # 0. PRE-SANITIZATION
        text = text.replace('%', r'\%')
        text = text.replace('#', r'\#')
        text = text.replace('$', r'\$')
        text = text.replace('&', r'\&') 
        
        # 1. Handle Functions First
        text = re.sub(r'\bPr(?=[\[\(])', r'\\Pr', text)
        text = re.sub(r'\blog(?=[\[\(])', r'\\log', text)
        text = re.sub(r'\bsin(?=[\[\(])', r'\\sin', text)
        text = re.sub(r'\bcos(?=[\[\(])', r'\\cos', text)
        text = re.sub(r'\blim(?=[\[\(])', r'\\lim', text)

        # --- Handle Domain Specific Operators (Enck/Deck) ---
        text = re.sub(r'\b(Enc|Dec)k(?=\()', r'\\text{\1}_k', text)

        # 2. Map Unicode Symbols
        for char, command in self.math_map.items():
            text = text.replace(char, f" {command} ")
            
        # 3. Handle Square Roots
        if '√' in text:
            text = re.sub(r'√(\w+)', r'\\sqrt{\1}', text)
            text = re.sub(r'√', r'\\sqrt', text)

        # 4. Automatic Subscripting
        text = re.sub(r'(?<!\\)\b([a-zA-Z])(\d)\b', r'\1_\2', text)
        
        def two_letter_sub(match):
            word = match.group(0)
            if word in self.english_anchors or "Pr" in word:
                return word
            return f"{match.group(1)}_{match.group(2)}"

        text = re.sub(r'(?<!\\)\b([a-zA-Z])([a-zA-Z])\b', two_letter_sub, text)

        return re.sub(r'\s+', ' ', text).strip()

    def is_math_token(self, token: str) -> bool:
        clean = token.strip(".,;:?!")
        if not clean: return False
        
        if clean.lower() in self.english_anchors: return False

        # Function Call Detection (e.g., Fk(, Gen()
        if re.search(r'\b[A-Z][a-zA-Z0-9]*\(', clean):
            return True

        math_chars = set(self.math_map.keys()) | {'=', '<', '>', '+', '◦', '·', '±', '^', '_', '|', '\\', '/'}
        if any(c in clean for c in math_chars): return True

        if any(c.isdigit() for c in clean): return True

        if len(clean) == 1 and clean.isalpha():
            return clean not in ['a', 'A', 'I']
        
        if len(clean) == 2 and clean.isalpha():
            return True 
            
        if '(' in clean and ')' in clean: return True

        return False

    def process_inline_math(self, line: str) -> str:
        raw_tokens = line.split(' ')
        output_tokens = []
        
        for i in range(len(raw_tokens)):
            token = raw_tokens[i]
            
            # 1. Punctuation Stripping
            prefix_match = re.match(r'^([.,;:?!()\[\]"\']+)(.*)', token)
            prefix, body = prefix_match.groups() if prefix_match else ("", token)
            
            suffix_match = re.search(r'(.*?)([.,;:?!()\[\]"\']+)$', body)
            core, suffix = suffix_match.groups() if suffix_match else (body, "")
            
            # 2. Balance Check
            while core.count('(') > core.count(')') and suffix.startswith(')'):
                core += ')'
                suffix = suffix[1:]
            while core.count('[') > core.count(']') and suffix.startswith(']'):
                core += ']'
                suffix = suffix[1:]

            # 3. Logic Decision
            is_math = False
            
            if core in ['an', 'a']:
                next_is_math = False
                if i + 1 < len(raw_tokens):
                    next_token = raw_tokens[i+1].strip(".,;:?!")
                    if any(c in next_token for c in {'=', '+', '≤', '≥', '>', '<', '⊕', '≈'}):
                        next_is_math = True
                is_math = next_is_math
            else:
                is_math = self.is_math_token(core)

            # 4. Output Generation
            if is_math:
                tex_math = self.transpile_math(core)
                output_tokens.append(f"{self.sanitize_text(prefix)}${tex_math}${self.sanitize_text(suffix)}")
            else:
                output_tokens.append(self.sanitize_text(token))
                
        return " ".join(output_tokens)

    def format_list_content(self, raw_content: str) -> str:
        """Bold prefix before a colon if it appears within the first five words."""
        # Determine search boundary: end of the 5th word (if it exists)
        word_spans = list(re.finditer(r'\S+', raw_content))
        if not word_spans:
            return self.process_inline_math(raw_content)

        limit = word_spans[min(4, len(word_spans) - 1)].end()
        colon_pos = raw_content.find(':', 0, limit)
        if colon_pos == -1:
            return self.process_inline_math(raw_content)

        prefix = raw_content[:colon_pos].rstrip()
        suffix = raw_content[colon_pos:].lstrip()
        if not prefix:
            return self.process_inline_math(raw_content)

        prefix_tex = self.process_inline_math(prefix)
        suffix_tex = self.process_inline_math(suffix)

        # Avoid extra space when suffix starts with punctuation (e.g., ': definition')
        if suffix_tex and suffix_tex[0] in {':', ';', ',', '.', '!', '?'}:
            return f"\\textbf{{{prefix_tex}}}{suffix_tex}"
        return f"\\textbf{{{prefix_tex}}} {suffix_tex}"

    def is_math_line(self, line: str) -> bool:
        words = re.findall(r'\b[a-zA-Z]{2,}\b', line.lower())
        english_count = sum(1 for w in words if w in self.english_anchors)
        if english_count >= 2: return False
        strong_indicators = set(self.math_map.keys()) | {'=', '≤', '≥', '≠', '≈', '→', '<', '>'}
        if any(c in line for c in strong_indicators): return True
        return False

    def detect_structure(self, line: str) -> Tuple[str, str]:
        # Priority 1: User Custom Identifiers (Markdown Style)
        if line.startswith(self.subsection_id):
            return ('subsection', line.replace(self.subsection_id, '', 1).strip())
        if line.startswith(self.section_id):
            return ('section', line.replace(self.section_id, '', 1).strip())

        if self.is_math_line(line): return ('math_display', line)
        
        # Priority 2: Standard Numbering (Academic Style)
        header_match = re.match(r'^(\d+\.\d+(?:\.\d+)*)\s+(.*)', line)
        # The \.? allows for an optional trailing dot (e.g., matches "1.1." and "1.1")
        header_match = re.match(r'^(\d+(?:\.\d+)+)\.?\s+(.*)', line)
        if header_match:
            numbering, title = header_match.group(1), header_match.group(2).strip()
            if numbering.endswith('.0'): return ('section', title)
            elif numbering.count('.') == 1: return ('subsection', title)
            return ('subsubsection', title)
            
        if re.match(r'^\d+\.\s+', line): return ('enumerate', re.sub(r'^\d+\.\s+', '', line))
        if line.startswith('- ') or line.startswith('* '): return ('itemize', line[2:].strip())
        if line: return ('paragraph', line)
        return ('empty', '')

    def generate_table_block(self, rows: List[str]) -> str:
        if not rows: return ""
        
        header_cols = rows[0].split('\t')
        num_cols = len(header_cols)
        col_spec = "X" * num_cols
        
        safe_headers = [f"\\textbf{{{self.process_inline_math(h.strip())}}}" for h in header_cols]
        header_row = " & ".join(safe_headers) + r' \\'

        latex_block = []
        latex_block.append(fr'\begin{{xltabular}}{{\textwidth}}{{@{{}}{col_spec}@{{}}}}')
        latex_block.append(r'\caption{Auto-generated table} \\')
        latex_block.append(r'\toprule')
        latex_block.append(header_row)
        latex_block.append(r'\midrule')
        latex_block.append(r'\endfirsthead')
        latex_block.append(r'\caption[]{Auto-generated table (continued)} \\')
        latex_block.append(r'\toprule')
        latex_block.append(header_row)
        latex_block.append(r'\midrule')
        latex_block.append(r'\endhead')
        latex_block.append(r'\bottomrule')
        latex_block.append(r'\endfoot')

        for row in rows[1:]:
            cols = row.split('\t')
            safe_cols = [self.process_inline_math(c.strip()) for c in cols]
            latex_block.append(" & ".join(safe_cols) + r' \\')
            latex_block.append(r'\addlinespace')
            
        latex_block.append(r'\end{xltabular}')
        return '\n'.join(latex_block)

    def transpile(self, raw_input: str) -> str:
        lines = raw_input.strip().split('\n')
        
        # Extract Title (First Line)
        title_text = lines.pop(0) if lines else "Untitled Document"
        
        latex_output = []
        latex_output.append(r'\documentclass{article}')
        latex_output.append(r'\usepackage{amsmath, amssymb}') 
        latex_output.append(r'\usepackage[utf8]{inputenc}')
        latex_output.append(r'\usepackage{xltabular}')
        latex_output.append(r'\usepackage{booktabs}')
        latex_output.append(r'\setlength{\parskip}{1em}')
        
        latex_output.append(fr'\title{{{self.process_inline_math(title_text)}}}')
        latex_output.append(r'\author{}')
        latex_output.append(r'\date{\today}')
        
        latex_output.append(r'\begin{document}')
        
        # Dynamic Title Toggle
        if self.include_title:
            latex_output.append(r'\maketitle')
        
        table_buffer = []
        current_list_type: Optional[str] = None
        
        for line in lines:
            line = line.strip()

            if '\t' in line:
                table_buffer.append(line)
                continue
            elif table_buffer:
                latex_output.append(self.generate_table_block(table_buffer))
                table_buffer = []

            structure, raw_content = self.detect_structure(line)
            
            if structure in ['itemize', 'enumerate']:
                safe_content = self.format_list_content(raw_content)
                if current_list_type and current_list_type != structure:
                    latex_output.append(f'\\end{{{current_list_type}}}')
                    current_list_type = None
                if not current_list_type:
                    latex_output.append(f'\\begin{{{structure}}}')
                    current_list_type = structure
                latex_output.append(f'    \\item {safe_content}')
                continue
            elif current_list_type:
                latex_output.append(f'\\end{{{current_list_type}}}')
                current_list_type = None

            if structure == 'math_display':
                latex_output.append(f'\\[ {self.transpile_math(raw_content)} \\]')
            elif structure == 'paragraph':
                latex_output.append(f'{self.process_inline_math(raw_content)}\n\n')
            elif structure.startswith('section') or structure.startswith('sub'):
                safe_content = self.process_inline_math(raw_content) 
                latex_output.append(f'\\{structure}{{{safe_content}}}')

        if current_list_type: latex_output.append(f'\\end{{{current_list_type}}}')
        if table_buffer: latex_output.append(self.generate_table_block(table_buffer))
            
        latex_output.append(r'\end{document}')
        return '\n'.join(latex_output)
