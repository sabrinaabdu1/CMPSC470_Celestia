# Celestia Language Translator — implemented in Python
# Data structure: dict (Python's built-in hash table)
#
# Supported syntax:
#   Declaration:  num x = 10
#                 String name = "Alice"
#                 Boolean flag = true
#   Update:       x = 25        (no type keyword)
#   Comment:      // single-line comment

import re
import copy


class SymbolTable:
    """
    Hash-table-backed symbol table for the Celestia language.
    Internally uses a Python dict (hash map) keyed by variable name.
    Each entry stores: name (str), type (str), value (float | str | bool)
    """

    VALID_TYPES = {"num", "String", "Boolean"}

    def __init__(self):
        self._table: dict = {}   # The core hash table: name -> entry dict

    # ------------------------------------------------------------------ #
    # Public Interface                                                   #
    # ------------------------------------------------------------------ #

    def declare(self, name: str, type_: str, raw_val: str) -> dict:
        """Declare a new variable. Returns {'ok': bool, 'msg': str}."""
        if name in self._table:
            return {"ok": False, "msg": f"'{name}' is already declared"}
        result = self._parse(type_, raw_val)
        if "err" in result:
            return {"ok": False, "msg": result["err"]}
        self._table[name] = {"name": name, "type": type_, "value": result["val"]}
        return {"ok": True}

    def update(self, name: str, raw_val: str) -> dict:
        """Update an existing variable. Type must match its declaration."""
        if name not in self._table:
            return {
                "ok": False,
                "msg": f"'{name}' is undeclared — declare with num/String/Boolean first",
            }
        entry = self._table[name]
        result = self._parse(entry["type"], raw_val)
        if "err" in result:
            return {
                "ok": False,
                "msg": (
                    f"TypeError: cannot assign '{raw_val}' to "
                    f"{entry['type']} variable '{name}' — {result['err']}"
                ),
            }
        old_val = entry["value"]
        entry["value"] = result["val"]
        return {"ok": True, "old": old_val, "new": result["val"]}

    def snapshot(self) -> dict:
        """Return a deep copy of the current table state."""
        return copy.deepcopy(self._table)

    def print_table(self, label: str = "Symbol Table") -> None:
        """Print all entries to stdout in a formatted table."""
        print(f"\n{'─' * 50}")
        print(f"  {label}")
        print(f"{'─' * 50}")
        if not self._table:
            print("  (empty)")
        else:
            print(f"  {'Name':<16} {'Type':<10} {'Value'}")
            print(f"  {'─'*14}  {'─'*8}  {'─'*14}")
            for entry in self._table.values():
                val = self._fmt(entry["value"], entry["type"])
                print(f"  {entry['name']:<16} {entry['type']:<10} {val}")
        print(f"{'─' * 50}\n")

    # ------------------------------------------------------------------ #
    # Private Helpers                                                    #
    # ------------------------------------------------------------------ #

    def _parse(self, type_: str, raw: str) -> dict:
        """Validate and convert a raw token to the appropriate Python type."""
        raw = raw.strip()

        if type_ == "num":
            if not re.fullmatch(r"-?\d+(\.\d+)?", raw):
                return {"err": f"'{raw}' is not a valid num"}
            return {"val": float(raw)}

        if type_ == "String":
            if not (raw.startswith('"') and raw.endswith('"') and len(raw) >= 2):
                return {"err": "String value must be enclosed in double quotes"}
            return {"val": raw[1:-1]}

        if type_ == "Boolean":
            if raw not in ("true", "false"):
                return {"err": "Boolean value must be true or false"}
            return {"val": raw == "true"}

        return {"err": f"Unknown type '{type_}'"}

    @staticmethod
    def _fmt(value, type_: str) -> str:
        """Format a stored value for display."""
        if type_ == "String":
            return f'"{value}"'
        if type_ == "Boolean":
            return "true" if value else "false"
        # num: show as int if whole number, else float
        return str(int(value)) if isinstance(value, float) and value == int(value) else str(value)


