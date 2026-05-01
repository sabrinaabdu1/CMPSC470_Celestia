"""
Celestia Language Tokenizer
Analyzes Celestia source code and produces a token report.
"""

import sys
import re
from collections import defaultdict


RESERVED_WORDS = {
    'num', 'string', 'boolean', 'if', 'else', 'while',
    'print', 'return', 'true', 'false', 'and', 'or', 'not', 'null'
}

DATA_TYPES = {'num', 'string', 'boolean'}

MULTI_CHAR_OPERATORS = {'==', '!=', '>=', '<='}
SINGLE_CHAR_OPERATORS = set('+-*/><!=')


# ── Tokenizer ─────────────────────────────────────────────────────────────────

def tokenize(source: str) -> list[dict]:
    """
    Tokenize a Celestia source string (with comments already stripped).
    Returns a list of token dicts with keys: type, value.
    """
    tokens = []
    i = 0
    n = len(source)

    while i < n:
        # Skip whitespace
        if source[i].isspace():
            i += 1
            continue

        # String literal
        if source[i] == '"':
            j = i + 1
            while j < n and source[j] != '"':
                j += 1
            value = source[i:j + 1]
            tokens.append({'type': 'string', 'value': value})
            i = j + 1
            continue

        # Number literal
        if source[i].isdigit():
            j = i
            while j < n and (source[j].isdigit() or source[j] == '.'):
                j += 1
            tokens.append({'type': 'number', 'value': source[i:j]})
            i = j
            continue

        # Two-character operators
        if i + 1 < n and source[i:i+2] in MULTI_CHAR_OPERATORS:
            tokens.append({'type': 'operator', 'value': source[i:i+2]})
            i += 2
            continue

        # Single-character operators
        if source[i] in SINGLE_CHAR_OPERATORS:
            tokens.append({'type': 'operator', 'value': source[i]})
            i += 1
            continue

        # Identifiers, keywords, booleans
        if source[i].isalpha() or source[i] == '_':
            j = i
            while j < n and (source[j].isalnum() or source[j] == '_'):
                j += 1
            word = source[i:j]
            word_lower = word.lower()
            if word_lower in ('true', 'false'):
                tokens.append({'type': 'boolean', 'value': word})
            elif word_lower in RESERVED_WORDS:
                tokens.append({'type': 'keyword', 'value': word})
            else:
                tokens.append({'type': 'identifier', 'value': word})
            i = j
            continue

        # Skip punctuation (parens, braces, commas, semicolons, etc.)
        i += 1

    return tokens


# ── Comment stripper & line counter ───────────────────────────────────────────

def strip_comments_and_count(source: str) -> tuple[str, int]:
    """
    Remove // line comments and /* */ block comments from source.
    Returns (cleaned_source, non_comment_line_count).
    """
    lines = source.split('\n')
    cleaned_lines = []
    in_block_comment = False
    code_line_count = 0

    for line in lines:
        result = []
        i = 0
        while i < len(line):
            if in_block_comment:
                if line[i] == '*' and i + 1 < len(line) and line[i+1] == '/':
                    in_block_comment = False
                    i += 2
                else:
                    i += 1
            else:
                if line[i] == '/' and i + 1 < len(line) and line[i+1] == '*':
                    in_block_comment = True
                    i += 2
                elif line[i] == '/' and i + 1 < len(line) and line[i+1] == '/':
                    break  # rest of line is a comment
                else:
                    result.append(line[i])
                    i += 1

        cleaned = ''.join(result).strip()
        cleaned_lines.append(cleaned)
        if cleaned:
            code_line_count += 1

    return '\n'.join(cleaned_lines), code_line_count


# ── Analyzer ──────────────────────────────────────────────────────────────────

def analyze(source: str) -> dict:
    """
    Full analysis pipeline: strip comments, tokenize, classify, and report.
    """
    cleaned, line_count = strip_comments_and_count(source)
    tokens = tokenize(cleaned)

    num_literals   = []
    str_literals   = []
    bool_literals  = []
    operators      = []
    variables      = []
    reserved_words = []
    data_types     = []

    declared_vars  = defaultdict(int)   # name -> declaration count
    seen_operators = set()
    seen_reserved  = set()
    seen_types     = set()
    seen_vars      = set()

    for idx, tok in enumerate(tokens):
        t, v = tok['type'], tok['value']

        if t == 'number':
            num_literals.append(v)

        elif t == 'string':
            str_literals.append(v)

        elif t == 'boolean':
            bool_literals.append(v)

        elif t == 'operator':
            if v not in seen_operators:
                operators.append(v)
                seen_operators.add(v)

        elif t == 'keyword':
            vl = v.lower()
            if vl not in seen_reserved:
                reserved_words.append(v)
                seen_reserved.add(vl)
            if vl in DATA_TYPES and vl not in seen_types:
                data_types.append(v)
                seen_types.add(vl)
            # Variable declaration: type keyword followed by an identifier
            if vl in DATA_TYPES:
                ni = idx + 1
                while ni < len(tokens) and tokens[ni]['value'] in ('(', ')'):
                    ni += 1
                if ni < len(tokens) and tokens[ni]['type'] == 'identifier':
                    declared_vars[tokens[ni]['value']] += 1

        elif t == 'identifier':
            if v not in seen_vars and v.lower() not in RESERVED_WORDS:
                variables.append(v)
                seen_vars.add(v)

    duplicates = {name: count for name, count in declared_vars.items() if count > 1}

    return {
        'line_count':    line_count,
        'num_literals':  num_literals,
        'str_literals':  str_literals,
        'bool_literals': bool_literals,
        'all_literals':  num_literals + str_literals + bool_literals,
        'operators':     operators,
        'variables':     variables,
        'reserved_words': reserved_words,
        'data_types':    data_types,
        'declared_vars': dict(declared_vars),
        'duplicates':    duplicates,
    }


