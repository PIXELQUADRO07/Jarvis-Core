import ast
import math
import operator
from typing import Any

# Allowed binary operators
_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

# Allowed unary operators
_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

# Allowed math functions (safe subset)
_MATH_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "log": math.log,
    "ln": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
    "ceil": math.ceil,
    "floor": math.floor,
}

def _safe_eval_node(node: ast.AST) -> Any:
    """Recursively evaluate an AST node using only whitelisted operations."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float, complex)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BINOPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        return _BINOPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARYOPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _safe_eval_node(node.operand)
        return _UNARYOPS[op_type](operand)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only simple function calls are allowed")
        fname = node.func.id
        if fname not in _MATH_FUNCS:
            raise ValueError(f"Unknown function: {fname}")
        func = _MATH_FUNCS[fname]
        args = [_safe_eval_node(a) for a in node.args]
        return func(*args)
    if isinstance(node, ast.Name):
        name = node.id
        if name in _MATH_FUNCS:
            val = _MATH_FUNCS[name]
            if isinstance(val, (int, float)):
                return val
        raise ValueError(f"Unknown variable: {name}")
    raise ValueError(f"Unsupported expression type: {type(node).__name__}")

def calculate(expression: str) -> str:
    """
    Evaluate a math expression safely using AST.
    """
    # Support ^ as the power operator
    expression = expression.replace("^", "**")
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval_node(tree.body)
        return f"Result: {result}"
    except ZeroDivisionError:
        return "Calculation error: division by zero"
    except Exception as e:
        return f"Calculation error: {str(e)}"
