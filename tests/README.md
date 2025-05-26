# Testing Guide for TrafaPy

This document provides comprehensive information about testing the TrafaPy library.

## 📋 Overview

TrafaPy has a comprehensive test suite that includes:

- **Unit Tests**: Test individual components in isolation using mocks (53 tests)
- **Integration Tests**: Test real API interactions (use sparingly)
- **Performance Tests**: Test caching and performance optimizations
- **Error Handling Tests**: Test edge cases and error scenarios
- **Real-World Usage Tests**: Test realistic workflows and patterns

## 📁 Test Structure

```
tests/
├── __init__.py                 # Makes tests a Python package
├── conftest.py                 # Shared test fixtures and configuration
├── test_trafapy.py            # Core functionality tests (25 tests)
├── test_convenience.py         # Advanced features tests (28 tests)
└── run_tests.py               # Custom test runner script
```

## 🚀 Quick Start

### Install Test Dependencies

```bash
# Essential test dependencies
pip install pytest pytest-cov pytest-mock

# Install your package in development mode
pip install -e .

# Optional: Install all development dependencies
pip install -r requirements-test.txt
```

### Run Basic Tests

```bash
# Run all unit tests (recommended for development)
pytest -m "not integration" -v

# Using the custom test runner
python tests/run_tests.py --unit --verbose

# Run with coverage reporting
pytest -m "not integration" --cov=trafapy --cov-report=term-missing
```

## 🧪 Test Categories

### Unit Tests (Recommended for Regular Use)

Unit tests are fast, reliable, and don't require network access. They use mocking to simulate API responses.

```bash
# Run only unit tests
pytest -m "not integration" -v

# Run specific test categories
pytest -k "cache" -v          # Cache-related tests
pytest -k "client" -v         # Client functionality tests
pytest -k "query" -v          # Query building tests
```

**What they test:**
- Query building logic and parameter handling
- Data processing and DataFrame conversion
- Cache functionality (save, retrieve, expire)
- Error handling and edge cases
- Utility and convenience functions
- Mock API response processing

**Expected results:**
- ✅ All tests should pass
- ⚡ Complete in under 10 seconds
- 🔒 No network requests to external APIs

### Integration Tests (Use Sparingly)

Integration tests hit the real Trafikanalys API and should be used carefully to avoid rate limiting.

```bash
# Run integration tests (use sparingly!)
pytest -m integration -v

# Run with the test runner
python tests/run_tests.py --integration
```

**What they test:**
- Real API connectivity and authentication
- Actual data retrieval and format validation
- Current API response structure

⚠️ **Important Notes:**
- May fail due to network issues, API downtime, or rate limiting
- Should not be run frequently during development
- Failures don't necessarily indicate code problems
- Use caching when running to minimize API calls

### Performance Tests

Test caching efficiency, memory usage, and concurrent access:

```bash
# Run performance-related tests
pytest -k "performance or cache" -v

# Run tests for large datasets
pytest -k "large_dataset" -v
```

## ⚙️ Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
markers =
    integration: marks tests as integration tests (may hit real API)
    slow: marks tests as slow running tests
    unit: marks tests as unit tests
```

### Custom Markers

- `@pytest.mark.integration`: Tests that make real API calls
- `@pytest.mark.slow`: Tests that take significant time (>2 seconds)
- `@pytest.mark.unit`: Pure unit tests (default, no marker needed)

### Running Specific Tests

```bash
# Run specific test file
pytest tests/test_trafapy.py -v

# Run specific test class
pytest tests/test_trafapy.py::TestTrafikanalysClient -v

# Run specific test method
pytest tests/test_trafapy.py::TestAPICache::test_cache_initialization -v

# Run tests matching a pattern
pytest -k "build_query" -v

# Exclude specific tests
pytest -k "not cache_warming_strategy" -v
```

## 📊 Coverage Reports

Generate coverage reports to ensure comprehensive testing:

```bash
# Terminal coverage report
pytest -m "not integration" --cov=trafapy --cov-report=term-missing

# Generate HTML coverage report
pytest -m "not integration" --cov=trafapy --cov-report=html

# Using the test runner
python tests/run_tests.py --coverage-report
```

**Coverage targets:**
- **Overall coverage**: >90%
- **Core modules**: >95%
- **Critical paths**: 100%

The HTML report (`htmlcov/index.html`) shows:
- Line-by-line coverage visualization
- Untested code paths
- Branch coverage information
- Missing test areas

## 🔧 Test Runner Usage

The custom test runner (`tests/run_tests.py`) provides convenient commands:

```bash
# Basic usage
python tests/run_tests.py --unit              # Unit tests only
python tests/run_tests.py --integration       # Integration tests only
python tests/run_tests.py --all               # All tests
python tests/run_tests.py --fast              # Fast tests only

# With options
python tests/run_tests.py --unit --verbose    # Verbose output
python tests/run_tests.py --unit --coverage   # With coverage
python tests/run_tests.py --coverage-report   # Detailed HTML report

