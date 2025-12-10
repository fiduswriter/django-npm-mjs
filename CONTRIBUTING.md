# Contributing to django-npm-mjs

Thank you for your interest in contributing to django-npm-mjs! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/django-npm-mjs.git
   cd django-npm-mjs
   ```
3. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip

### Setting Up Your Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install pre-commit hooks (optional but recommended):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Running Tests

### Quick Test Run

Run all tests with the test runner:

```bash
python runtests.py
```

### Using unittest

Run all tests:
```bash
python -m unittest discover npm_mjs/tests
```

Run specific test class:
```bash
python -m unittest npm_mjs.tests.test_json5_parser.TestJSON5Comments
```

Run specific test method:
```bash
python -m unittest npm_mjs.tests.test_json5_parser.TestJSON5Comments.test_single_line_comment_inline
```

### Using pytest

If you have pytest installed:

```bash
pytest -v
```

Run specific tests:
```bash
pytest -v -k "Comments"  # All comment-related tests
```

### Writing Tests

When adding new features or fixing bugs:

1. **Add tests first** (Test-Driven Development)
2. **Use descriptive test names** that explain what is being tested
3. **Add docstrings** to explain the test's purpose
4. **Test edge cases** and error conditions
5. **Add regression tests** for bug fixes

Example test:

```python
def test_new_feature(self):
    """Test that new feature handles X correctly."""
    content = '{ key: "value" }'
    result = parse_json5(content)
    self.assertEqual(result, {'key': 'value'})
```

### Test Organization

Tests are organized in `npm_mjs/tests/`:

- `test_json5_parser.py` - Tests for JSON5 parser functionality

When adding tests:
- Group related tests in the same test class
- Use clear, descriptive names
- Keep tests focused and isolated

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters (Black formatter default)
- Use meaningful variable and function names

### Pre-commit Hooks

The project uses pre-commit hooks to enforce code quality. Run manually with:

```bash
pre-commit run --all-files
```

### Docstrings

Use docstrings for all public modules, functions, classes, and methods:

```python
def parse_json5(content: str) -> Dict[str, Any]:
    """
    Parse JSON5 content and return a dictionary.

    Args:
        content: JSON5 string content

    Returns:
        Dictionary representation of the JSON5 content

    Raises:
        json.JSONDecodeError: If the content cannot be parsed
    """
```

### Type Hints

Use type hints for function signatures:

```python
from typing import Dict, Any

def my_function(name: str, count: int) -> Dict[str, Any]:
    return {"name": name, "count": count}
```

## Submitting Changes

### Commit Messages

Write clear, descriptive commit messages:

- Use the imperative mood ("Add feature" not "Added feature")
- First line: brief summary (50 chars or less)
- Leave a blank line
- Add detailed description if needed

Example:
```
Fix JSON5 parser handling of double slashes in strings

The parser was incorrectly treating // inside string literals as
comments, causing strings like "path//to//file" to be truncated.
This fix adds proper string boundary tracking to prevent comment
removal inside strings.

Fixes #123
```

### Pull Request Process

1. **Update tests**: Ensure all tests pass and add new tests for your changes
2. **Update documentation**: Update README.md or other docs as needed
3. **Run pre-commit**: Make sure pre-commit checks pass
4. **Create pull request**:
   - Provide a clear description of the changes
   - Reference any related issues
   - Explain why the change is needed

5. **Respond to feedback**: Address any review comments promptly

### Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] All tests pass (`python runtests.py`)
- [ ] New tests added for new features/bug fixes
- [ ] Code follows the project's style guidelines
- [ ] Documentation updated (if applicable)
- [ ] Pre-commit hooks pass
- [ ] Commit messages are clear and descriptive
- [ ] Branch is up to date with main

## Reporting Bugs

### Before Reporting

1. Check if the bug has already been reported in [Issues](https://github.com/fiduswriter/django-npm-mjs/issues)
2. Verify you're using the latest version
3. Try to reproduce the bug with a minimal example

### Bug Report Template

When reporting a bug, include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Minimal steps to reproduce the bug
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**:
   - Python version
   - Django version
   - Operating system
   - django-npm-mjs version
6. **Code sample**: Minimal code that reproduces the issue
7. **Error message**: Full error message and stack trace

Example:

```markdown
## Description
JSON5 parser fails when parsing strings with double slashes

## Steps to Reproduce
1. Create a package.json5 with: `{ path: "some//path" }`
2. Run `./manage.py transpile`

## Expected Behavior
Should parse successfully with path = "some//path"

## Actual Behavior
Error: Unterminated string starting at line 1

## Environment
- Python: 3.12
- Django: 5.0
- OS: Ubuntu 22.04
- django-npm-mjs: 3.2.1

## Code Sample
```python
from npm_mjs.json5_parser import parse_json5
content = '{ path: "some//path" }'
result = parse_json5(content)  # Fails here
```

## Error Message
```
json.decoder.JSONDecodeError: Unterminated string starting at: line 1 column 10 (char 9)
```
```

## Feature Requests

We welcome feature requests! When suggesting a new feature:

1. **Check existing issues** to see if it's already been suggested
2. **Explain the use case**: Why is this feature needed?
3. **Describe the solution**: How should it work?
4. **Consider alternatives**: Are there other ways to achieve this?
5. **Breaking changes**: Note if this would break existing functionality

## Development Guidelines

### JSON5 Parser Development

When modifying the JSON5 parser (`npm_mjs/json5_parser.py`):

1. **Maintain PyPy compatibility**: No C extensions
2. **Keep it simple**: The parser should be easy to understand
3. **Focus on package.json**: Prioritize features used in package.json files
4. **Add regression tests**: For every bug fix
5. **Update documentation**: Keep JSON5_PARSER_MIGRATION.md up to date

### Testing Philosophy

- **Test behavior, not implementation**: Tests should verify what the code does, not how it does it
- **Keep tests isolated**: Each test should be independent
- **Use realistic examples**: Test with actual use cases
- **Test error conditions**: Don't just test the happy path

### Performance Considerations

- Keep in mind that this is build-time processing, not runtime
- Optimize for correctness first, performance second
- Profile before optimizing

## Questions?

If you have questions:

1. Check the [README.md](README.md) for basic usage
2. Look at existing code and tests for examples
3. Open an issue for discussion

## License

By contributing, you agree that your contributions will be licensed under the LGPL-3.0-or-later license.

## Code of Conduct

Be respectful and constructive in all interactions. We want this to be a welcoming community for everyone.

Thank you for contributing to django-npm-mjs!
