# Contributing to MCP Python Library

Thank you for your interest in contributing to the MCP (Mathema Calculation Plus) Python library! We welcome contributions from the community.

## 🤝 How to Contribute

### Types of Contributions

We welcome several types of contributions:

- **Bug Reports**: Report issues and bugs
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Submit code improvements or new features
- **Documentation**: Improve documentation and examples
- **Examples**: Add new example scripts and use cases
- **Testing**: Improve test coverage and quality

### Getting Started

1. **Fork the Repository**
   ```bash
   git clone https://github.com/MDTSH/mcp_excel.git
   cd mcp-_xcel
   ```

2. **Create a Development Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # or
   source venv/bin/activate  # Linux/Mac
   
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Development Guidelines

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for function parameters and return values
- Write clear, descriptive variable and function names
- Add docstrings for all public functions and classes

### Example Code Style

```python
def calculate_option_price(
    spot_price: float,
    strike_price: float,
    volatility: float,
    time_to_expiry: float,
    risk_free_rate: float
) -> float:
    """
    Calculate European option price using Black-Scholes model.
    
    Args:
        spot_price: Current underlying asset price
        strike_price: Option strike price
        volatility: Annualized volatility (0.0 to 1.0)
        time_to_expiry: Time to expiry in years
        risk_free_rate: Risk-free interest rate
        
    Returns:
        Option price
    """
    # Implementation here
    pass
```

### Testing

- Write tests for new functionality
- Ensure all existing tests pass
- Aim for high test coverage
- Test both success and error cases

### Documentation

- Update README.md if adding new features
- Add docstrings to all public functions
- Include usage examples in docstrings
- Update example scripts if relevant

## 🐛 Reporting Issues

### Before Reporting

1. Check if the issue already exists
2. Ensure you're using the latest version
3. Verify the issue with a minimal example

### Issue Template

When reporting issues, please include:

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment:**
- OS: [e.g. Windows 10]
- Python version: [e.g. 3.8.5]
- MCP version: [e.g. 1.4.0]

**Additional context**
Add any other context about the problem here.
```

## 🚀 Pull Request Process

### Before Submitting

1. **Run Tests**: Ensure all tests pass
   ```bash
   python script/03_test_python.py
   ```

2. **Code Quality**: Run linting and formatting
   ```bash
   black .
   flake8 .
   mypy .
   ```

3. **Update Documentation**: Update relevant documentation

4. **Test Examples**: Verify example scripts work correctly

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Example addition
- [ ] Performance improvement

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Documentation
- [ ] README.md updated (if needed)
- [ ] Docstrings added/updated
- [ ] Example scripts updated (if needed)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No breaking changes (or clearly documented)
```

## 📋 Development Setup

### Prerequisites

- Python 3.7+
- Git
- PyXLL (for Excel integration testing)
- Visual Studio Code (recommended)

### IDE Setup

For VS Code, install these extensions:
- Python
- Pylance
- Black Formatter
- GitLens

### Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## 🏗️ Project Structure

```
mcp-python/
├── mcp/                    # Core library
├── example/                # Example scripts
├── excel/                  # Excel templates
├── pyxll_func/            # Excel functions
├── script/                # Utility scripts
└── docs/                  # Documentation
```

## 📚 Adding New Examples

When adding new example scripts:

1. Place in appropriate subdirectory under `example/`
2. Follow naming convention: `descriptive_name_demo.py`
3. Include comprehensive docstring
4. Add main function for standalone execution
5. Include error handling
6. Add to test suite

### Example Template

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[Description] Demo Program

This program demonstrates [functionality]:
1. [Feature 1]
2. [Feature 2]
3. [Feature 3]

Author: Mathema Team
Last Updated: [Date]
"""

from mcp.tool.tools_main import [RelevantClass]
from mcp.utils.enums import [RelevantEnums]

def main():
    """Main function to demonstrate [functionality]"""
    print("[Title] Demo")
    print("=" * 50)
    
    try:
        # Implementation here
        print("Demo completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

if __name__ == "__main__":
    main()
```

## 🔒 Security

- Never commit sensitive information (API keys, passwords, etc.)
- Use environment variables for configuration
- Validate all user inputs
- Follow secure coding practices

## 📞 Getting Help

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Documentation**: Check the [user guide](http://help.mathema.com.cn/latest/api/)

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to MCP! 🎉
