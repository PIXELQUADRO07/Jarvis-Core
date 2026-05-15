import re
import math

def calculate(expression: str) -> str:
    """
    Evaluate a simple math expression.
    Supports basic operators: +, -, *, /, **, sqrt, sin, cos, etc.
    """
    try:
        # Remove dangerous characters
        if any(char in expression for char in [';', '__', 'import', 'exec', 'eval']):
            return "Unsafe expression."

        # Replace common functions
        expression = re.sub(r'\bsqrt\b', 'math.sqrt', expression)
        expression = re.sub(r'\bsin\b', 'math.sin', expression)
        expression = re.sub(r'\bcos\b', 'math.cos', expression)
        expression = re.sub(r'\btan\b', 'math.tan', expression)
        expression = re.sub(r'\blog\b', 'math.log', expression)
        expression = re.sub(r'\bexp\b', 'math.exp', expression)
        expression = re.sub(r'\bpi\b', 'math.pi', expression)
        expression = re.sub(r'\be\b', 'math.e', expression)

        # Valuta in un contesto sicuro
        result = eval(expression, {"__builtins__": None}, {"math": math})
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {str(e)}"