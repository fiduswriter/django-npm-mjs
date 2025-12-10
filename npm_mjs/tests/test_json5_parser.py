"""
Comprehensive test suite for the JSON5 parser.

Tests cover:
- Comment removal (single-line and multi-line)
- Quote conversion (single to double)
- Unquoted keys
- Trailing commas
- Edge cases with strings containing special characters
- URL preservation in strings
- Mixed quote types
- Escape sequences
- Complex realistic scenarios
"""

import json
import os
import tempfile
import unittest

from npm_mjs.json5_parser import dump_json5
from npm_mjs.json5_parser import encode_json5
from npm_mjs.json5_parser import load_json5
from npm_mjs.json5_parser import parse_json5


class TestJSON5ParserBasics(unittest.TestCase):
    """Test basic JSON5 parsing functionality."""

    def test_basic_unquoted_key(self):
        """Test parsing unquoted object keys."""
        content = '{ key: "value" }'
        result = parse_json5(content)
        self.assertEqual(result, {"key": "value"})

    def test_quoted_key_with_special_chars(self):
        """Test parsing keys with special characters (already quoted)."""
        content = '{ "@rspack/core": "1.6.7" }'
        result = parse_json5(content)
        self.assertEqual(result, {"@rspack/core": "1.6.7"})

    def test_standard_json(self):
        """Test that standard JSON still works."""
        content = '{"name": "test", "version": "1.0.0"}'
        result = parse_json5(content)
        self.assertEqual(result, {"name": "test", "version": "1.0.0"})

    def test_nested_objects(self):
        """Test parsing nested objects."""
        content = """
        {
          dependencies: {
            "@rspack/core": "1.6.7",
            "other": "1.0.0"
          }
        }
        """
        result = parse_json5(content)
        self.assertEqual(
            result,
            {"dependencies": {"@rspack/core": "1.6.7", "other": "1.0.0"}},
        )

    def test_arrays(self):
        """Test parsing arrays."""
        content = '{ items: ["a", "b", "c"] }'
        result = parse_json5(content)
        self.assertEqual(result, {"items": ["a", "b", "c"]})

    def test_mixed_types(self):
        """Test parsing various JSON types."""
        content = """
        {
          string: "text",
          number: 42,
          float: 3.14,
          bool_true: true,
          bool_false: false,
          null_value: null
        }
        """
        result = parse_json5(content)
        self.assertEqual(
            result,
            {
                "string": "text",
                "number": 42,
                "float": 3.14,
                "bool_true": True,
                "bool_false": False,
                "null_value": None,
            },
        )


class TestJSON5Comments(unittest.TestCase):
    """Test comment removal functionality."""

    def test_single_line_comment_start(self):
        """Test single-line comment at the start."""
        content = """
        // This is a comment
        { key: "value" }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"key": "value"})

    def test_single_line_comment_inline(self):
        """Test single-line comment after a value."""
        content = """
        {
          key: "value", // This is a comment
          other: "value2"
        }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"key": "value", "other": "value2"})

    def test_multi_line_comment(self):
        """Test multi-line comment removal."""
        content = """
        /* This is a
           multi-line comment */
        { key: "value" }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"key": "value"})

    def test_multi_line_comment_inline(self):
        """Test inline multi-line comment."""
        content = """
        {
          /* comment */ key: "value"
        }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"key": "value"})

    def test_comment_with_url(self):
        """Test that URLs in comments don't break parsing."""
        content = """
        {
          // See https://example.com for more info
          name: "test",
          url: "https://github.com/user/repo" // GitHub repo
        }
        """
        result = parse_json5(content)
        self.assertEqual(
            result,
            {"name": "test", "url": "https://github.com/user/repo"},
        )

    def test_multi_line_comment_with_slashes(self):
        """Test multi-line comment containing // inside."""
        content = """
        {
          /* This is a comment with https://example.com
             and some // slashes too */
          name: "test"
        }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"name": "test"})


class TestJSON5StringsWithSlashes(unittest.TestCase):
    """Test that // inside strings is preserved correctly."""

    def test_double_slashes_in_string(self):
        """Test string with // that are not comments."""
        content = '{ path: "some//path//with//slashes" }'
        result = parse_json5(content)
        self.assertEqual(result, {"path": "some//path//with//slashes"})

    def test_url_in_string(self):
        """Test URL preservation in strings."""
        content = """
        {
          url: "https://example.com",
          homepage: "https://github.com/user/repo"
        }
        """
        result = parse_json5(content)
        self.assertEqual(
            result,
            {"url": "https://example.com", "homepage": "https://github.com/user/repo"},
        )

    def test_comment_marker_in_string(self):
        """Test that // in string is not treated as comment."""
        content = '{ comment: "This is not a // comment" }'
        result = parse_json5(content)
        self.assertEqual(result, {"comment": "This is not a // comment"})

    def test_mixed_slashes(self):
        """Test various slash patterns in strings."""
        content = """
        {
          single: "a/b/c",
          double: "a//b//c",
          url: "http://example.com",
          path: "C://Users//test"
        }
        """
        result = parse_json5(content)
        self.assertEqual(
            result,
            {
                "single": "a/b/c",
                "double": "a//b//c",
                "url": "http://example.com",
                "path": "C://Users//test",
            },
        )


