# POTALE_STOCK Test Suite

This directory contains the test suite for the POTALE_STOCK project.

## Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── pytest.ini               # Pytest configuration (in project root)
├── unit/                    # Unit tests (fast, isolated)
│   ├── entities/           # Domain entity tests
│   ├── services/           # Service layer tests
│   └── repositories/       # Repository tests
├── integration/            # Integration tests
└── fixtures/               # Shared test data
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-asyncio` - Async test support
- `pytest-mock` - Mocking utilities
- `faker` - Test data generation

### Run All Tests

```bash
pytest
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only repository tests
pytest -m repository

# Run only checker tests
pytest -m checker

# Run only entity tests
pytest -m entity
```

### Run Tests with Coverage

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# View coverage in browser
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Run Specific Test Files

```bash
# Run all Block1Detection entity tests
pytest tests/unit/entities/test_block1_detection.py

# Run specific test class
pytest tests/unit/entities/test_block1_detection.py::TestBlock1DetectionCreation

# Run specific test method
pytest tests/unit/entities/test_block1_detection.py::TestBlock1DetectionCreation::test_create_minimal_block1_detection
```

### Verbose Output

```bash
# Show detailed output
pytest -v

# Show extra test summary
pytest -ra

# Show local variables on failure
pytest --showlocals
```

### Stop on First Failure

```bash
pytest -x
```

## Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests that use database or external services
- `@pytest.mark.slow` - Tests that take > 1 second
- `@pytest.mark.checker` - Block checker tests
- `@pytest.mark.repository` - Repository tests
- `@pytest.mark.service` - Service layer tests
- `@pytest.mark.entity` - Entity/domain tests

## Writing Tests

### Test Naming Conventions

- Test files: `test_*.py` or `*_test.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Example Test Structure

```python
import pytest

@pytest.mark.unit
@pytest.mark.entity
class TestMyEntity:
    """Test suite for MyEntity"""

    def test_creation(self):
        """Test entity creation"""
        entity = MyEntity(...)
        assert entity.field == expected_value

    def test_validation(self):
        """Test entity validation"""
        with pytest.raises(ValueError):
            MyEntity(invalid_data)
```

### Using Fixtures

Shared fixtures are defined in `tests/conftest.py`:

```python
def test_with_fixture(sample_block1_detection):
    """Use a fixture from conftest.py"""
    detection = sample_block1_detection
    assert detection.ticker == "005930"
```

### Mocking

Use `unittest.mock` or `pytest-mock`:

```python
from unittest.mock import Mock

def test_with_mock(mock_stock_repository):
    """Use a mock repository"""
    mock_stock_repository.find_by_ticker.return_value = None
    result = service.process(mock_stock_repository)
    assert result is None
```

## Coverage Goals

- **Overall**: 80%+ coverage
- **Entities**: 90%+ coverage (critical business logic)
- **Repositories**: 85%+ coverage (data integrity)
- **Services**: 80%+ coverage
- **Infrastructure**: 70%+ coverage

## Continuous Integration

Tests should be run on every commit:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-report=xml
```

## Best Practices

1. **Fast Tests**: Keep unit tests < 100ms each
2. **Isolation**: Each test should be independent
3. **Clear Names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Follow AAA pattern
5. **One Assertion**: Focus on one thing per test (when possible)
6. **Use Fixtures**: Reuse common test data
7. **Mock External Dependencies**: Don't hit real databases/APIs in unit tests

## Common Issues

### Import Errors

If you get import errors, ensure `PYTHONPATH` includes the project root:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Unix
set PYTHONPATH=%PYTHONPATH%;%CD%  # Windows
```

Or use `pytest.ini` configuration (already set up).

### Database Tests

Integration tests use in-memory SQLite by default. No setup required.

For real database testing:
```python
@pytest.fixture
def real_db():
    db = DatabaseConnection(db_path="test_database.db")
    yield db
    # Cleanup
    os.remove("test_database.db")
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
