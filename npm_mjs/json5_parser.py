"""
JSON5 parser using regex and native JSON parsing.
Compatible with PyPy and doesn't require external dependencies.

This parser handles:
- Single-line comments (//)
- Multi-line comments (/* */)
- Unquoted object keys
- Trailing commas
- Single-quoted strings
"""

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def parse_json5(content: str, debug: bool = False) -> dict[str, Any]:
    """
    Parse JSON5 content and return a dictionary.

    Args:
        content: JSON5 string content
        debug: If True, print debug output on parse errors (default: False)

    Returns:
        Dictionary representation of the JSON5 content

    Raises:
        json.JSONDecodeError: If the content cannot be parsed
    """
    # Process the content in a single pass to:
    # 1. Remove comments (but not // or /* */ inside strings)
    # 2. Convert single-quoted strings to double-quoted strings
    # 3. Preserve all string content correctly

    def process_content(text):
        """Process JSON5 content: remove comments and convert quotes."""
        result = []
        i = 0

        while i < len(text):
            char = text[i]

            # Check for double-quoted strings - preserve as-is
            if char == '"':
                # Copy the entire double-quoted string, handling escapes
                result.append(char)
                i += 1
                while i < len(text):
                    char = text[i]
                    result.append(char)
                    if char == "\\" and i + 1 < len(text):
                        # Copy the escaped character
                        i += 1
                        result.append(text[i])
                        i += 1
                    elif char == '"':
                        # End of string
                        i += 1
                        break
                    else:
                        i += 1
                continue

            # Check for single-quoted strings - convert to double quotes
            if char == "'":
                # Start of single-quoted string
                result.append('"')  # Convert to double quote
                i += 1
                while i < len(text):
                    char = text[i]
                    if char == "\\" and i + 1 < len(text):
                        # Handle escape sequences
                        next_char = text[i + 1]
                        if next_char == "'":
                            # Escaped single quote in single-quoted string
                            # In double-quoted string, we don't need to escape it
                            result.append("'")
                            i += 2
                        else:
                            # Other escape sequences - preserve
                            result.append(char)
                            i += 1
                            result.append(text[i])
                            i += 1
                    elif char == "'":
                        # End of single-quoted string
                        result.append('"')  # Convert to double quote
                        i += 1
                        break
                    elif char == '"':
                        # Double quote inside single-quoted string - escape it
                        result.append('\\"')
                        i += 1
                    else:
                        result.append(char)
                        i += 1
                continue

            # Check for multi-line comment start
            if i + 1 < len(text) and text[i : i + 2] == "/*":  # noqa: E203
                # Find the end of the comment
                end = text.find("*/", i + 2)
                if end != -1:
                    # Skip the entire comment, but preserve newlines for line number accuracy
                    comment_text = text[i : end + 2]  # noqa: E203
                    newlines = comment_text.count("\n")
                    result.append("\n" * newlines)
                    i = end + 2
                else:
                    # Unclosed comment, skip to end
                    i = len(text)
                continue

            # Check for single-line comment
            # Make sure it's not part of a URL (http:// or https://)
            if i + 1 < len(text) and text[i : i + 2] == "//":  # noqa: E203
                # Check if this is part of a URL
                if i > 0 and text[i - 1] == ":":
                    # This is likely a URL, keep it
                    result.append(char)
                    i += 1
                else:
                    # This is a comment - skip to end of line
                    while i < len(text) and text[i] != "\n":
                        i += 1
                    # Keep the newline
                    if i < len(text):
                        result.append("\n")
                        i += 1
                continue

            # Regular character
            result.append(char)
            i += 1

        return "".join(result)

    content = process_content(content)

    # Convert unquoted keys to quoted keys
    # Match: word characters followed by colon (not already quoted)
    # This regex looks for keys at the start of a line or after { or ,
    content = re.sub(r"([\{\,]\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:", r'\1"\2":', content)

    # Also handle keys at the beginning of the content
    content = re.sub(
        r"^(\s*)([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:",
        r'\1"\2":',
        content,
        flags=re.MULTILINE,
    )

    # Remove trailing commas before closing braces/brackets
    content = re.sub(r",(\s*[}\]])", r"\1", content)

    # Parse as regular JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # Log debug information if requested
        if debug:
            logger.error("\n" + "=" * 80)
            logger.error("JSON5 Parser Error - Processed content that failed to parse:")
            logger.error("=" * 80)
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                marker = " --> " if i == e.lineno else "     "
                logger.error(f"{marker}{i:3}: {line}")
            logger.error("=" * 80)
            logger.error(f"Error at line {e.lineno}, column {e.colno}: {e.msg}")
            logger.error("=" * 80 + "\n")
        raise


def encode_json5(data: dict[str, Any], indent: int = 2) -> str:
    """
    Encode dictionary to JSON5 format (actually just JSON with nice formatting).

    Args:
        data: Dictionary to encode
        indent: Number of spaces for indentation

    Returns:
        JSON5-formatted string
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def load_json5(file_path: str, debug: bool = False) -> dict[str, Any]:
    """
    Load and parse a JSON5 file.

    Args:
        file_path: Path to JSON5 file
        debug: If True, print debug output on parse errors (default: False)

    Returns:
        Dictionary representation of the JSON5 content
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    return parse_json5(content, debug=debug)


def dump_json5(data: dict[str, Any], file_path: str, indent: int = 2):
    """
    Dump dictionary to a JSON5 file (as regular JSON).

    Args:
        data: Dictionary to dump
        file_path: Path to output file
        indent: Number of spaces for indentation
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