class TestJSON5Quotes(unittest.TestCase):
    """Test single and double quote handling."""

    def test_single_quoted_string(self):
        """Test single-quoted string conversion."""
        content = "{ key: 'value' }"
        result = parse_json5(content)
        self.assertEqual(result, {"key": "value"})

    def test_single_quotes_with_double_inside(self):
        """Test single-quoted string containing double quotes."""
        content = "{ single: 'value with \"quotes\"' }"
        result = parse_json5(content)
        self.assertEqual(result, {"single": 'value with "quotes"'})

    def test_double_quotes_with_single_inside(self):
        """Test double-quoted string containing single quotes."""
        content = "{ double: \"value with 'quotes'\" }"
        result = parse_json5(content)
        self.assertEqual(result, {"double": "value with 'quotes'"})

    def test_mixed_quote_types(self):
        """Test mixing single and double quotes."""
        content = """
        {
          single: 'value1',
          double: "value2",
          mixed1: 'has "double" inside',
          mixed2: "has 'single' inside"
        }
        """
        result = parse_json5(content)
        self.assertEqual(
            result,
            {
                "single": "value1",
                "double": "value2",
                "mixed1": 'has "double" inside',
                "mixed2": "has 'single' inside",
            },
        )

    def test_url_with_single_quotes(self):
        """Test URL in single-quoted string."""
        content = "{ url: 'https://example.com' }"
        result = parse_json5(content)
        self.assertEqual(result, {"url": "https://example.com"})


class TestJSON5EscapeSequences(unittest.TestCase):
    """Test escape sequence handling."""

    def test_escaped_double_quotes(self):
        """Test escaped double quotes in strings."""
        content = r'{ message: "He said \"hello\"" }'
        result = parse_json5(content)
        self.assertEqual(result, {"message": 'He said "hello"'})

    def test_escaped_backslash(self):
        """Test escaped backslashes."""
        content = r'{ path: "C:\\Users\\test\\path" }'
        result = parse_json5(content)
        self.assertEqual(result, {"path": r"C:\Users\test\path"})

    def test_escaped_newline(self):
        """Test escaped newline character."""
        content = r'{ text: "line1\nline2" }'
        result = parse_json5(content)
        self.assertEqual(result, {"text": "line1\nline2"})

    def test_escaped_tab(self):
        """Test escaped tab character."""
        content = r'{ text: "col1\tcol2" }'
        result = parse_json5(content)
        self.assertEqual(result, {"text": "col1\tcol2"})

    def test_mixed_escapes_and_slashes(self):
        """Test combination of escapes and slashes."""
        content = r'{ message: "He said \"hello // world\"" }'
        result = parse_json5(content)
        self.assertEqual(result, {"message": 'He said "hello // world"'})


