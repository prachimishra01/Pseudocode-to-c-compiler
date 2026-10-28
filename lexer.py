"""
Lexer for the Pseudocode to C Compiler.
Tokenizes pseudocode text with support for flexible syntax, mixed casing,
comments, multi-word keywords, strings, chars, numbers, and operators.
"""

import re
from errors import LexerError

class Token:
    def __init__(self, token_type, value, line, column=1):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, L{self.line}:C{self.column})"


class Lexer:
    # Single and multi-word keywords mapped to canonical token types
    KEYWORD_MAP = {
        "START": "START",
        "BEGIN": "START",
        "PROGRAM": "PROGRAM",
        "MAIN": "MAIN",
        "END": "END",
        "STOP": "END",
        
        "INPUT": "INPUT",
        "READ": "INPUT",
        "GET": "INPUT",
        
        "OUTPUT": "OUTPUT",
        "PRINT": "OUTPUT",
        "DISPLAY": "OUTPUT",
        "WRITE": "OUTPUT",
        
        "SET": "SET",
        "LET": "LET",
        "TO": "TO",
        "FROM": "FROM",
        "STEP": "STEP",
        
        "DECLARE": "DECLARE",
        "ARRAY": "ARRAY",
        
        "IF": "IF",
        "THEN": "THEN",
        "ELSE": "ELSE",
        "ELSEIF": "ELSEIF",
        "ELIF": "ELSEIF",
        "ENDIF": "END_IF",
        
        "FOR": "FOR",
        "ENDFOR": "END_FOR",
        "NEXT": "NEXT",
        
        "WHILE": "WHILE",
        "ENDWHILE": "END_WHILE",
        "DO": "DO",
        
        "REPEAT": "REPEAT",
        "UNTIL": "UNTIL",
        
        "FUNCTION": "FUNCTION",
        "PROCEDURE": "PROCEDURE",
        "RETURN": "RETURN",
        "ENDFUNCTION": "END_FUNCTION",
        "ENDPROCEDURE": "END_PROCEDURE",
        
        "AND": "LOGICAL_AND",
        "OR": "LOGICAL_OR",
        "NOT": "LOGICAL_NOT",
        "MOD": "MOD",
        
        "TRUE": "BOOLEAN_LITERAL",
        "FALSE": "BOOLEAN_LITERAL",
        
        # Data types
        "INTEGER": "TYPE_SPEC",
        "INT": "TYPE_SPEC",
        "FLOAT": "TYPE_SPEC",
        "REAL": "TYPE_SPEC",
        "DOUBLE": "TYPE_SPEC",
        "CHARACTER": "TYPE_SPEC",
        "CHAR": "TYPE_SPEC",
        "STRING": "TYPE_SPEC",
        "BOOLEAN": "TYPE_SPEC",
        "BOOL": "TYPE_SPEC",
        "LONG": "TYPE_SPEC",
        "SHORT": "TYPE_SPEC",
        "VOID": "TYPE_SPEC",
    }

    # Regex definitions
    OPERATORS_AND_DELIMITERS = [
        ("++", "INCREMENT"),
        ("--", "DECREMENT"),
        ("==", "COMPARATOR"),
        ("!=", "COMPARATOR"),
        ("<>", "COMPARATOR"),
        ("<=", "COMPARATOR"),
        (">=", "COMPARATOR"),
        ("&&", "LOGICAL_AND"),
        ("||", "LOGICAL_OR"),
        ("+=", "ASSIGN_OP"),
        ("-=", "ASSIGN_OP"),
        ("*=", "ASSIGN_OP"),
        ("/=", "ASSIGN_OP"),
        ("<", "COMPARATOR"),
        (">", "COMPARATOR"),
        ("=", "ASSIGN"),
        ("+", "OPERATOR"),
        ("-", "OPERATOR"),
        ("*", "OPERATOR"),
        ("/", "OPERATOR"),
        ("%", "OPERATOR"),
        ("!", "LOGICAL_NOT"),
        ("(", "LPAREN"),
        (")", "RPAREN"),
        ("[", "LBRACKET"),
        ("]", "RBRACKET"),
        ("{", "LBRACE"),
        ("}", "RBRACE"),
        (",", "COMMA"),
        (":", "COLON"),
        (";", "SEMICOLON"),
    ]

    def tokenize(self, text):
        raw_tokens = []
        lines = text.splitlines(keepends=True)
        
        line_num = 1
        i = 0
        n = len(text)
        
        in_multiline_comment = False
        multiline_start_line = 1

        while i < n:
            # Check multiline comment end
            if in_multiline_comment:
                if text[i:i+2] == "*/":
                    in_multiline_comment = False
                    i += 2
                else:
                    if text[i] == "\n":
                        line_num += 1
                    i += 1
                continue

            # Check multiline comment start
            if text[i:i+2] == "/*":
                in_multiline_comment = True
                multiline_start_line = line_num
                i += 2
                continue

            # Check single line comment
            if text[i:i+2] == "//" or text[i] == "#":
                # skip until end of line
                while i < n and text[i] != "\n":
                    i += 1
                continue

            char = text[i]

            # Newlines
            if char == "\n":
                line_num += 1
                i += 1
                continue

            # Whitespace
            if char.isspace():
                i += 1
                continue

            # String literals
            if char == '"':
                start_line = line_num
                val = ""
                i += 1
                while i < n and text[i] != '"':
                    if text[i] == "\n":
                        line_num += 1
                    if text[i] == "\\" and i + 1 < n:
                        val += text[i:i+2]
                        i += 2
                    else:
                        val += text[i]
                        i += 1
                if i >= n:
                    raise LexerError(
                        f"Unterminated string literal starting at line {start_line}.",
                        line=start_line,
                        suggestion="Ensure all string literals are closed with double quotes '\"'."
                    )
                i += 1  # Skip closing quote
                raw_tokens.append(Token("STRING_LITERAL", val, start_line))
                continue

            # Character literals
            if char == "'":
                start_line = line_num
                val = ""
                i += 1
                while i < n and text[i] != "'":
                    if text[i] == "\n":
                        line_num += 1
                    if text[i] == "\\" and i + 1 < n:
                        val += text[i:i+2]
                        i += 2
                    else:
                        val += text[i]
                        i += 1
                if i >= n:
                    raise LexerError(
                        f"Unterminated character literal starting at line {start_line}.",
                        line=start_line,
                        suggestion="Ensure all character literals are closed with single quotes '\''."
                    )
                i += 1  # Skip closing quote
                raw_tokens.append(Token("CHAR_LITERAL", val, start_line))
                continue

            # Multi-character & single-character operators and delimiters
            matched_op = False
            for op, op_type in self.OPERATORS_AND_DELIMITERS:
                if text.startswith(op, i):
                    raw_tokens.append(Token(op_type, op, line_num))
                    i += len(op)
                    matched_op = True
                    break
            if matched_op:
                continue

            # Numbers (integer or floating point)
            if char.isdigit() or (char == '.' and i + 1 < n and text[i+1].isdigit()):
                start_i = i
                has_dot = (char == '.')
                i += 1
                while i < n:
                    if text[i] == '.' and not has_dot and i + 1 < n and text[i+1].isdigit():
                        has_dot = True
                        i += 1
                    elif text[i].isdigit():
                        i += 1
                    else:
                        break
                num_str = text[start_i:i]
                token_type = "NUMBER"
                raw_tokens.append(Token(token_type, num_str, line_num))
                continue

            # Identifiers or keywords
            if char.isalpha() or char == '_':
                start_i = i
                while i < n and (text[i].isalnum() or text[i] == '_'):
                    i += 1
                word = text[start_i:i]
                upper_word = word.upper()

                if upper_word in self.KEYWORD_MAP:
                    raw_tokens.append(Token(self.KEYWORD_MAP[upper_word], word, line_num))
                else:
                    raw_tokens.append(Token("IDENTIFIER", word, line_num))
                continue

            # If we reached here, invalid character
            raise LexerError(
                f"Invalid or unexpected character '{char}' at line {line_num}.",
                line=line_num,
                suggestion=f"Remove or replace character '{char}'."
            )

        if in_multiline_comment:
            raise LexerError(
                f"Unterminated multi-line comment starting at line {multiline_start_line}.",
                line=multiline_start_line,
                suggestion="Close multi-line comments with '*/'."
            )

        # Post-process multi-word tokens:
        # e.g. "END" + "IF" -> "END_IF"
        #      "END" + "WHILE" -> "END_WHILE"
        #      "END" + "FOR" -> "END_FOR"
        #      "END" + "FUNCTION" -> "END_FUNCTION"
        #      "END" + "PROCEDURE" -> "END_PROCEDURE"
        #      "ELSE" + "IF" -> "ELSEIF"
        #      "DO" + "WHILE" -> "DO_WHILE"
        merged_tokens = []
        k = 0
        total = len(raw_tokens)
        while k < total:
            curr = raw_tokens[k]
            next_t = raw_tokens[k+1] if k + 1 < total else None

            if curr.type == "END" and next_t:
                nxt_u = next_t.value.upper()
                if nxt_u == "IF" or next_t.type == "IF":
                    merged_tokens.append(Token("END_IF", "END IF", curr.line, curr.column))
                    k += 2
                    continue
                elif nxt_u == "WHILE" or next_t.type == "WHILE":
                    merged_tokens.append(Token("END_WHILE", "END WHILE", curr.line, curr.column))
                    k += 2
                    continue
                elif nxt_u == "FOR" or next_t.type == "FOR":
                    merged_tokens.append(Token("END_FOR", "END FOR", curr.line, curr.column))
                    k += 2
                    continue
                elif nxt_u == "FUNCTION" or next_t.type == "FUNCTION":
                    merged_tokens.append(Token("END_FUNCTION", "END FUNCTION", curr.line, curr.column))
                    k += 2
                    continue
                elif nxt_u == "PROCEDURE" or next_t.type == "PROCEDURE":
                    merged_tokens.append(Token("END_PROCEDURE", "END PROCEDURE", curr.line, curr.column))
                    k += 2
                    continue

            if curr.type == "ELSE" and next_t and (next_t.value.upper() == "IF" or next_t.type == "IF"):
                merged_tokens.append(Token("ELSEIF", "ELSE IF", curr.line, curr.column))
                k += 2
                continue

            if curr.type == "DO" and next_t and (next_t.value.upper() == "WHILE" or next_t.type == "WHILE"):
                merged_tokens.append(Token("DO_WHILE", "DO WHILE", curr.line, curr.column))
                k += 2
                continue

            # Standard pass-through
            merged_tokens.append(curr)
            k += 1

        last_line = line_num
        merged_tokens.append(Token("EOF", "", last_line, 1))
        return merged_tokens