# ======================================================================= #
# Interpreter / Driver                                                    #
# ======================================================================= #

DECL_RE = re.compile(
    r"^(num|String|Boolean)\s+([a-zA-Z][a-zA-Z0-9]*)\s*=\s*(.+)$"
)
UPDATE_RE = re.compile(r"^([a-zA-Z][a-zA-Z0-9]*)\s*=\s*(.+)$")


def run(source: str) -> None:
    """
    Parse and execute a Celestia source string.
    Prints the symbol table before and after the update phase.
    """
    lines = source.splitlines()
    sym = SymbolTable()
    decls = []
    updates = []
    errors = []

    # ── Pass 1: classify lines ──────────────────────────────────────── #
    for i, line in enumerate(lines, start=1):
        # Strip single-line comments
        comment_pos = line.find("//")
        if comment_pos != -1:
            line = line[:comment_pos]
        line = line.strip()
        if not line:
            continue

        d_match = DECL_RE.match(line)
        u_match = UPDATE_RE.match(line)

        if d_match:
            decls.append((i, d_match.group(1), d_match.group(2), d_match.group(3).strip()))
        elif u_match:
            updates.append((i, u_match.group(1), u_match.group(2).strip()))
        else:
            errors.append(f"Line {i}: SyntaxError — '{line}'")

    for err in errors:
        print(err)

    # ── Phase 1: Declarations ────────────────────────────────────────── #
    print("\n━━ Declaration phase ━━")
    for line_no, type_, name, raw_val in decls:
        result = sym.declare(name, type_, raw_val)
        if result["ok"]:
            entry = sym._table[name]
            print(f"  Line {line_no}: declared  {type_} {name} = {sym._fmt(entry['value'], type_)}")
        else:
            print(f"  Line {line_no}: ERROR — {result['msg']}")

    # Capture state BEFORE updates
    snap_before = sym.snapshot()
    sym.print_table("Symbol Table — BEFORE updates")

    # ── Phase 2: Updates ─────────────────────────────────────────────── #
    if updates:
        print("━━ Update phase ━━")
        for line_no, name, raw_val in updates:
            result = sym.update(name, raw_val)
            if result["ok"]:
                entry = sym._table[name]
                old_fmt = sym._fmt(result["old"], entry["type"])
                new_fmt = sym._fmt(result["new"], entry["type"])
                print(f"  Line {line_no}: updated   {name}  {old_fmt} → {new_fmt}")
            else:
                print(f"  Line {line_no}: ERROR — {result['msg']}")
    else:
        print("(no update statements found)")

    # Capture state AFTER updates
    sym.print_table("Symbol Table — AFTER updates")


# ======================================================================= #
# Entry Point — runs built-in test suites when executed directly          #
# ======================================================================= #

if __name__ == "__main__":

    TEST_BASIC = """
// Test Suite 1 — Basic Declarations
num age = 17
num gpa = 3.87
String name = "Alice"
String school = "Westview High"
Boolean enrolled = true
Boolean graduated = false
num credits = 120
"""

    TEST_UPDATE = """
// Test Suite 2 — Declarations then Updates
num score = 50
num temperature = 98.6
String city = "Boston"
Boolean active = false
num level = 1

// Updates:
score = 95
temperature = 101.3
city = "New York"
active = true
level = 5
"""

    TEST_ERRORS = """
// Test Suite 3 — Type Errors
num x = 10
String greeting = "Hello"
Boolean flag = true

// Invalid updates:
x = "not a number"
greeting = 42
flag = yes
// Undeclared:
z = 100
"""

    print("=" * 50)
    print("CELESTIA INTERPRETER — TEST SUITE 1")
    print("=" * 50)
    run(TEST_BASIC)

    print("=" * 50)
    print("CELESTIA INTERPRETER — TEST SUITE 2")
    print("=" * 50)
    run(TEST_UPDATE)

    print("=" * 50)
    print("CELESTIA INTERPRETER — TEST SUITE 3 (errors)")
    print("=" * 50)
    run(TEST_ERRORS)