# Code quality checks
python tests/run_tests.py --lint              # Run flake8, black, mypy
```

## 🧪 Writing New Tests

### Test Structure Template

```python
class TestNewFeature:
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.client = TrafikanalysClient(
            cache_enabled=True,
            cache_dir=self.temp_dir,
            debug=False
        )
    
    def teardown_method(self):
        """Clean up after each test."""
        if hasattr(self, 'temp_dir') and self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_specific_functionality(self):
        """Test a specific piece of functionality."""
        # Arrange - Set up test data
        test_input = {"key": "value"}
        
        # Act - Execute the functionality
        result = self.client.some_method(test_input)
        
        # Assert - Verify the results
        assert result == expected_output
```

### Best Practices

1. **Use descriptive test names**: `test_build_query_with_multiple_filters_returns_correct_string`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies**: Use `@patch` for API calls
4. **Test edge cases**: Empty inputs, malformed data, error conditions
5. **Use fixtures**: Share common setup across tests
6. **Keep tests focused**: One concept per test method
7. **Test both success and failure paths**

### Mocking Examples

```python
# Mock API responses
@patch('trafapy.client.TrafikanalysClient._make_request')
def test_list_products(mock_request):
    mock_request.return_value = {"StructureItems": [...]}
    # Test logic here

# Mock specific methods
@patch.object(client, 'explore_product_variables')
def test_build_query(mock_explore):
    mock_explore.return_value = pd.DataFrame([...])
    # Test logic here

# Mock with side effects
mock_request.side_effect = [response1, response2, response3]
```

### Adding Integration Tests

Mark integration tests appropriately and use caching:

```python
@pytest.mark.integration
def test_real_api_functionality():
    """Test actual API interaction (marked as integration test)."""
    client = TrafikanalysClient(cache_enabled=True)  # Use cache!
    
    try:
        result = client.list_products()
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0
    except Exception as e:
        pytest.skip(f"API test failed (normal): {e}")
```

## 🔄 Continuous Integration

### GitHub Actions Workflow

The test suite runs automatically on:
- Pull requests to main/develop branches
- Pushes to main/develop branches

**Workflow steps:**
1. **Unit tests** on Python 3.7, 3.8, 3.9, 3.10, 3.11
2. **Code quality checks** (flake8, black, mypy)
3. **Coverage reporting** to Codecov
4. **Integration tests** (separate job, may fail)

### Local CI Simulation

```bash
# Run the same checks as CI
python tests/run_tests.py --lint       # Code quality
pytest -m "not integration" --cov     # Unit tests with coverage
pytest -m integration --maxfail=3     # Integration tests
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Import Errors
```bash
# Solution: Install in development mode
pip install -e .

# Verify installation
python -c "import trafapy; print('Success!')"
```

#### Missing Dependencies
```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Or install all development dependencies
pip install -r requirements-test.txt
```

#### Cache Directory Issues
```bash
# Clean cache manually
rm -rf ~/.trafapy_cache

# Or in tests
shutil.rmtree(temp_dir, ignore_errors=True)
```

#### Integration Test Failures
- Check internet connectivity
- Verify Trafikanalys API is accessible
- Look for rate limiting (429 errors)
- Try running individual tests with `pytest -s` for debug output

#### Unknown Marker Warnings
```bash
# Make sure pytest.ini is properly configured
# Add markers to pytest.ini if needed
```

### Debug Mode

```bash
# Run with debug output
pytest -s -v --tb=long

# Enable client debug mode
client = TrafikanalysClient(debug=True)

# Show print statements
pytest -s tests/test_file.py::test_method
```

## 📈 Performance Considerations

- **Unit tests** should complete in <10 seconds total
- **Individual tests** should complete in <1 second
- Use **caching** to speed up repeated test runs
- **Mock expensive operations** like HTTP requests
- Avoid creating **large test datasets** in memory

## ✅ Test Quality Metrics

Current test suite statistics:
- **Total tests**: 53 unit tests + integration tests
- **Coverage**: >90% of codebase
- **Execution time**: <10 seconds for unit tests
- **Success rate**: 98%+ for unit tests

**Quality indicators:**
- All core functionality is tested
- Error paths are covered
- Edge cases are handled
- Real-world usage patterns are validated

## 🔮 Future Improvements

Planned test enhancements:
- **Property-based testing** with Hypothesis
- **Performance benchmarking** suite
- **Load testing** for cache system
- **Automated API compatibility** checking
- **Documentation testing** with doctest

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python.org/3/library/unittest.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Trafikanalys API Documentation](https://www.trafa.se/sidor/oppen-data-api/)

## 🤝 Contributing Tests

When contributing to TrafaPy:

1. **Write tests first** (TDD approach recommended)
2. **Ensure >90% coverage** for new code
3. **Include both positive and negative test cases**
4. **Update this documentation** for new test patterns
5. **Run full test suite** before submitting PRs:

```bash
# Pre-contribution checklist
python tests/run_tests.py --all --lint --coverage
```

6. **Add appropriate markers** for new test types
7. **Use descriptive test and commit messages**

---

## 📞 Support

If you encounter testing issues:

1. **Check this documentation** for common solutions
2. **Run with verbose output**: `pytest -v -s`
3. **Check test isolation**: Run individual tests
4. **Verify dependencies**: `pip list | grep pytest`
5. **Clean environment**: Remove cache and temporary files

**Remember**: A passing test suite means your TrafaPy installation is working correctly! 🎉