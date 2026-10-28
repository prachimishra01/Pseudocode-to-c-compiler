"""
Code Generator for the Pseudocode to C Compiler.
Transforms the parsed AST and symbol tables into clean, standard C code
with proper headers, variable declarations, format specifiers, and explanations.
"""

from symbol_table import SCANF_FORMATS, PRINTF_FORMATS

class CodeGenerator:
    def __init__(self):
        self.headers = set()
        self.explanation_steps = []
        self.temp_var_count = 0

    def generate(self, tree):
        """
        Generate complete C program from AST tree.
        Returns a dictionary with:
          - 'c_code': string
          - 'explanation': list of explanations / notes
          - 'headers': list of headers included
        """
        self.headers = {"<stdio.h>"}
        self.explanation_steps = []
        self.temp_var_count = 0

        functions_code = []
        main_code = []

        # Analyze symbols to determine required headers
        symbols = tree.get("symbols", {})
        symbol_table = tree.get("symbol_table")

        for name, sym in symbols.items():
            if sym.c_type == "bool":
                self.headers.add("<stdbool.h>")
            elif sym.c_type == "string":
                self.headers.add("<string.h>")

        # Check functions
        from symbol_table import TYPE_MAP
        for func in tree.get("functions", []):
            if func.get("return_type") == "bool":
                self.headers.add("<stdbool.h>")
            for _, p_type in func.get("params", []):
                p_c = TYPE_MAP.get(p_type.upper(), "int")
                if p_c == "bool":
                    self.headers.add("<stdbool.h>")
                elif p_c == "string":
                    self.headers.add("<string.h>")

            f_code = self.generate_function(func)
            functions_code.append(f_code)

        # Main function variable declarations
        main_var_decls = self.generate_declarations(symbols, indent=1)

        # Main statements
        main_stmts_code = []
        for stmt in tree.get("statements", []):
            lines = self.generate_statement(stmt, indent=1, scope=symbol_table)
            main_stmts_code.extend(lines)

        # Assemble full C code
        full_lines = []
        sorted_headers = sorted(list(self.headers))
        for h in sorted_headers:
            full_lines.append(f"#include {h}")

        full_lines.append("")

        # Add function prototypes if any
        if functions_code:
            for f in tree.get("functions", []):
                proto = self.generate_function_prototype(f)
                full_lines.append(f"{proto};")
            full_lines.append("")

            # Add function implementations
            for f_str in functions_code:
                full_lines.append(f_str)
                full_lines.append("")

        # Main function
        full_lines.append("int main(void)")
        full_lines.append("{")

        if main_var_decls:
            full_lines.extend(main_var_decls)
            full_lines.append("")

        if main_stmts_code:
            full_lines.extend(main_stmts_code)
        else:
            full_lines.append("    // (Empty program body)")

        full_lines.append("")
        full_lines.append("    return 0;")
        full_lines.append("}")

        c_code_str = "\n".join(full_lines)
        self.build_explanation(tree, sorted_headers)

        return c_code_str

    def generate_with_metadata(self, tree):
        """Returns code along with structured explanation and metadata."""
        code = self.generate(tree)
        return {
            "c_code": code,
            "explanation": self.explanation_steps,
            "headers": sorted(list(self.headers)),
            "warnings": tree.get("warnings", [])
        }

    def generate_declarations(self, symbols, indent=1):
        """Generate formatted C declarations grouped by type."""
        space = "    " * indent
        lines = []

        # Group by c_type
        by_type = {}
        arrays = []

        for name, sym in symbols.items():
            if sym.is_array:
                arrays.append(sym)
            else:
                c_t = sym.c_type
                if c_t not in by_type:
                    by_type[c_t] = []
                by_type[c_t].append(name)

        # Standard scalar types
        type_order = ["int", "long", "short", "float", "double", "char", "bool"]
        for c_t in type_order:
            if c_t in by_type:
                var_list = ", ".join(by_type[c_t])
                lines.append(f"{space}{c_t} {var_list};")

        # String variables (char array)
        if "string" in by_type:
            for sname in by_type["string"]:
                lines.append(f"{space}char {sname}[100];")

        # Array variables
        for arr in arrays:
            elem_t = arr.c_type if arr.c_type != "string" else "char"
            size = arr.array_size or 100
            lines.append(f"{space}{elem_t} {arr.name}[{size}];")

        return lines

    def generate_function_prototype(self, func):
        ret_t = func.get("return_type", "void")
        name = func.get("name")
        params = func.get("params", [])
        if not params:
            return f"{ret_t} {name}(void)"
        p_strs = []
        for p_name, p_type in params:
            if p_type.upper() == "STRING":
                p_strs.append(f"char {p_name}[]")
            else:
                from symbol_table import TYPE_MAP
                c_t = TYPE_MAP.get(p_type.upper(), "int")
                p_strs.append(f"{c_t} {p_name}")
        return f"{ret_t} {name}({', '.join(p_strs)})"

    def generate_function(self, func):
        ret_t = func.get("return_type", "void")
        name = func.get("name")
        proto = self.generate_function_prototype(func)

        lines = [f"{proto}", "{"]

        # Local variable declarations
        symbols = func.get("symbols", {})
        param_names = {p[0] for p in func.get("params", [])}
        local_symbols = {k: v for k, v in symbols.items() if k not in param_names}

        decls = self.generate_declarations(local_symbols, indent=1)
        if decls:
            lines.extend(decls)
            lines.append("")

        for stmt in func.get("statements", []):
            lines.extend(self.generate_statement(stmt, indent=1))

        lines.append("}")
        return "\n".join(lines)

    def generate_statement(self, stmt, indent=1, scope=None):
        space = "    " * indent
        stype = stmt.get("type")

        # Declaration
        if stype == "declaration":
            if stmt.get("initial_value"):
                init_val = self.generate_expression(stmt["initial_value"])
                return [f"{space}{stmt['variable']} = {init_val};"]
            return []

        # Normal assignment
        if stype == "assignment":
            var = stmt["variable"]
            op = stmt.get("operator", "=")
            expr = stmt["expression"]

            # Check if this variable is a string
            var_type = "int"
            if scope:
                sym = scope.lookup(var)
                if sym:
                    var_type = sym.c_type

            if var_type == "string" and expr.get("type") == "string_literal":
                self.headers.add("<string.h>")
                val = expr["value"]
                return [f'{space}snprintf({var}, sizeof({var}), "%s", "{val}");']

            expr_str = self.generate_expression(expr)
            return [f"{space}{var} {op} {expr_str};"]

        # Array assignment
        if stype == "array_assignment":
            var = stmt["variable"]
            idx = self.generate_expression(stmt["index"])
            op = stmt.get("operator", "=")
            expr_str = self.generate_expression(stmt["expression"])
            return [f"{space}{var}[{idx}] {op} {expr_str};"]

        # Increments / Decrements
        if stype == "increment":
            var = stmt["variable"]
            op = stmt["operator"]
            if stmt.get("prefix"):
                return [f"{space}{op}{var};"]
            return [f"{space}{var}{op};"]

        # Expression statement (e.g. function call)
        if stype == "expression_statement":
            expr_str = self.generate_expression(stmt["expression"])
            return [f"{space}{expr_str};"]

        # Input statement
        if stype == "input":
            return self.generate_input(stmt, indent, scope)

        # Output statement
        if stype == "output":
            return self.generate_output(stmt, indent, scope)

        # IF statement
        if stype == "if":
            return self.generate_if(stmt, indent, scope)

        # FOR loop (Pseudocode style)
        if stype == "for":
            return self.generate_for(stmt, indent, scope)

        # FOR loop (C style)
        if stype == "for_c_style":
            return self.generate_for_c_style(stmt, indent, scope)

        # WHILE loop
        if stype == "while":
            return self.generate_while(stmt, indent, scope)

        # REPEAT ... UNTIL loop
        if stype == "repeat_until":
            return self.generate_repeat_until(stmt, indent, scope)

        # DO ... WHILE loop
        if stype == "do_while":
            return self.generate_do_while(stmt, indent, scope)

        # RETURN statement
        if stype == "return":
            if stmt.get("expression"):
                expr_str = self.generate_expression(stmt["expression"])
                return [f"{space}return {expr_str};"]
            return [f"{space}return;"]

        return []

    def generate_input(self, stmt, indent, scope):
        space = "    " * indent
        lines = []

        for item in stmt.get("items", []):
            var = item["variable"]
            idx = item.get("index")

            var_type = "int"
            if scope:
                sym = scope.lookup(var)
                if sym:
                    var_type = sym.c_type

            if idx is not None:
                idx_str = self.generate_expression(idx)
                target = f"{var}[{idx_str}]"
                addr = f"&{target}"
            else:
                target = var
                addr = target if var_type == "string" else f"&{target}"

            fmt = SCANF_FORMATS.get(var_type, "%d")

            if var_type == "bool":
                self.headers.add("<stdbool.h>")
                self.temp_var_count += 1
                tname = f"_temp_bool_{self.temp_var_count}"
                lines.append(f"{space}int {tname};")
                lines.append(f'{space}scanf("%d", &{tname});')
                lines.append(f"{space}{target} = ({tname} != 0);")
            else:
                lines.append(f'{space}scanf("{fmt}", {addr});')

        return lines

    def generate_output(self, stmt, indent, scope):
        space = "    " * indent
        expressions = stmt.get("expressions", [])

        if not expressions:
            return [f'{space}printf("\\n");']

        format_parts = []
        arg_parts = []

        for expr in expressions:
            etype = expr.get("type")

            # String literal: place directly into format string
            if etype == "string_literal":
                escaped = expr["value"].replace("\\", "\\\\").replace('"', '\\"').replace("%", "%%")
                format_parts.append(escaped)

            # Character literal
            elif etype == "char_literal":
                format_parts.append("%c")
                arg_parts.append(f"'{expr['value']}'")

            # Number literal
            elif etype == "number":
                if expr.get("is_float"):
                    format_parts.append("%f")
                else:
                    format_parts.append("%d")
                arg_parts.append(expr["value"])

            # Boolean literal
            elif etype == "boolean_literal":
                format_parts.append("%s")
                arg_parts.append('"true"' if expr["value"] else '"false"')

            # Variables, arrays, expressions
            else:
                expr_type = self.infer_expr_type(expr, scope)
                expr_str = self.generate_expression(expr)

                if expr_type == "bool":
                    self.headers.add("<stdbool.h>")
                    format_parts.append("%s")
                    arg_parts.append(f'({expr_str} ? "true" : "false")')
                elif expr_type == "float":
                    format_parts.append("%f")
                    arg_parts.append(expr_str)
                elif expr_type == "double":
                    format_parts.append("%lf")
                    arg_parts.append(expr_str)
                elif expr_type == "char":
                    format_parts.append("%c")
                    arg_parts.append(expr_str)
                elif expr_type == "string":
                    format_parts.append("%s")
                    arg_parts.append(expr_str)
                elif expr_type == "long":
                    format_parts.append("%ld")
                    arg_parts.append(expr_str)
                elif expr_type == "short":
                    format_parts.append("%hd")
                    arg_parts.append(expr_str)
                else:
                    format_parts.append("%d")
                    arg_parts.append(expr_str)

        fmt_str = "".join(format_parts) + "\\n"
        if arg_parts:
            args_str = ", ".join(arg_parts)
            return [f'{space}printf("{fmt_str}", {args_str});']
        else:
            return [f'{space}printf("{fmt_str}");']

    def generate_if(self, stmt, indent, scope):
        space = "    " * indent
        cond_str = self.generate_expression(stmt["condition"])
        lines = [f"{space}if ({cond_str}) {{"]

        for s in stmt.get("statements", []):
            lines.extend(self.generate_statement(s, indent + 1, scope))

        for elif_node in stmt.get("else_ifs", []):
            elif_cond = self.generate_expression(elif_node["condition"])
            lines.append(f"{space}}} else if ({elif_cond}) {{")
            for s in elif_node.get("statements", []):
                lines.extend(self.generate_statement(s, indent + 1, scope))

        if stmt.get("else_statements"):
            lines.append(f"{space}}} else {{")
            for s in stmt["else_statements"]:
                lines.extend(self.generate_statement(s, indent + 1, scope))

        lines.append(f"{space}}}")
        return lines

    def generate_for(self, stmt, indent, scope):
        space = "    " * indent
        var = stmt["variable"]
        start_str = self.generate_expression(stmt["start"])
        end_str = self.generate_expression(stmt["end"])

        # Determine step
        if stmt.get("step"):
            step_str = self.generate_expression(stmt["step"])
            header = f"for ({var} = {start_str}; {var} <= {end_str}; {var} += {step_str})"
        else:
            header = f"for ({var} = {start_str}; {var} <= {end_str}; {var}++)"

        lines = [f"{space}{header} {{"]
        for s in stmt.get("statements", []):
            lines.extend(self.generate_statement(s, indent + 1, scope))
        lines.append(f"{space}}}")
        return lines

    def generate_for_c_style(self, stmt, indent, scope):
        space = "    " * indent
        init_lines = self.generate_statement(stmt["init"], 0, scope)
        init_str = init_lines[0].rstrip(";") if init_lines else ""
        cond_str = self.generate_expression(stmt["condition"])
        upd_lines = self.generate_statement(stmt["update"], 0, scope)
        upd_str = upd_lines[0].rstrip(";") if upd_lines else ""

        lines = [f"{space}for ({init_str}; {cond_str}; {upd_str}) {{"]
        for s in stmt.get("statements", []):
            lines.extend(self.generate_statement(s, indent + 1, scope))
        lines.append(f"{space}}}")
        return lines

    def generate_while(self, stmt, indent, scope):
        space = "    " * indent
        cond_str = self.generate_expression(stmt["condition"])
        lines = [f"{space}while ({cond_str}) {{"]
        for s in stmt.get("statements", []):
            lines.extend(self.generate_statement(s, indent + 1, scope))
        lines.append(f"{space}}}")
        return lines

    def generate_repeat_until(self, stmt, indent, scope):
        space = "    " * indent
        cond_str = self.generate_expression(stmt["condition"])
        lines = [f"{space}do {{"]
        for s in stmt.get("statements", []):
            lines.extend(self.generate_statement(s, indent + 1, scope))
        # Repeat until condition becomes true => loop continues while NOT condition
        lines.append(f"{space}}} while (!({cond_str}));")
        return lines

    def generate_do_while(self, stmt, indent, scope):
        space = "    " * indent
        cond_str = self.generate_expression(stmt["condition"])
        lines = [f"{space}do {{"]
        for s in stmt.get("statements", []):
            lines.extend(self.generate_statement(s, indent + 1, scope))
        lines.append(f"{space}}} while ({cond_str});")
        return lines

    def generate_expression(self, expr):
        if not expr:
            return ""

        etype = expr.get("type")

        if etype == "number":
            return expr["value"]

        if etype == "string_literal":
            return f'"{expr["value"]}"'

        if etype == "char_literal":
            return f"'{expr['value']}'"

        if etype == "boolean_literal":
            self.headers.add("<stdbool.h>")
            return "true" if expr["value"] else "false"

        if etype == "identifier":
            return expr["value"]

        if etype == "array_access":
            idx_str = self.generate_expression(expr["index"])
            return f"{expr['variable']}[{idx_str}]"

        if etype == "function_call":
            args = [self.generate_expression(a) for a in expr.get("arguments", [])]
            return f"{expr['name']}({', '.join(args)})"

        if etype == "condition":
            left = self.generate_expression(expr["left"])
            right = self.generate_expression(expr["right"])
            op = expr["operator"]
            return f"({left} {op} {right})"

        if etype == "unary":
            op = expr["operator"]
            operand = self.generate_expression(expr["operand"])
            return f"{op}({operand})"

        if etype == "binary":
            left = self.generate_expression(expr["left"])
            right = self.generate_expression(expr["right"])
            op = expr["operator"]
            return f"({left} {op} {right})"

        return ""

    def infer_expr_type(self, expr, scope):
        if not expr:
            return "int"
        etype = expr.get("type")
        if etype == "number":
            return "float" if expr.get("is_float") else "int"
        if etype == "string_literal":
            return "string"
        if etype == "char_literal":
            return "char"
        if etype == "boolean_literal":
            return "bool"
        if etype == "condition":
            return "bool"
        if etype == "identifier" and scope:
            sym = scope.lookup(expr["value"])
            return sym.c_type if sym else "int"
        if etype == "array_access" and scope:
            sym = scope.lookup(expr["variable"])
            return sym.c_type if sym else "int"
        if etype == "unary":
            if expr.get("operator") == "!":
                return "bool"
            return self.infer_expr_type(expr.get("operand"), scope)
        if etype == "binary":
            op = expr.get("operator")
            if op in ["&&", "||", "==", "!=", "<", ">", "<=", ">="]:
                return "bool"
            left_t = self.infer_expr_type(expr.get("left"), scope)
            right_t = self.infer_expr_type(expr.get("right"), scope)
            if "string" in [left_t, right_t]:
                return "string"
            if "double" in [left_t, right_t]:
                return "double"
            if "float" in [left_t, right_t]:
                return "float"
            return "int"
        return "int"

    def build_explanation(self, tree, headers):
        symbols = tree.get("symbols", {})
        self.explanation_steps.append({
            "stage": "Header Inclusions",
            "details": f"Included headers: {', '.join(headers)}. " +
                       ("<stdbool.h> added for boolean support. " if "<stdbool.h>" in headers else "") +
                       ("<string.h> added for safe string manipulation. " if "<string.h>" in headers else "")
        })

        if symbols:
            var_summaries = []
            for name, sym in symbols.items():
                origin = "explicitly declared" if sym.is_explicit else f"inferred from {sym.inferred_from or 'usage'}"
                var_summaries.append(f"'{name}' -> C type `{sym.c_type}` ({origin})")
            self.explanation_steps.append({
                "stage": "Data Type Analysis & Symbol Resolution",
                "details": f"Resolved {len(symbols)} variable(s): " + "; ".join(var_summaries)
            })

        funcs = tree.get("functions", [])
        if funcs:
            func_summaries = [f"`{f['name']}` returning `{f['return_type']}`" for f in funcs]
            self.explanation_steps.append({
                "stage": "Functions & Procedures",
                "details": f"Generated prototypes and definitions for: {', '.join(func_summaries)}."
            })

        self.explanation_steps.append({
            "stage": "Control Flow & I/O",
            "details": "Mapped pseudocode INPUT/OUTPUT statements to typed scanf/printf, preserved nested blocks, and structured loops with standard C syntax."
        })