# ── Report printer ────────────────────────────────────────────────────────────

def print_report(result: dict) -> None:
    W = 60
    div  = '─' * W
    hdiv = '═' * W

    def header(title):
        print(f'\n╔{hdiv}╗')
        print(f'║  {title:<{W-2}}║')
        print(f'╚{hdiv}╝')

    def section(title, count, items, note=''):
        print(f'\n┌{div}┐')
        print(f'│  {title} ({count}){" " * (W - len(title) - len(str(count)) - 5)}│')
        print(f'├{div}┤')
        if items:
            for item in items:
                print(f'│    {item:<{W-4}}│')
        else:
            print(f'│    {"(none)":<{W-4}}│')
        if note:
            print(f'├{div}┤')
            for line in note.splitlines():
                print(f'│  {line:<{W-2}}│')
        print(f'└{div}┘')

    header('Celestia Lexer Report')

    # Summary metrics
    print(f'\n  Lines processed (excl. comments) : {result["line_count"]}')
    print(f'  Total literals                   : {len(result["all_literals"])}')
    print(f'  Distinct operators               : {len(result["operators"])}')
    print(f'  Variables                        : {len(result["variables"])}')
    print(f'  Reserved words used              : {len(result["reserved_words"])}')
    print(f'  Data types declared              : {len(result["data_types"])}')

    # 1. Literals
    lit_items = []
    if result['num_literals']:
        lit_items.append(f'Number  ({len(result["num_literals"])}) : {", ".join(result["num_literals"])}')
    if result['str_literals']:
        lit_items.append(f'String  ({len(result["str_literals"])}) : {", ".join(result["str_literals"])}')
    if result['bool_literals']:
        lit_items.append(f'Boolean ({len(result["bool_literals"])}) : {", ".join(result["bool_literals"])}')
    section('1. Literals', len(result['all_literals']), lit_items)

    # 2. Operators
    section('2. Operators', len(result['operators']),
            [f'{op}' for op in result['operators']])

    # 3. Variables (with duplicate note)
    dup_note = ''
    if result['duplicates']:
        lines = ['⚠  Duplicate declarations detected:']
        for name, count in result['duplicates'].items():
            lines.append(f'   {name}  declared {count} times')
        dup_note = '\n'.join(lines)
    section('3. Variables', len(result['variables']),
            result['variables'], note=dup_note)

    # 4. Reserved words
    section('4. Reserved words', len(result['reserved_words']),
            result['reserved_words'])

    # 5. Data types
    section('5. Data types declared', len(result['data_types']),
            result['data_types'])

    print()


# ── Sample programs ───────────────────────────────────────────────────────────
SAMPLES = {
    '1': {
        'title': 'Grade Checker',
        'code': """\
// Grade Checker — determines pass/fail based on a score
num score = 85
num passing = 60
Boolean passed = false
String result = "unknown"

if (score >= passing) {
    passed = true
    result = "Pass"
}
if (score < passing) {
    result = "Fail"
}

print(result)
return passed
"""
    },
    '2': {
        'title': 'Countdown Loop',
        'code': """\
/* Countdown program
   counts down from a start value to zero */
num start = 10
num step = 1
num current = start
Boolean running = true

while (current > 0) {
    print("Count:")
    current = current - step
}

// Done
num current = 0
print("Liftoff!")
return current
"""
    },
    '3': {
        'title': 'String Greeter',
        'code': """\
// Greeter — builds a personalised welcome message
String firstName = "Alice"
String lastName  = "Smith"
String greeting  = "Hello"
num visitCount   = 3
Boolean returning = true

if (returning == true) {
    greeting = "Welcome back"
}

print(greeting + " " + firstName + " " + lastName)

/* Track visit number */
num visitCount = visitCount + 1
print("Visit number:")
print(visitCount)
return visitCount
"""
    },
}


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print('\n  Celestia Lexer')
    print('  ─────────────────────────────────────────')
    print('  1) Grade Checker')
    print('  2) Countdown Loop')
    print('  3) String Greeter')
    print('  4) Enter your own code')
    print()

    choice = input('  Select an option (1-4): ').strip()

    if choice in SAMPLES:
        sample = SAMPLES[choice]
        print(f'\n  Running sample: {sample["title"]}\n')
        print('  ── Source code ───────────────────────────')
        for line in sample['code'].splitlines():
            print(f'  {line}')
        print('  ──────────────────────────────────────────')
        source = sample['code']
    elif choice == '4':
        print('\nPaste your Celestia code below (Ctrl+D / Ctrl+Z to finish):')
        source = sys.stdin.read()
    else:
        print('Invalid choice. Exiting.')
        sys.exit(1)

    result = analyze(source)
    print_report(result)


if __name__ == '__main__':
    main()
