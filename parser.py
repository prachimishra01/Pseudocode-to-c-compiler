"""
Parser for the Pseudocode to C Compiler.
Constructs an Abstract Syntax Tree (AST) supporting multiple syntax variations,
nested blocks, data types, arrays, functions, loops, and conditions.
"""

from errors import ParserError, TypeError, SemanticError
from symbol_table import SymbolTable, TYPE_MAP

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.global_symbol_table = SymbolTable(scope_name="global")
        self.current_scope = self.global_symbol_table
        self.functions = []

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]  # EOF token

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def advance(self):
        tok = self.current()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def match(self, *token_types):
        if self.current().type in token_types:
            return self.advance()
        return None

    def expect(self, token_type, error_msg=None, suggestion=None):
        tok = self.current()
        if tok.type != token_type:
            msg = error_msg or f"Expected {token_type}, found '{tok.value}'"
            raise ParserError(f"Line {tok.line}: {msg}", line=tok.line, suggestion=suggestion)
        return self.advance()

    def parse(self):
        """Parse complete program."""
        main_statements = []

        while self.current().type != "EOF":
            tok = self.current()

            # Skip optional START / BEGIN / PROGRAM / MAIN
            if tok.type in ["START", "PROGRAM", "MAIN"]:
                self.advance()
                # Optional program name
                if tok.type == "PROGRAM" and self.current().type == "IDENTIFIER":
                    self.advance()
                continue

            # Skip optional END / STOP at program end
            if tok.type == "END":
                self.advance()
                continue

            # Skip stray semicolons
            if tok.type == "SEMICOLON":
                self.advance()
                continue

            # Check if this is a function or procedure
            if tok.type in ["FUNCTION", "PROCEDURE"]:
                func_node = self.parse_function_or_procedure()
                self.functions.append(func_node)
            else:
                stmt = self.parse_statement()
                if stmt:
                    if isinstance(stmt, list):
                        main_statements.extend(stmt)
                    else:
                        main_statements.append(stmt)

        return {
            "type": "program",
            "statements": main_statements,
            "functions": self.functions,
            "symbols": self.global_symbol_table.get_all_symbols(),
            "symbol_table": self.global_symbol_table,
            "warnings": self.global_symbol_table.warnings
        }

    def parse_statement(self):
        """Parse a single pseudocode statement."""
        tok = self.current()

        # Semicolons
        if tok.type == "SEMICOLON":
            self.advance()
            return None

        # DECLARE or ARRAY
        if tok.type in ["DECLARE", "ARRAY"]:
            return self.parse_declaration()

        # Direct type declaration like "INTEGER x, y" or "FLOAT price"
        if tok.type == "TYPE_SPEC" and self.peek().type == "IDENTIFIER":
            return self.parse_direct_type_declaration()

        # INPUT / READ / GET
        if tok.type == "INPUT":
            return self.parse_input()

        # OUTPUT / PRINT / DISPLAY / WRITE
        if tok.type == "OUTPUT":
            return self.parse_output()

        # SET x TO 10
        if tok.type == "SET":
            return self.parse_set()

        # LET x = 10
        if tok.type == "LET":
            return self.parse_let()

        # IF
        if tok.type == "IF":
            return self.parse_if()

        # FOR
        if tok.type == "FOR":
            return self.parse_for()

        # WHILE
        if tok.type == "WHILE":
            return self.parse_while()

        # REPEAT ... UNTIL
        if tok.type == "REPEAT":
            return self.parse_repeat_until()

        # DO ... WHILE
        if tok.type == "DO":
            return self.parse_do_while()

        # RETURN
        if tok.type == "RETURN":
            return self.parse_return()

        # Unary increment/decrement: ++x or --x
        if tok.type in ["INCREMENT", "DECREMENT"] and self.peek().type == "IDENTIFIER":
            op_tok = self.advance()
            var_tok = self.expect("IDENTIFIER")
            return {
                "type": "increment",
                "operator": op_tok.value,
                "variable": var_tok.value,
                "prefix": True,
                "line": tok.line
            }

        # Identifier: could be assignment, array assignment, postfix ++/--, or function call
        if tok.type == "IDENTIFIER":
            # Check postfix ++/--
            if self.peek().type in ["INCREMENT", "DECREMENT"]:
                var_tok = self.advance()
                op_tok = self.advance()
                return {
                    "type": "increment",
                    "operator": op_tok.value,
                    "variable": var_tok.value,
                    "prefix": False,
                    "line": tok.line
                }

            # Check function call: func(arg1, arg2)
            if self.peek().type == "LPAREN":
                expr = self.parse_primary()
                return {
                    "type": "expression_statement",
                    "expression": expr,
                    "line": tok.line
                }

            # Array assignment: numbers[0] = 10
            if self.peek().type == "LBRACKET":
                return self.parse_array_assignment()

            # Normal assignment: x = 10 or x += 5
            return self.parse_assignment()

        raise ParserError(
            f"Line {tok.line}: Unsupported or invalid pseudocode statement '{tok.value}'",
            line=tok.line,
            suggestion="Check statement syntax (e.g. SET x TO 10, IF condition THEN, FOR i = 1 TO 10, DISPLAY x)."
        )

    def parse_declaration(self):
        """Parse 'DECLARE x: INTEGER', 'DECLARE nums[5]: INTEGER', or 'ARRAY nums[5]'."""
        decl_tok = self.advance()  # DECLARE or ARRAY
        line = decl_tok.line

        is_array_keyword = (decl_tok.type == "ARRAY")

        var_names = []
        is_array = is_array_keyword
        array_size = None

        # First identifier
        first_id = self.expect("IDENTIFIER", "Expected variable or array name after DECLARE/ARRAY").value

        # Check array bracket
        if self.match("LBRACKET"):
            is_array = True
            size_tok = self.current()
            if size_tok.type in ["NUMBER", "IDENTIFIER"]:
                array_size = self.advance().value
            self.expect("RBRACKET", "Expected ']' to close array dimension")
            var_names.append(first_id)
        else:
            var_names.append(first_id)
            # Could be comma-separated list of variables: DECLARE a, b, c: INTEGER
            while self.match("COMMA"):
                next_id = self.expect("IDENTIFIER", "Expected variable name after comma").value
                var_names.append(next_id)

        # Optional type specification: e.g. ": INTEGER" or "AS INTEGER"
        pseudo_type = "INTEGER"  # default if omitted
        if self.match("COLON") or (self.current().type == "IDENTIFIER" and self.current().value.upper() == "AS"):
            if self.current().value.upper() == "AS":
                self.advance()
            type_tok = self.expect("TYPE_SPEC", "Expected data type (e.g. INTEGER, FLOAT, STRING, BOOLEAN)")
            pseudo_type = type_tok.value.upper()
        elif is_array_keyword:
            # Check optional 'OF INTEGER'
            if self.current().type == "IDENTIFIER" and self.current().value.upper() == "OF":
                self.advance()
                type_tok = self.expect("TYPE_SPEC", "Expected data type after 'OF'")
                pseudo_type = type_tok.value.upper()

        # Optional initialization: e.g. DECLARE count: INTEGER = 0
        init_expr = None
        if self.match("ASSIGN"):
            init_expr = self.parse_expression()

        statements = []
        for vname in var_names:
            self.current_scope.declare(
                name=vname,
                pseudo_type=pseudo_type,
                is_explicit=True,
                is_array=is_array,
                array_size=array_size or 10,
                line=line
            )
            statements.append({
                "type": "declaration",
                "variable": vname,
                "pseudo_type": pseudo_type,
                "c_type": TYPE_MAP.get(pseudo_type, "int"),
                "is_array": is_array,
                "array_size": array_size or 10,
                "initial_value": init_expr,
                "line": line
            })

        return statements if len(statements) > 1 else statements[0]

    def parse_direct_type_declaration(self):
        """Parse 'INTEGER x, y' or 'FLOAT price = 99.50'."""
        type_tok = self.advance()
        pseudo_type = type_tok.value.upper()
        line = type_tok.line

        statements = []
        while True:
            vname = self.expect("IDENTIFIER", "Expected variable name in declaration").value
            is_array = False
            array_size = None
            if self.match("LBRACKET"):
                is_array = True
                size_tok = self.current()
                if size_tok.type in ["NUMBER", "IDENTIFIER"]:
                    array_size = self.advance().value
                self.expect("RBRACKET", "Expected ']'")

            init_expr = None
            if self.match("ASSIGN"):
                init_expr = self.parse_expression()

            self.current_scope.declare(
                name=vname,
                pseudo_type=pseudo_type,
                is_explicit=True,
                is_array=is_array,
                array_size=array_size or 10,
                line=line
            )

            statements.append({
                "type": "declaration",
                "variable": vname,
                "pseudo_type": pseudo_type,
                "c_type": TYPE_MAP.get(pseudo_type, "int"),
                "is_array": is_array,
                "array_size": array_size or 10,
                "initial_value": init_expr,
                "line": line
            })

            if not self.match("COMMA"):
                break

        return statements if len(statements) > 1 else statements[0]

    def parse_set(self):
        """Parse 'SET x TO 10' or 'SET numbers[i] TO 10'."""
        set_tok = self.advance()
        var_tok = self.expect("IDENTIFIER", "Expected variable name after SET")
        var_name = var_tok.value

        # Check array index
        index_expr = None
        if self.match("LBRACKET"):
            index_expr = self.parse_expression()
            self.expect("RBRACKET", "Expected ']' after array index")

        # Expect TO or =
        if not (self.match("TO") or self.match("ASSIGN")):
            raise ParserError(
                f"Line {var_tok.line}: Expected 'TO' or '=' in SET statement",
                line=var_tok.line,
                suggestion="Use format: SET x TO 10"
            )

        expr = self.parse_expression()
        inferred_type = self.infer_expression_type(expr)

        if index_expr is None:
            self.current_scope.infer(var_name, inferred_type, line=set_tok.line, reason="SET assignment")
            return {
                "type": "assignment",
                "variable": var_name,
                "operator": "=",
                "expression": expr,
                "line": set_tok.line
            }
        else:
            return {
                "type": "array_assignment",
                "variable": var_name,
                "index": index_expr,
                "operator": "=",
                "expression": expr,
                "line": set_tok.line
            }

    def parse_let(self):
        """Parse 'LET x = 10' or 'LET x: INTEGER = 10'."""
        let_tok = self.advance()
        var_tok = self.expect("IDENTIFIER", "Expected variable name after LET")
        var_name = var_tok.value

        # Optional type: LET x: INTEGER = 10
        if self.match("COLON"):
            type_tok = self.expect("TYPE_SPEC", "Expected data type after ':'")
            pseudo_type = type_tok.value.upper()
            self.current_scope.declare(
                name=var_name,
                pseudo_type=pseudo_type,
                is_explicit=True,
                line=let_tok.line
            )

        self.expect("ASSIGN", "Expected '=' after variable name in LET statement")
        expr = self.parse_expression()
        inferred_type = self.infer_expression_type(expr)
        self.current_scope.infer(var_name, inferred_type, line=let_tok.line, reason="LET assignment")

        return {
            "type": "assignment",
            "variable": var_name,
            "operator": "=",
            "expression": expr,
            "line": let_tok.line
        }

    def parse_assignment(self):
        """Parse 'x = 10' or 'x += 5'."""
        var_tok = self.advance()
        var_name = var_tok.value

        op_tok = self.match("ASSIGN", "ASSIGN_OP")
        if not op_tok:
            raise ParserError(
                f"Line {var_tok.line}: Expected '=' or assignment operator after '{var_name}'",
                line=var_tok.line,
                suggestion=f"Use: {var_name} = <expression>"
            )

        expr = self.parse_expression()
        inferred_type = self.infer_expression_type(expr)

        self.current_scope.infer(var_name, inferred_type, line=var_tok.line, reason="Assignment")

        return {
            "type": "assignment",
            "variable": var_name,
            "operator": op_tok.value,
            "expression": expr,
            "line": var_tok.line
        }

    def parse_array_assignment(self):
        """Parse 'numbers[i] = 10'."""
        var_tok = self.advance()
        var_name = var_tok.value

        self.expect("LBRACKET", "Expected '['")
        index_expr = self.parse_expression()
        self.expect("RBRACKET", "Expected ']'")

        op_tok = self.match("ASSIGN", "ASSIGN_OP")
        if not op_tok:
            raise ParserError(
                f"Line {var_tok.line}: Expected '=' after array index",
                line=var_tok.line
            )

        expr = self.parse_expression()
        inferred_type = self.infer_expression_type(expr)

        if not self.current_scope.exists(var_name):
            # Infer as array
            self.current_scope.declare(
                name=var_name,
                pseudo_type="INTEGER" if inferred_type == "int" else inferred_type.upper(),
                is_explicit=False,
                is_array=True,
                array_size=100,
                line=var_tok.line
            )

        return {
            "type": "array_assignment",
            "variable": var_name,
            "index": index_expr,
            "operator": op_tok.value,
            "expression": expr,
            "line": var_tok.line
        }

    def parse_input(self):
        """Parse 'INPUT x', 'READ a, b', 'GET numbers[i]'."""
        input_tok = self.advance()
        line = input_tok.line

        items = []
        while True:
            var_tok = self.expect("IDENTIFIER", "Expected variable name to read input into")
            var_name = var_tok.value

            # Check array index
            index_expr = None
            if self.match("LBRACKET"):
                index_expr = self.parse_expression()
                self.expect("RBRACKET", "Expected ']'")

            if not self.current_scope.exists(var_name):
                # Default to int if no prior knowledge
                if index_expr is not None:
                    self.current_scope.declare(
                        name=var_name,
                        pseudo_type="INTEGER",
                        is_explicit=False,
                        is_array=True,
                        array_size=100,
                        line=line
                    )
                else:
                    self.current_scope.infer(var_name, "int", line=line, reason="INPUT statement (default int)")

            items.append({
                "variable": var_name,
                "index": index_expr
            })

            if not self.match("COMMA"):
                break

        return {
            "type": "input",
            "items": items,
            "line": line
        }

    def parse_output(self):
        """Parse 'OUTPUT x', 'PRINT \"Value: \", x', 'DISPLAY x'."""
        out_tok = self.advance()
        line = out_tok.line

        expressions = []
        while True:
            expr = self.parse_expression()
            expressions.append(expr)
            if not self.match("COMMA"):
                break

        return {
            "type": "output",
            "expressions": expressions,
            "line": line
        }

    def parse_if(self):
        """Parse IF condition THEN ... [ELSE IF condition THEN ...] [ELSE ...] END IF."""
        if_tok = self.advance()
        line = if_tok.line

        condition = self.parse_condition()

        # Optional THEN
        self.match("THEN")

        then_stmts = []
        while self.current().type not in ["ELSEIF", "ELSE", "END_IF", "END", "EOF"]:
            stmt = self.parse_statement()
            if stmt:
                if isinstance(stmt, list):
                    then_stmts.extend(stmt)
                else:
                    then_stmts.append(stmt)

        else_ifs = []
        while self.current().type == "ELSEIF":
            elif_tok = self.advance()
            elif_cond = self.parse_condition()
            self.match("THEN")
            elif_stmts = []
            while self.current().type not in ["ELSEIF", "ELSE", "END_IF", "END", "EOF"]:
                stmt = self.parse_statement()
                if stmt:
                    if isinstance(stmt, list):
                        elif_stmts.extend(stmt)
                    else:
                        elif_stmts.append(stmt)
            else_ifs.append({
                "condition": elif_cond,
                "statements": elif_stmts,
                "line": elif_tok.line
            })

        else_stmts = []
        if self.current().type == "ELSE":
            self.advance()
            while self.current().type not in ["END_IF", "END", "EOF"]:
                stmt = self.parse_statement()
                if stmt:
                    if isinstance(stmt, list):
                        else_stmts.extend(stmt)
                    else:
                        else_stmts.append(stmt)

        if self.current().type != "END_IF":
            raise ParserError(
                f"Line {self.current().line}: Missing 'END IF' (or 'ENDIF') to close IF block from line {line}.",
                line=self.current().line,
                suggestion="Add 'END IF' to close the conditional block."
            )
        self.advance()  # Consume END_IF

        return {
            "type": "if",
            "condition": condition,
            "statements": then_stmts,
            "else_ifs": else_ifs,
            "else_statements": else_stmts,
            "line": line
        }

    def parse_for(self):
        """
        Parse FOR loops:
        1. FOR i = 1 TO 10 [STEP 1] ... END FOR / NEXT i
        2. FOR i FROM 1 TO 10 ... END FOR
        3. FOR (i = 0; i < 10; i++) ... END FOR / }
        """
        for_tok = self.advance()
        line = for_tok.line

        # Check C-style FOR (i = 0; i < 10; i++)
        if self.current().type == "LPAREN":
            self.advance()
            init_stmt = self.parse_statement()
            if self.current().type == "SEMICOLON":
                self.advance()
            cond_expr = self.parse_condition()
            self.expect("SEMICOLON", "Expected ';' after condition in for loop")
            # Update part
            update_stmt = self.parse_statement()
            self.expect("RPAREN", "Expected ')' to close for loop header")

            body_stmts = self.parse_loop_body(["END_FOR", "RBRACE", "END"])
            self.match("END_FOR", "RBRACE")

            return {
                "type": "for_c_style",
                "init": init_stmt,
                "condition": cond_expr,
                "update": update_stmt,
                "statements": body_stmts,
                "line": line
            }

        # Pseudocode FOR loop
        var_tok = self.expect("IDENTIFIER", "Expected loop counter variable in FOR loop")
        var_name = var_tok.value

        # Infer loop variable as int
        self.current_scope.infer(var_name, "int", line=line, reason="FOR loop counter")

        # Expect '=' or 'FROM'
        if not (self.match("ASSIGN") or self.match("FROM")):
            raise ParserError(
                f"Line {line}: Expected '=' or 'FROM' after loop variable '{var_name}'",
                line=line,
                suggestion=f"Use: FOR {var_name} = 1 TO 10"
            )

        start_expr = self.parse_expression()
        self.expect("TO", "Expected 'TO' in FOR loop (e.g. FOR i = 1 TO 10)")
        end_expr = self.parse_expression()

        # Optional STEP
        step_expr = None
        if self.match("STEP"):
            step_expr = self.parse_expression()

        # Parse body until END_FOR or NEXT [i]
        body_stmts = []
        while self.current().type not in ["END_FOR", "NEXT", "END", "EOF"]:
            stmt = self.parse_statement()
            if stmt:
                if isinstance(stmt, list):
                    body_stmts.extend(stmt)
                else:
                    body_stmts.append(stmt)

        if self.current().type not in ["END_FOR", "NEXT"]:
            raise ParserError(
                f"Line {self.current().line}: Missing 'END FOR' or 'NEXT' to terminate loop starting at line {line}.",
                line=self.current().line,
                suggestion="Add 'END FOR' or 'NEXT' to close the loop."
            )

        term_tok = self.advance()
        if term_tok.type == "NEXT" and self.current().type == "IDENTIFIER":
            self.advance()  # Optional counter variable after NEXT: NEXT i

        return {
            "type": "for",
            "variable": var_name,
            "start": start_expr,
            "end": end_expr,
            "step": step_expr,
            "statements": body_stmts,
            "line": line
        }

    def parse_while(self):
        """Parse WHILE condition [DO] ... END WHILE."""
        while_tok = self.advance()
        line = while_tok.line

        condition = self.parse_condition()
        self.match("DO")  # Optional DO

        body_stmts = []
        while self.current().type not in ["END_WHILE", "END", "EOF"]:
            stmt = self.parse_statement()
            if stmt:
                if isinstance(stmt, list):
                    body_stmts.extend(stmt)
                else:
                    body_stmts.append(stmt)

        if self.current().type != "END_WHILE":
            raise ParserError(
                f"Line {self.current().line}: Missing 'END WHILE' (or 'ENDWHILE') for WHILE loop starting at line {line}.",
                line=self.current().line,
                suggestion="Add 'END WHILE' to close the loop."
            )
        self.advance()

        return {
            "type": "while",
            "condition": condition,
            "statements": body_stmts,
            "line": line
        }

    def parse_repeat_until(self):
        """Parse REPEAT ... UNTIL condition."""
        rep_tok = self.advance()
        line = rep_tok.line

        body_stmts = []
        while self.current().type not in ["UNTIL", "END", "EOF"]:
            stmt = self.parse_statement()
            if stmt:
                if isinstance(stmt, list):
                    body_stmts.extend(stmt)
                else:
                    body_stmts.append(stmt)

        if self.current().type != "UNTIL":
            raise ParserError(
                f"Line {self.current().line}: Missing 'UNTIL' for REPEAT block starting at line {line}.",
                line=self.current().line,
                suggestion="Add 'UNTIL <condition>' to terminate the REPEAT loop."
            )
        self.advance()
        condition = self.parse_condition()

        return {
            "type": "repeat_until",
            "condition": condition,
            "statements": body_stmts,
            "line": line
        }

    def parse_do_while(self):
        """Parse DO ... WHILE condition."""
        do_tok = self.advance()
        line = do_tok.line

        body_stmts = []
        while self.current().type not in ["WHILE", "EOF"]:
            stmt = self.parse_statement()
            if stmt:
                if isinstance(stmt, list):
                    body_stmts.extend(stmt)
                else:
                    body_stmts.append(stmt)

        if self.current().type != "WHILE":
            raise ParserError(
                f"Line {self.current().line}: Expected 'WHILE <condition>' after DO block starting at line {line}.",
                line=self.current().line
            )
        self.advance()
        condition = self.parse_condition()

        return {
            "type": "do_while",
            "condition": condition,
            "statements": body_stmts,
            "line": line
        }

    def parse_function_or_procedure(self):
        """Parse FUNCTION or PROCEDURE definition."""
        tok = self.advance()
        is_function = (tok.type == "FUNCTION")
        line = tok.line

        name_tok = self.expect("IDENTIFIER", "Expected function or procedure name")
        func_name = name_tok.value

        # Parameters
        self.expect("LPAREN", "Expected '(' after function/procedure name")
        params = []
        if self.current().type != "RPAREN":
            while True:
                p_id = self.expect("IDENTIFIER", "Expected parameter name").value
                p_type = "INTEGER"
                if self.match("COLON"):
                    type_tok = self.expect("TYPE_SPEC", "Expected parameter data type")
                    p_type = type_tok.value.upper()
                params.append((p_id, p_type))
                if not self.match("COMMA"):
                    break
        self.expect("RPAREN", "Expected ')' after parameter list")

        # Return type for function
        return_type = "void"
        if is_function:
            if self.match("COLON"):
                ret_tok = self.expect("TYPE_SPEC", "Expected return data type")
                return_type = TYPE_MAP.get(ret_tok.value.upper(), "int")
            else:
                return_type = "int"

        # Register in global symbol table
        self.global_symbol_table.declare_function(func_name, return_type, params, line=line)

        # Function scope
        func_scope = SymbolTable(parent=self.global_symbol_table, scope_name=func_name)
        for p_id, p_type in params:
            func_scope.declare(name=p_id, pseudo_type=p_type, is_explicit=True, line=line)

        prev_scope = self.current_scope
        self.current_scope = func_scope

        terminator = "END_FUNCTION" if is_function else "END_PROCEDURE"
        body_stmts = []
        while self.current().type not in [terminator, "EOF"]:
            stmt = self.parse_statement()
            if stmt:
                if isinstance(stmt, list):
                    body_stmts.extend(stmt)
                else:
                    body_stmts.append(stmt)

        if self.current().type != terminator:
            term_name = "END FUNCTION" if is_function else "END PROCEDURE"
            raise ParserError(
                f"Line {self.current().line}: Missing '{term_name}' to close {tok.value.lower()} '{func_name}' from line {line}.",
                line=self.current().line
            )
        self.advance()

        self.current_scope = prev_scope

        return {
            "type": "function",
            "name": func_name,
            "is_function": is_function,
            "return_type": return_type,
            "params": params,
            "statements": body_stmts,
            "symbols": func_scope.get_all_symbols(),
            "line": line
        }

    def parse_return(self):
        """Parse 'RETURN value' or 'RETURN'."""
        ret_tok = self.advance()
        expr = None
        if self.current().type not in ["SEMICOLON", "END_FUNCTION", "END_PROCEDURE", "EOF", "END_IF", "ELSE", "ELSEIF"]:
            expr = self.parse_expression()
        return {
            "type": "return",
            "expression": expr,
            "line": ret_tok.line
        }

    # =========================================================================
    # Conditions and Expressions
    # =========================================================================
    def parse_condition(self):
        """Parse conditions (logical OR, AND, NOT, comparisons, boolean literals/vars)."""
        return self.parse_logical_or()

    def parse_logical_or(self):
        expr = self.parse_logical_and()
        while self.match("LOGICAL_OR"):
            right = self.parse_logical_and()
            expr = {
                "type": "binary",
                "operator": "||",
                "left": expr,
                "right": right
            }
        return expr

    def parse_logical_and(self):
        expr = self.parse_logical_not()
        while self.match("LOGICAL_AND"):
            right = self.parse_logical_not()
            expr = {
                "type": "binary",
                "operator": "&&",
                "left": expr,
                "right": right
            }
        return expr

    def parse_logical_not(self):
        if self.match("LOGICAL_NOT"):
            operand = self.parse_logical_not()
            return {
                "type": "unary",
                "operator": "!",
                "operand": operand
            }
        return self.parse_comparison()

    def parse_comparison(self):
        left = self.parse_expression()
        comp_tok = self.match("COMPARATOR")
        if comp_tok:
            op = comp_tok.value
            if op == "<>":
                op = "!="
            right = self.parse_expression()
            return {
                "type": "condition",
                "operator": op,
                "left": left,
                "right": right
            }
        return left

    def parse_expression(self):
        """Parse arithmetic / string / boolean expression."""
        return self.parse_additive()

    def parse_additive(self):
        left = self.parse_multiplicative()
        while True:
            tok = self.current()
            if tok.type == "OPERATOR" and tok.value in ["+", "-"]:
                self.advance()
                right = self.parse_multiplicative()
                left = {
                    "type": "binary",
                    "operator": tok.value,
                    "left": left,
                    "right": right
                }
            else:
                break
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while True:
            tok = self.current()
            if (tok.type == "OPERATOR" and tok.value in ["*", "/", "%"]) or tok.type == "MOD":
                op_val = "%" if tok.type == "MOD" else tok.value
                self.advance()
                right = self.parse_unary()
                left = {
                    "type": "binary",
                    "operator": op_val,
                    "left": left,
                    "right": right
                }
            else:
                break
        return left

    def parse_unary(self):
        tok = self.current()
        if tok.type == "OPERATOR" and tok.value in ["+", "-"]:
            self.advance()
            operand = self.parse_unary()
            return {
                "type": "unary",
                "operator": tok.value,
                "operand": operand
            }
        if tok.type in ["LOGICAL_NOT"]:
            self.advance()
            operand = self.parse_unary()
            return {
                "type": "unary",
                "operator": "!",
                "operand": operand
            }
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()

        # Number literal
        if tok.type == "NUMBER":
            self.advance()
            is_float = ("." in tok.value)
            return {
                "type": "number",
                "value": tok.value,
                "is_float": is_float
            }

        # String literal
        if tok.type == "STRING_LITERAL":
            self.advance()
            return {
                "type": "string_literal",
                "value": tok.value
            }

        # Char literal
        if tok.type == "CHAR_LITERAL":
            self.advance()
            return {
                "type": "char_literal",
                "value": tok.value
            }

        # Boolean literal
        if tok.type == "BOOLEAN_LITERAL":
            self.advance()
            val = (tok.value.upper() == "TRUE")
            return {
                "type": "boolean_literal",
                "value": val
            }

        # Parenthesized expression
        if tok.type == "LPAREN":
            self.advance()
            expr = self.parse_logical_or()
            self.expect("RPAREN", "Expected ')' to close expression")
            return expr

        # Identifier: variable, array index, or function call
        if tok.type == "IDENTIFIER":
            name = self.advance().value

            # Function call
            if self.match("LPAREN"):
                args = []
                if self.current().type != "RPAREN":
                    while True:
                        arg_expr = self.parse_expression()
                        args.append(arg_expr)
                        if not self.match("COMMA"):
                            break
                self.expect("RPAREN", "Expected ')' after function arguments")
                return {
                    "type": "function_call",
                    "name": name,
                    "arguments": args
                }

            # Array access
            if self.match("LBRACKET"):
                idx_expr = self.parse_expression()
                self.expect("RBRACKET", "Expected ']' after array index")
                return {
                    "type": "array_access",
                    "variable": name,
                    "index": idx_expr
                }

            # Simple variable
            return {
                "type": "identifier",
                "value": name
            }

        raise ParserError(
            f"Line {tok.line}: Unexpected token '{tok.value}' in expression",
            line=tok.line,
            suggestion="Expected a number, variable, string, or parenthesized expression."
        )

    def parse_loop_body(self, terminators):
        stmts = []
        while self.current().type not in terminators + ["EOF"]:
            s = self.parse_statement()
            if s:
                if isinstance(s, list):
                    stmts.extend(s)
                else:
                    stmts.append(s)
        return stmts

    def infer_expression_type(self, expr):
        """Infer C data type resulting from an expression."""
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

        if etype == "identifier":
            var_name = expr["value"]
            existing = self.current_scope.lookup(var_name)
            return existing.c_type if existing else "int"

        if etype == "array_access":
            var_name = expr["variable"]
            existing = self.current_scope.lookup(var_name)
            return existing.c_type if existing else "int"

        if etype == "function_call":
            func_name = expr["name"]
            func = self.current_scope.lookup_function(func_name)
            return func.return_type if func else "int"

        if etype == "condition":
            return "bool"

        if etype == "unary":
            op = expr.get("operator")
            if op == "!":
                return "bool"
            return self.infer_expression_type(expr.get("operand"))

        if etype == "binary":
            op = expr.get("operator")
            if op in ["&&", "||", "==", "!=", "<", ">", "<=", ">="]:
                return "bool"
            left_t = self.infer_expression_type(expr.get("left"))
            right_t = self.infer_expression_type(expr.get("right"))
            if "string" in [left_t, right_t]:
                return "string"
            if "double" in [left_t, right_t]:
                return "double"
            if "float" in [left_t, right_t]:
                return "float"
            return "int"

        return "int"