class TestJSON5TrailingCommas(unittest.TestCase):
    """Test trailing comma handling."""

    def test_trailing_comma_object(self):
        """Test trailing comma in object."""
        content = """
        {
          key1: "value1",
          key2: "value2",
        }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})

    def test_trailing_comma_array(self):
        """Test trailing comma in array."""
        content = """
        {
          items: [
            "item1",
            "item2",
          ]
        }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"items": ["item1", "item2"]})

    def test_trailing_comma_nested(self):
        """Test trailing commas in nested structures."""
        content = """
        {
          obj: {
            key: "value",
          },
          arr: ["a", "b",],
        }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"obj": {"key": "value"}, "arr": ["a", "b"]})

    def test_multiple_trailing_commas(self):
        """Test multiple trailing commas in same structure."""
        content = """
        {
          a: "1",
          b: "2",
          c: "3",
        }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"a": "1", "b": "2", "c": "3"})


class TestJSON5ComplexScenarios(unittest.TestCase):
    """Test complex realistic scenarios."""

    def test_package_json5_example(self):
        """Test a realistic package.json5 file."""
        content = """
        // Package configuration
        {
          name: "my-package",
          version: "1.0.0",
          description: "A package with // in description",
          // Repository info
          repository: {
            type: "git",
            url: "https://github.com/user/repo.git" // Main repo
          },
          scripts: {
            test: "echo \\"test\\"",
            build: "npm run compile"
          },
          dependencies: {
            "@org/package": "^1.0.0",
            "another": "2.0.0", // Latest version
          },
          /* Multi-line comment
             with various content
             including https://example.com
             and // comment markers */
          author: "John Doe"
        }
        """
        result = parse_json5(content)
        self.assertEqual(result["name"], "my-package")
        self.assertEqual(result["version"], "1.0.0")
        self.assertEqual(result["description"], "A package with // in description")
        self.assertEqual(
            result["repository"]["url"],
            "https://github.com/user/repo.git",
        )
        self.assertEqual(result["scripts"]["test"], 'echo "test"')
        self.assertEqual(result["dependencies"]["@org/package"], "^1.0.0")
        self.assertEqual(result["author"], "John Doe")

    def test_npm_mjs_package_json5(self):
        """Test the actual package.json5 from this project."""
        content = """
        // Django-npm-mjs will combine this file with package.json files in other installed
        // apps before executing npm commands. Different from a regular package.json, comments
        // are allowed in this file.
        {
          description: "Install dependencies for ES6 transpilation",
          private: true,
          dependencies: {
            "@rspack/core": "1.6.7",
            "@rspack/cli": "1.6.7"
          },
        }
        """
        result = parse_json5(content)
        self.assertEqual(
            result["description"],
            "Install dependencies for ES6 transpilation",
        )
        self.assertTrue(result["private"])
        self.assertEqual(result["dependencies"]["@rspack/core"], "1.6.7")
        self.assertEqual(result["dependencies"]["@rspack/cli"], "1.6.7")

    def test_long_description_line(self):
        """Test parsing with a very long description (regression test for char 178 error)."""
        long_desc = (
            "This is a very long description that should push us past "
            "character 178 when combined with the other content"
        )
        content = f"""
        {{
          name: "test-package",
          version: "1.0.0",
          description: "{long_desc}",
          author: "Test Author",
          dependencies: {{
            "package1": "^1.0.0"
          }}
        }}
        """
        result = parse_json5(content)
        self.assertEqual(result["name"], "test-package")
        self.assertIn("very long description", result["description"])

    def test_inline_objects_and_arrays(self):
        """Test compact inline notation."""
        content = """
        {
          version: "1.0.0",
          engines: { node: ">=14.0.0", npm: ">=6.0.0" },
          keywords: ["django", "npm", "es6"],
          main: "index.js"
        }
        """
        result = parse_json5(content)
        self.assertEqual(result["engines"]["node"], ">=14.0.0")
        self.assertEqual(result["keywords"], ["django", "npm", "es6"])

    def test_empty_structures(self):
        """Test empty objects and arrays."""
        content = """
        {
          empty_obj: {},
          empty_arr: [],
          obj_with_empty: { nested: {} },
          arr_with_empty: [[]]
        }
        """
        result = parse_json5(content)
        self.assertEqual(result["empty_obj"], {})
        self.assertEqual(result["empty_arr"], [])
        self.assertEqual(result["obj_with_empty"]["nested"], {})
        self.assertEqual(result["arr_with_empty"], [[]])


