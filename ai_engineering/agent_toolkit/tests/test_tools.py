import unittest

from agent.tools import ToolCall, ToolError, ToolRegistry, tool


@tool
def add(a: int, b: int) -> int:
    """Return a + b."""
    return a + b


@tool
def raise_domain() -> str:
    """Always raises a ToolError to exercise the error path."""
    raise ToolError("nope")


class TestToolRegistry(unittest.TestCase):
    def setUp(self):
        self.reg = ToolRegistry()
        self.reg.register_many([add, raise_domain])

    def test_specs_include_typed_parameters(self):
        spec = next(s for s in self.reg.specs() if s["function"]["name"] == "add")
        params = spec["function"]["parameters"]
        self.assertEqual(params["properties"]["a"]["type"], "integer")
        self.assertEqual(params["properties"]["b"]["type"], "integer")
        self.assertEqual(sorted(params["required"]), ["a", "b"])

    def test_call_success(self):
        result = self.reg.call(ToolCall(name="add", arguments={"a": 2, "b": 3}))
        self.assertTrue(result.ok)
        self.assertEqual(result.output, 5)

    def test_call_unknown_tool(self):
        result = self.reg.call(ToolCall(name="missing", arguments={}))
        self.assertFalse(result.ok)
        self.assertIn("unknown tool", result.error)

    def test_call_bad_args(self):
        result = self.reg.call(ToolCall(name="add", arguments={"a": 1}))
        self.assertFalse(result.ok)
        self.assertIn("bad arguments", result.error)

    def test_tool_error_propagates_as_failure(self):
        result = self.reg.call(ToolCall(name="raise_domain", arguments={}))
        self.assertFalse(result.ok)
        self.assertEqual(result.error, "nope")


class TestBuiltinTools(unittest.TestCase):
    def test_calculator_basic(self):
        from builtin_tools import calculator
        self.assertEqual(calculator("2 + 3 * 4"), 14.0)

    def test_calculator_precedence_and_parens(self):
        from builtin_tools import calculator
        self.assertEqual(calculator("(2 + 3) * 4"), 20.0)
        self.assertEqual(calculator("2 ** 3"), 8.0)
        self.assertEqual(calculator("-5 + 2"), -3.0)

    def test_calculator_allows_whitelisted_functions_and_constants(self):
        from builtin_tools import calculator
        self.assertEqual(calculator("sqrt(16)"), 4.0)
        self.assertAlmostEqual(calculator("log(e)"), 1.0)

    def test_calculator_rejects_unsafe(self):
        from builtin_tools import calculator
        with self.assertRaises(ToolError):
            calculator("__import__('os').system('echo hi')")

    def test_calculator_rejects_attribute_and_unknown_names(self):
        from builtin_tools import calculator
        for expr in ("(1).__class__", "os.getcwd()", "unknownfn(3)", "x + 1"):
            with self.assertRaises(ToolError):
                calculator(expr)


if __name__ == "__main__":
    unittest.main()
