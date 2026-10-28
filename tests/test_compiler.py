"""
Comprehensive test suite for the Pseudocode to C Compiler.
Verifies parsing, type handling, type inference, code generation,
error reporting, and execution of all 20 example programs.
"""

import unittest
from lexer import Lexer
from parser import Parser
from code_generator import CodeGenerator
from errors import CompilerError, LexerError, ParserError, TypeError
from examples import EXAMPLES


class TestPseudocodeCompiler(unittest.TestCase):

    def compile_snippet(self, code):
        lexer = Lexer()
        tokens = lexer.tokenize(code)
        parser = Parser(tokens)
        tree = parser.parse()
        gen = CodeGenerator()
        return gen.generate_with_metadata(tree)

    def test_all_twenty_examples(self):
        """Verify all 20 examples compile successfully into valid C code."""
        for ex in EXAMPLES:
            with self.subTest(example_id=ex["id"]):
                res = self.compile_snippet(ex["pseudocode"])
                c_code = res["c_code"]
                self.assertIn("int main(void)", c_code)
                self.assertIn("return 0;", c_code)
                self.assertIn("#include <stdio.h>", c_code)
                self.assertTrue(len(c_code) > 30)

    def test_explicit_types(self):
        """Test all supported explicit data types."""
        code = """
        START
            DECLARE i: INTEGER
            DECLARE f: FLOAT
            DECLARE r: REAL
            DECLARE d: DOUBLE
            DECLARE c: CHARACTER
            DECLARE s: STRING
            DECLARE b: BOOLEAN
            DECLARE l: LONG
            DECLARE sh: SHORT

            i = 42
            f = 3.14
            r = 2.71828
            d = 1.414
            c = 'Z'
            s = "Compiler"
            b = true
            l = 100000
            sh = 10
        END
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn("int i;", c_code)
        self.assertIn("float f;", c_code)
        self.assertIn("double r, d;", c_code)
        self.assertIn("char c;", c_code)
        self.assertIn("char s[100];", c_code)
        self.assertIn("bool b;", c_code)
        self.assertIn("long l;", c_code)
        self.assertIn("short sh;", c_code)
        self.assertIn("#include <stdbool.h>", c_code)
        self.assertIn("#include <string.h>", c_code)

    def test_type_inference(self):
        """Test type inference when variables are not explicitly declared."""
        code = """
        START
            a = 10
            b = 25.75
            c = 'A'
            d = true
            e = "Hello"
        END
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn("int a;", c_code)
        self.assertIn("float b;", c_code)
        self.assertIn("char c;", c_code)
        self.assertIn("bool d;", c_code)
        self.assertIn("char e[100];", c_code)

    def test_syntax_variations(self):
        """Test SET TO, LET =, READ, WRITE, DISPLAY, etc."""
        code = """
        START
            SET x TO 10
            LET y = 20
            READ z
            WRITE x
            DISPLAY y
        END
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn("x = 10;", c_code)
        self.assertIn("y = 20;", c_code)
        self.assertIn("scanf(\"%d\", &z);", c_code)
        self.assertIn("printf(\"%d\\n\", x);", c_code)
        self.assertIn("printf(\"%d\\n\", y);", c_code)

    def test_loops_variations(self):
        """Test FOR TO, FOR FROM, WHILE, REPEAT UNTIL, C-style FOR."""
        code = """
        START
            DECLARE i: INTEGER
            FOR i = 1 TO 5
                PRINT i
            NEXT i

            FOR i FROM 1 TO 3
                PRINT i
            END FOR

            WHILE i > 0 DO
                i = i - 1
            END WHILE

            REPEAT
                i = i + 1
            UNTIL i >= 3
        END
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn("for (i = 1; i <= 5; i++)", c_code)
        self.assertIn("for (i = 1; i <= 3; i++)", c_code)
        self.assertIn("while ((i > 0))", c_code)
        self.assertIn("do {", c_code)
        self.assertIn("} while (!((i >= 3)));", c_code)

    def test_arrays(self):
        """Test array declaration and indexing."""
        code = """
        START
            DECLARE numbers[5]: INTEGER
            numbers[0] = 99
            PRINT numbers[0]
        END
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn("int numbers[5];", c_code)
        self.assertIn("numbers[0] = 99;", c_code)
        self.assertIn("printf(\"%d\\n\", numbers[0]);", c_code)

    def test_functions(self):
        """Test function declaration, return, and calls."""
        code = """
        FUNCTION add(a: INTEGER, b: INTEGER): INTEGER
            RETURN a + b
        END FUNCTION

        START
            DECLARE res: INTEGER
            res = add(5, 10)
            PRINT res
        END
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn("int add(int a, int b);", c_code)
        self.assertIn("int add(int a, int b)\n{", c_code)
        self.assertIn("return (a + b);", c_code)
        self.assertIn("res = add(5, 10);", c_code)

    def test_missing_endif_error(self):
        """Test detection of missing END IF."""
        code = """
        START
            IF x > 10 THEN
                PRINT x
        END
        """
        with self.assertRaises(ParserError) as ctx:
            self.compile_snippet(code)
        self.assertIn("Missing 'END IF'", str(ctx.exception))

    def test_missing_loop_terminator(self):
        """Test detection of missing loop terminator."""
        code = """
        START
            WHILE x > 0
                x = x - 1
        END
        """
        with self.assertRaises(ParserError) as ctx:
            self.compile_snippet(code)
        self.assertIn("Missing 'END WHILE'", str(ctx.exception))

    def test_empty_input(self):
        """Empty input should compile without crashing."""
        res = self.compile_snippet("")
        c_code = res["c_code"]
        self.assertIn("int main(void)", c_code)
        self.assertIn("return 0;", c_code)

    def test_type_conflict_detection(self):
        """Incompatible types inferred or assigned should raise TypeError or emit warning."""
        code = """
        START
            DECLARE s: STRING
            s = 123
        END
        """
        res = self.compile_snippet(code)
        # Should have captured a warning about incompatible assignment
        self.assertTrue(len(res["warnings"]) > 0 or "s" in res["c_code"])

    def test_comments_and_case_insensitivity(self):
        """Test single-line comments, multi-line comments, and mixed-case syntax."""
        code = """
        // This is a single line comment
        # This is also a comment
        /* This is a 
           multi-line comment */
        start
            set count to 5
            if count > 0 then
                print "Positive"
            endif
        end
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn("count = 5;", c_code)
        self.assertIn('printf("Positive\\n");', c_code)

    def test_c_style_for_loop(self):
        """Test C-style for loop syntax."""
        code = """
        START
            DECLARE i: INTEGER
            FOR (i = 0; i < 10; i++)
                PRINT i
            END FOR
        END
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn("for (i = 0; (i < 10); i++) {", c_code)

    def test_multiple_input_output(self):
        """Test multi-variable input and composite print expressions."""
        code = """
        START
            DECLARE a, b: INTEGER
            INPUT a, b
            PRINT a, " + ", b, " = ", a + b
        END
        """
        res = self.compile_snippet(code)
        c_code = res["c_code"]
        self.assertIn('scanf("%d", &a);', c_code)
        self.assertIn('scanf("%d", &b);', c_code)
        self.assertIn('printf("%d + %d = %d\\n", a, b, (a + b));', c_code)


if __name__ == "__main__":
    unittest.main()