class TestJSON5EdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def test_comment_at_end_of_file(self):
        """Test comment at the very end."""
        content = """
        { key: "value" }
        // Final comment
        """
        result = parse_json5(content)
        self.assertEqual(result, {"key": "value"})

    def test_multiple_keys_one_line(self):
        """Test multiple keys on a single line."""
        content = '{ key1: "value1", key2: "value2", key3: "value3" }'
        result = parse_json5(content)
        self.assertEqual(result, {"key1": "value1", "key2": "value2", "key3": "value3"})

    def test_whitespace_variations(self):
        """Test various whitespace patterns."""
        content = """
        {
          key1  :  "value1"  ,
          key2:"value2",
          key3 : "value3"
        }
        """
        result = parse_json5(content)
        self.assertEqual(result, {"key1": "value1", "key2": "value2", "key3": "value3"})

    def test_unicode_strings(self):
        """Test Unicode content in strings."""
        content = '{ text: "Hello 世界 🌍" }'
        result = parse_json5(content)
        self.assertEqual(result, {"text": "Hello 世界 🌍"})

    def test_numbers_with_underscores_not_supported(self):
        """Test that number separators are handled (pass through to JSON parser)."""
        # JSON5 supports underscores in numbers, but Python's json doesn't
        # Our parser just passes through, so this will fail in json.loads
        content = "{ number: 1_000_000 }"
        with self.assertRaises(json.JSONDecodeError):
            parse_json5(content)

    def test_glob_patterns(self):
        """Test glob patterns often found in package.json."""
        content = """
        {
          files: ["src/**/*.js", "dist/**/*.mjs"],
          pattern: "**/*.test.js"
        }
        """
        result = parse_json5(content)
        self.assertEqual(result["files"], ["src/**/*.js", "dist/**/*.mjs"])
        self.assertEqual(result["pattern"], "**/*.test.js")


class TestJSON5FileOperations(unittest.TestCase):
    """Test file loading and saving operations."""

    def test_load_json5_file(self):
        """Test loading a JSON5 file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json5", delete=False) as f:
            f.write('{ key: "value", number: 42 }')
            temp_path = f.name

        try:
            result = load_json5(temp_path)
            self.assertEqual(result, {"key": "value", "number": 42})
        finally:
            os.unlink(temp_path)

    def test_dump_json5_file(self):
        """Test dumping data to a JSON file."""
        data = {"key": "value", "number": 42}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            dump_json5(data, temp_path)

            # Read back and verify
            with open(temp_path) as f:
                content = f.read()
                result = json.loads(content)

            self.assertEqual(result, data)
        finally:
            os.unlink(temp_path)

    def test_encode_json5(self):
        """Test encoding data to JSON string."""
        data = {"key": "value", "nested": {"inner": "data"}}
        result = encode_json5(data)

        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed, data)

        # Should be formatted with indentation
        self.assertIn("\n", result)
        self.assertIn("  ", result)


class TestJSON5ErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""

    def test_invalid_json_after_processing(self):
        """Test that invalid JSON raises appropriate error."""
        content = '{ key: "value", }'  # Trailing comma before }
        # This should actually work due to our trailing comma removal
        result = parse_json5(content)
        self.assertEqual(result, {"key": "value"})

    def test_unclosed_string(self):
        """Test that unclosed string raises error."""
        content = '{ key: "value }'
        with self.assertRaises(json.JSONDecodeError):
            parse_json5(content)

    def test_unclosed_object(self):
        """Test that unclosed object raises error."""
        content = '{ key: "value"'
        with self.assertRaises(json.JSONDecodeError):
            parse_json5(content)

    def test_unclosed_array(self):
        """Test that unclosed array raises error."""
        content = '{ arr: ["item1", "item2" }'
        with self.assertRaises(json.JSONDecodeError):
            parse_json5(content)

    def test_empty_string(self):
        """Test parsing empty string."""
        with self.assertRaises(json.JSONDecodeError):
            parse_json5("")

    def test_only_comment(self):
        """Test parsing file with only comments."""
        content = "// Just a comment"
        with self.assertRaises(json.JSONDecodeError):
            parse_json5(content)


if __name__ == "__main__":
    unittest.main()
