"""
Symbol Table and Type System for the Pseudocode to C Compiler.
Handles explicit data type declarations, type inference, array definitions,
scope management, and type conflict detection.
"""

from errors import TypeError, SemanticError

TYPE_MAP = {
    "INTEGER": "int",
    "INT": "int",
    "FLOAT": "float",
    "REAL": "double",
    "DOUBLE": "double",
    "CHARACTER": "char",
    "CHAR": "char",
    "STRING": "string",  # Converted to char array in C generator
    "BOOLEAN": "bool",
    "BOOL": "bool",
    "LONG": "long",
    "SHORT": "short",
    "VOID": "void"
}

# C Type to input format specifier
SCANF_FORMATS = {
    "int": "%d",
    "float": "%f",
    "double": "%lf",
    "char": " %c",
    "string": "%99s",
    "bool": "%d",
    "long": "%ld",
    "short": "%hd"
}

# C Type to output format specifier
PRINTF_FORMATS = {
    "int": "%d",
    "float": "%f",
    "double": "%lf",
    "char": "%c",
    "string": "%s",
    "bool": "%s",  # Handled via ternary: var ? "true" : "false" or %d
    "long": "%ld",
    "short": "%hd"
}


class Symbol:
    def __init__(self, name, c_type="int", pseudo_type="INTEGER",
                 is_explicit=False, is_array=False, array_size=None,
                 line=None, inferred_from=None):
        self.name = name
        self.c_type = c_type
        self.pseudo_type = pseudo_type
        self.is_explicit = is_explicit
        self.is_array = is_array
        self.array_size = array_size
        self.line = line
        self.inferred_from = inferred_from

    def to_dict(self):
        return {
            "name": self.name,
            "c_type": self.c_type,
            "pseudo_type": self.pseudo_type,
            "is_explicit": self.is_explicit,
            "is_array": self.is_array,
            "array_size": self.array_size,
            "line": self.line,
            "inferred_from": self.inferred_from
        }


class FunctionSymbol:
    def __init__(self, name, return_type="void", params=None, line=None):
        self.name = name
        self.return_type = return_type
        self.params = params or []  # List of (param_name, c_type, pseudo_type)
        self.line = line

    def to_dict(self):
        return {
            "name": self.name,
            "return_type": self.return_type,
            "params": [
                {"name": p[0], "c_type": p[1], "pseudo_type": p[2]}
                for p in self.params
            ],
            "line": self.line
        }


class SymbolTable:
    def __init__(self, parent=None, scope_name="main"):
        self.parent = parent
        self.scope_name = scope_name
        self.symbols = {}
        self.functions = {}
        self.warnings = []

    def declare(self, name, pseudo_type="INTEGER", is_explicit=True,
                is_array=False, array_size=None, line=None):
        """Explicitly declare a variable with a known pseudocode type."""
        norm_type = pseudo_type.upper()
        if norm_type not in TYPE_MAP:
            raise TypeError(
                f"Unknown data type '{pseudo_type}' for variable '{name}'.",
                line=line,
                suggestion=f"Supported types: {', '.join(sorted(set(TYPE_MAP.keys())))}"
            )

        c_type = TYPE_MAP[norm_type]

        if name in self.symbols:
            existing = self.symbols[name]
            if existing.is_explicit:
                if existing.c_type != c_type or existing.is_array != is_array:
                    raise TypeError(
                        f"Variable '{name}' already declared as '{existing.c_type}'. "
                        f"Cannot redeclare as '{c_type}'.",
                        line=line,
                        suggestion="Check variable name or remove duplicate declaration."
                    )
                return existing
            else:
                # Upgrading inferred symbol to explicit declaration
                existing.c_type = c_type
                existing.pseudo_type = norm_type
                existing.is_explicit = True
                existing.is_array = is_array
                existing.array_size = array_size
                existing.line = line
                return existing

        symbol = Symbol(
            name=name,
            c_type=c_type,
            pseudo_type=norm_type,
            is_explicit=is_explicit,
            is_array=is_array,
            array_size=array_size,
            line=line
        )
        self.symbols[name] = symbol
        return symbol

    def infer(self, name, inferred_c_type, line=None, reason=None):
        """Infer variable type from usage or expression if not explicitly declared."""
        if name in self.symbols:
            existing = self.symbols[name]
            if existing.is_explicit:
                # Explicit declaration takes precedence! Check compatibility
                if not self.are_types_compatible(existing.c_type, inferred_c_type):
                    self.warnings.append(
                        f"Line {line}: Variable '{name}' explicitly declared as '{existing.c_type}', "
                        f"but assigned a '{inferred_c_type}' value. Value may be truncated or converted."
                    )
                return existing
            else:
                # Inferred before: check if compatible or upgrade (e.g. int -> float)
                if existing.c_type == inferred_c_type:
                    return existing
                elif existing.c_type == "int" and inferred_c_type in ["float", "double"]:
                    # Upgrade int to floating point
                    existing.c_type = inferred_c_type
                    existing.pseudo_type = "FLOAT" if inferred_c_type == "float" else "REAL"
                    existing.inferred_from = reason
                    return existing
                elif self.are_types_compatible(existing.c_type, inferred_c_type):
                    return existing
                else:
                    raise TypeError(
                        f"Conflicting types inferred for variable '{name}': previously '{existing.c_type}', "
                        f"now assigned '{inferred_c_type}'.",
                        line=line,
                        suggestion=f"Explicitly declare variable type with 'DECLARE {name}: {inferred_c_type.upper()}'"
                    )

        # Look in parent scope
        if self.parent and self.parent.exists(name):
            return self.parent.infer(name, inferred_c_type, line, reason)

        # New inferred symbol
        pseudo_name = "INTEGER"
        for p, c in TYPE_MAP.items():
            if c == inferred_c_type:
                pseudo_name = p
                break

        symbol = Symbol(
            name=name,
            c_type=inferred_c_type,
            pseudo_type=pseudo_name,
            is_explicit=False,
            line=line,
            inferred_from=reason
        )
        self.symbols[name] = symbol
        return symbol

    def are_types_compatible(self, t1, t2):
        """Check if two C types can be safely converted or assigned."""
        if t1 == t2:
            return True
        numeric = {"int", "float", "double", "long", "short", "bool"}
        if t1 in numeric and t2 in numeric:
            return True
        return False

    def declare_function(self, name, return_type="void", params=None, line=None):
        """Register a function signature."""
        norm_ret = return_type.upper()
        c_ret = TYPE_MAP.get(norm_ret, "void")
        c_params = []
        for p_name, p_type in (params or []):
            p_norm = p_type.upper() if p_type else "INTEGER"
            p_c = TYPE_MAP.get(p_norm, "int")
            c_params.append((p_name, p_c, p_norm))

        func_sym = FunctionSymbol(name, c_ret, c_params, line)
        self.functions[name] = func_sym
        return func_sym

    def lookup(self, name):
        """Look up symbol in this scope or parent scopes."""
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_function(self, name):
        """Look up function signature."""
        if name in self.functions:
            return self.functions[name]
        if self.parent:
            return self.parent.lookup_function(name)
        return None

    def exists(self, name):
        return self.lookup(name) is not None

    def get_type(self, name):
        sym = self.lookup(name)
        return sym.c_type if sym else None

    def get_all(self):
        return {name: sym.c_type for name, sym in self.symbols.items()}

    def get_all_symbols(self):
        return self.symbols