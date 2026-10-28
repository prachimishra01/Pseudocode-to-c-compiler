"""
Twenty ready-to-use example programs for the Pseudocode to C Compiler.
Each example includes:
  - title
  - description
  - pseudocode
  - explanation of how the conversion works
"""

EXAMPLES = [
    {
        "id": "hello_world",
        "title": "1. Hello World",
        "category": "Basics",
        "description": "The fundamental first program printing a welcoming message.",
        "pseudocode": """// Hello World in Pseudocode
START
    OUTPUT "Hello, World!"
END""",
        "explanation": "Translates `OUTPUT` with a string literal into a standard C `printf(\"Hello, World!\\n\");` with standard I/O library `<stdio.h>`."
    },
    {
        "id": "addition_two_numbers",
        "title": "2. Addition of Two Numbers",
        "category": "Basics",
        "description": "Reads two integers from input, computes their sum, and displays the result.",
        "pseudocode": """START
    DECLARE a: INTEGER
    DECLARE b: INTEGER
    DECLARE sum: INTEGER

    INPUT a
    INPUT b
    sum = a + b

    PRINT "Sum is: ", sum
END""",
        "explanation": "Explicitly declares variables `a`, `b`, and `sum` as `int`, converts `INPUT` into `scanf(\"%d\", &var)`, computes the sum, and formats the result with `printf(\"Sum is: %d\\n\", sum);`."
    },
    {
        "id": "int_and_float",
        "title": "3. Integer and Floating-Point Variables",
        "category": "Data Types",
        "description": "Demonstrates distinct integer and floating-point data types with arithmetic.",
        "pseudocode": """START
    DECLARE count: INTEGER
    DECLARE price: FLOAT
    DECLARE total: FLOAT

    count = 5
    price = 19.99
    total = count * price

    PRINT "Count: ", count
    PRINT "Price: ", price
    PRINT "Total: ", total
END""",
        "explanation": "Generates `int count;` and `float price, total;`. Uses format specifier `%d` for integer and `%f` for float, avoiding hardcoding all types as int."
    },
    {
        "id": "even_or_odd",
        "title": "4. Even or Odd Number",
        "category": "Conditionals",
        "description": "Determines whether an input integer is even or odd using the modulo operator.",
        "pseudocode": """START
    DECLARE num: INTEGER
    INPUT num

    IF num % 2 == 0 THEN
        PRINT "The number is even."
    ELSE
        PRINT "The number is odd."
    END IF
END""",
        "explanation": "Translates the modulo operator `%` and relational equality `== 0`, generating standard C `if ((num % 2) == 0) { ... } else { ... }`."
    },
    {
        "id": "positive_negative_zero",
        "title": "5. Positive, Negative, or Zero",
        "category": "Conditionals",
        "description": "Classifies a number as positive, negative, or zero using multi-branch conditional statements.",
        "pseudocode": """START
    DECLARE n: INTEGER
    INPUT n

    IF n > 0 THEN
        PRINT "Positive number"
    ELSE IF n < 0 THEN
        PRINT "Negative number"
    ELSE
        PRINT "Zero"
    END IF
END""",
        "explanation": "Converts `IF ... ELSE IF ... ELSE` branches into clean `if (...) { ... } else if (...) { ... } else { ... }` with proper nesting."
    },
    {
        "id": "largest_two",
        "title": "6. Largest of Two Numbers",
        "category": "Conditionals",
        "description": "Compares two floating-point numbers and outputs the larger one.",
        "pseudocode": """START
    DECLARE x: REAL
    DECLARE y: REAL

    INPUT x
    INPUT y

    IF x >= y THEN
        PRINT "Largest is: ", x
    ELSE
        PRINT "Largest is: ", y
    END IF
END""",
        "explanation": "Maps pseudocode type `REAL` to C `double`, reads values with `scanf(\"%lf\", ...)` and prints them with `%lf`."
    },
    {
        "id": "largest_three",
        "title": "7. Largest of Three Numbers",
        "category": "Conditionals",
        "description": "Finds the maximum of three numbers using compound logical AND conditions.",
        "pseudocode": """START
    DECLARE a, b, c: INTEGER
    INPUT a, b, c

    IF a >= b AND a >= c THEN
        PRINT "Max is: ", a
    ELSE IF b >= a AND b >= c THEN
        PRINT "Max is: ", b
    ELSE
        PRINT "Max is: ", c
    END IF
END""",
        "explanation": "Translates logical `AND` into C logical operator `&&`, and groups multiple input variables into individual `scanf` calls."
    },
    {
        "id": "if_else_statements",
        "title": "8. IF-ELSE Statements",
        "category": "Conditionals",
        "description": "Checks an eligibility criterion for voting based on age.",
        "pseudocode": """START
    DECLARE age: INTEGER
    INPUT age

    IF age >= 18 THEN
        PRINT "Eligible to vote"
    ELSE
        PRINT "Not eligible to vote"
    END IF
END""",
        "explanation": "Demonstrates standard conditional syntax with `IF ... THEN` and `END IF`, mapped to standard C braces and semicolons."
    },
    {
        "id": "nested_if_else",
        "title": "9. Nested IF-ELSE",
        "category": "Conditionals",
        "description": "Demonstrates nested conditional blocks evaluating student marks and attendance.",
        "pseudocode": """START
    DECLARE marks: INTEGER
    DECLARE attendance: INTEGER

    INPUT marks
    INPUT attendance

    IF attendance >= 75 THEN
        IF marks >= 50 THEN
            PRINT "Passed with good attendance"
        ELSE
            PRINT "Failed exam despite good attendance"
        END IF
    ELSE
        PRINT "Disqualified due to low attendance"
    END IF
END""",
        "explanation": "Accurately manages nested indentation and block delimiters (`{}` in C), closing inner and outer `IF` blocks cleanly."
    },
    {
        "id": "for_loop",
        "title": "10. FOR Loops",
        "category": "Loops",
        "description": "Prints numbers from 1 to 10 with a pseudocode FOR loop.",
        "pseudocode": """START
    DECLARE i: INTEGER

    FOR i = 1 TO 10
        PRINT i
    NEXT i
END""",
        "explanation": "Translates `FOR i = 1 TO 10 ... NEXT i` into canonical C `for (i = 1; i <= 10; i++) { printf(\"%d\\n\", i); }`."
    },
    {
        "id": "while_loop",
        "title": "11. WHILE Loops",
        "category": "Loops",
        "description": "Computes powers of 2 less than 100 using a WHILE loop.",
        "pseudocode": """START
    DECLARE val: INTEGER
    val = 1

    WHILE val < 100 DO
        PRINT val
        val = val * 2
    END WHILE
END""",
        "explanation": "Converts `WHILE val < 100 DO ... END WHILE` into standard `while ((val < 100)) { ... }`."
    },
    {
        "id": "repeat_until_loop",
        "title": "12. REPEAT-UNTIL Loops",
        "category": "Loops",
        "description": "Decrements a counter in a post-test loop until it reaches zero.",
        "pseudocode": """START
    DECLARE countdown: INTEGER
    countdown = 5

    REPEAT
        PRINT countdown
        countdown = countdown - 1
    UNTIL countdown <= 0
END""",
        "explanation": "Translates post-test `REPEAT ... UNTIL condition` into standard C `do { ... } while (!(condition));` where the loop exits when the condition becomes true."
    },
    {
        "id": "multiplication_table",
        "title": "13. Multiplication Tables",
        "category": "Loops",
        "description": "Generates a multiplication table for a chosen number.",
        "pseudocode": """START
    DECLARE num: INTEGER
    DECLARE i: INTEGER

    INPUT num

    FOR i = 1 TO 10
        PRINT num, " x ", i, " = ", num * i
    NEXT i
END""",
        "explanation": "Combines variables, string literals, and arithmetic expressions inside `PRINT`, synthesizing a multi-argument `printf(\"%d x %d = %d\\n\", num, i, (num * i));`."
    },
    {
        "id": "factorial",
        "title": "14. Factorial Calculation",
        "category": "Algorithms",
        "description": "Calculates the factorial of an integer using an iterative loop.",
        "pseudocode": """START
    DECLARE n: INTEGER
    DECLARE fact: LONG
    DECLARE i: INTEGER

    INPUT n
    fact = 1

    FOR i = 1 TO n
        fact = fact * i
    NEXT i

    PRINT "Factorial is: ", fact
END""",
        "explanation": "Uses `LONG` data type mapped to C `long` with `%ld` format specifier to prevent integer overflow for larger values."
    },
    {
        "id": "fibonacci",
        "title": "15. Fibonacci Series",
        "category": "Algorithms",
        "description": "Generates the first N terms of the Fibonacci sequence.",
        "pseudocode": """START
    DECLARE n, first, second, next_term, i: INTEGER
    first = 0
    second = 1

    INPUT n
    PRINT "Fibonacci Series:"

    FOR i = 1 TO n
        PRINT first
        next_term = first + second
        first = second
        second = next_term
    NEXT i
END""",
        "explanation": "Demonstrates multiple variable declarations, sequential updates, and iterative sequence calculation in valid C."
    },
    {
        "id": "array_operations",
        "title": "16. Array Operations",
        "category": "Arrays",
        "description": "Initializes an array, populates values via a loop, and calculates their sum.",
        "pseudocode": """START
    DECLARE numbers[5]: INTEGER
    DECLARE i: INTEGER
    DECLARE total: INTEGER

    total = 0

    FOR i = 0 TO 4
        numbers[i] = (i + 1) * 10
        total = total + numbers[i]
    NEXT i

    PRINT "Total sum of array: ", total
END""",
        "explanation": "Translates `DECLARE numbers[5]: INTEGER` to `int numbers[5];` and handles zero-indexed array access `numbers[i]`."
    },
    {
        "id": "functions_and_returns",
        "title": "17. Functions and Return Values",
        "category": "Functions",
        "description": "Defines an add function and calls it from the main program.",
        "pseudocode": """FUNCTION calculateSquare(n: INTEGER): INTEGER
    RETURN n * n
END FUNCTION

START
    DECLARE num: INTEGER
    DECLARE result: INTEGER

    INPUT num
    result = calculateSquare(num)
    PRINT "Square is: ", result
END""",
        "explanation": "Declares function prototype and definition `int calculateSquare(int n)` before `main(void)`, emits return statement, and calls function in expression."
    },
    {
        "id": "string_operations",
        "title": "18. String Operations",
        "category": "Data Types",
        "description": "Declares and prints strings safely in standard C.",
        "pseudocode": """START
    DECLARE greeting: STRING
    DECLARE name: STRING

    greeting = "Hello"
    name = "Prachi"

    PRINT greeting, ", ", name, "!"
END""",
        "explanation": "Translates pseudocode `STRING` into C `char[100]`, includes `<string.h>`, uses `snprintf` for safe initialization, and outputs using `%s`."
    },
    {
        "id": "boolean_variables",
        "title": "19. Boolean Variables",
        "category": "Data Types",
        "description": "Demonstrates boolean variables, literal assignment, and condition checks.",
        "pseudocode": """START
    DECLARE hasAccess: BOOLEAN
    DECLARE isAdmin: BOOLEAN

    hasAccess = true
    isAdmin = false

    IF hasAccess AND NOT isAdmin THEN
        PRINT "Standard user access granted."
    END IF
END""",
        "explanation": "Includes `<stdbool.h>`, generates `bool hasAccess, isAdmin;`, maps boolean literals `true`/`false`, and translates `AND NOT` to `&& !(...)`."
    },
    {
        "id": "mixed_types_expressions",
        "title": "20. Mixed Data Types and Expressions",
        "category": "Data Types",
        "description": "Demonstrates mixed types: integer, float, char, string, and bool working together.",
        "pseudocode": """START
    DECLARE age: INTEGER
    DECLARE rating: FLOAT
    DECLARE section: CHAR
    DECLARE isEnrolled: BOOL

    age = 20
    rating = 4.85
    section = 'A'
    isEnrolled = true

    PRINT "Age: ", age
    PRINT "Rating: ", rating
    PRINT "Section: ", section
    PRINT "Enrolled: ", isEnrolled
END""",
        "explanation": "Showcases multi-type inference and declarations (`int`, `float`, `char`, `bool`), generating clean C with `<stdbool.h>` and correct format specifiers for each type."
    }
]
