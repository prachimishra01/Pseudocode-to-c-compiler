"""
Error definitions for the Pseudocode to C Compiler.
Provides rich error classes with line numbers, error categories,
and actionable suggestions for user-friendly diagnostics.
"""

class CompilerError(Exception):
    """Base class for all compiler diagnostics and errors."""
    def __init__(self, message, line=None, column=None, suggestion=None, error_type="Compiler Error"):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.suggestion = suggestion
        self.error_type = error_type

    def __str__(self):
        location = f"Line {self.line}" if self.line is not None else "General"
        if self.column is not None:
            location += f", Column {self.column}"
        
        result = f"[{self.error_type}] {location}: {self.message}"
        if self.suggestion:
            result += f"\n  -> Suggestion: {self.suggestion}"
        return result

    def to_dict(self):
        return {
            "type": self.error_type,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "suggestion": self.suggestion,
            "formatted": str(self)
        }


class LexerError(CompilerError):
    """Raised when an invalid token or character is encountered."""
    def __init__(self, message, line=None, column=None, suggestion=None):
        super().__init__(message, line, column, suggestion, error_type="Syntax Error (Lexer)")


class ParserError(CompilerError):
    """Raised when pseudocode grammar or statement structure is invalid."""
    def __init__(self, message, line=None, column=None, suggestion=None):
        super().__init__(message, line, column, suggestion, error_type="Syntax Error (Parser)")


class TypeError(CompilerError):
    """Raised when variable types conflict or cannot be safely inferred."""
    def __init__(self, message, line=None, column=None, suggestion=None):
        super().__init__(message, line, column, suggestion, error_type="Type Error")


class SemanticError(CompilerError):
    """Raised when semantic rules are violated (e.g. undeclared function, duplicate definition)."""
    def __init__(self, message, line=None, column=None, suggestion=None):
        super().__init__(message, line, column, suggestion, error_type="Semantic Error")


class UnsupportedError(CompilerError):
    """Raised when pseudocode uses constructs that are currently unsupported."""
    def __init__(self, message, line=None, column=None, suggestion=None):
        super().__init__(message, line, column, suggestion, error_type="Unsupported Feature")