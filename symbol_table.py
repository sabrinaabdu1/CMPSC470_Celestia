"""
Celestia Symbol Table — Standalone Demo
========================================
This file demonstrates the SymbolTable class used by the Celestia compiler's
semantic analysis stage. It can be run independently without the full compiler.

Usage:
    python3 symbol_table.py

The SymbolTable maps variable names to their declared Celestia types:
    num, String, or Boolean

It is built during semantic analysis as VarDecl nodes are visited, and
consulted on every Assignment and Variable reference to enforce type safety.
"""


# ============================================================
# Symbol Table
# ============================================================

class SymbolTable:
    """
    Stores variable names and their declared types for the semantic analysis stage.

    Each entry maps an identifier (str) to its Celestia type: 'num', 'String', or 'Boolean'.
    The table is built incrementally as VarDecl nodes are visited and is consulted
    for every Assignment and Variable reference to enforce type safety.
    """

    def __init__(self):
        self._table: dict[str, str] = {}

    def declare(self, name: str, var_type: str) -> None:
        """Register a new variable. Raises KeyError if already declared."""
        if name in self._table:
            raise KeyError(f"Variable '{name}' is already declared")
        self._table[name] = var_type

    def lookup(self, name: str) -> str:
        """Return the type of a declared variable. Raises KeyError if undeclared."""
        if name not in self._table:
            raise KeyError(f"Variable '{name}' is undeclared")
        return self._table[name]

    def contains(self, name: str) -> bool:
        """Return True if the variable has been declared."""
        return name in self._table

    def all_entries(self) -> dict[str, str]:
        """Return a copy of the full symbol table (name -> type)."""
        return dict(self._table)

    def display(self) -> None:
        """Pretty-print the symbol table contents."""
        border = "-" * 36
        print(border)
        print(f"  {'Variable':<20} {'Type'}")
        print(border)
        if self._table:
            for name, vtype in self._table.items():
                print(f"  {name:<20} {vtype}")
        else:
            print(f"  {'(empty)':<20}")
        print(border)

    def __repr__(self) -> str:
        rows = "\n".join(f"  {name:<20} {vtype}" for name, vtype in self._table.items())
        return f"SymbolTable({{\n{rows}\n}})" if rows else "SymbolTable({})"


# ============================================================
# Demo
# ============================================================

def separator(title: str) -> None:
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def run_demo() -> None:

    separator("1. Declaring variables")
    table = SymbolTable()

    declarations = [
        ("score",    "num"),
        ("name",     "String"),
        ("enrolled", "Boolean"),
        ("counter",  "num"),
        ("greeting", "String"),
    ]

    for var_name, var_type in declarations:
        table.declare(var_name, var_type)
        print(f"  declared: {var_type} {var_name}")

    print()
    table.display()


    separator("2. Looking up variable types")
    for var_name, _ in declarations:
        resolved = table.lookup(var_name)
        print(f"  lookup('{var_name}') -> {resolved}")


    separator("3. Checking if variables exist (contains)")
    for test in ["score", "total", "name", "x"]:
        found = table.contains(test)
        print(f"  contains('{test}') -> {found}")


    separator("4. Simulating type-safe assignment checks")
    assignments = [
        ("score",    "num",     True),   # valid
        ("name",     "String",  True),   # valid
        ("score",    "String",  False),  # type mismatch
        ("enrolled", "num",     False),  # type mismatch
        ("unknown",  "num",     False),  # undeclared
    ]

    for var_name, assigned_type, should_pass in assignments:
        try:
            if not table.contains(var_name):
                raise KeyError(f"Variable '{var_name}' is undeclared")
            declared_type = table.lookup(var_name)
            if declared_type != assigned_type:
                raise TypeError(
                    f"Cannot assign {assigned_type} to {declared_type} variable '{var_name}'"
                )
            status = "OK    "
            msg = f"{var_name} = <{assigned_type} value>"
        except (KeyError, TypeError) as e:
            status = "ERROR "
            msg = str(e)

        marker = "✓" if should_pass else "✗"
        print(f"  [{status}] {marker}  {msg}")


    separator("5. Duplicate declaration check")
    try:
        table.declare("score", "num")
        print("  ERROR: should have raised KeyError")
    except KeyError as e:
        print(f"  Caught expected error: {e}")


    separator("6. Final symbol table state")
    table.display()

    separator("7. all_entries() snapshot")
    snapshot = table.all_entries()
    for k, v in snapshot.items():
        print(f"  '{k}': '{v}'")

    print()
    print("Demo complete.")


if __name__ == "__main__":
    run_demo()