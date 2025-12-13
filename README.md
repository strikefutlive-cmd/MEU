# Consolidated Form Automation Script

A unified and improved form automation solution that combines temporary email generation with robust field recognition and data filling capabilities.

## Features

### 1. Temporary Email Creation
- Uses `mail.tm` API for generating temporary email addresses
- Automatic account creation and authentication
- Email retrieval and message reading capabilities
- Clean account management

### 2. Robust Field Recognition
- Intelligent field detection using multiple strategies:
  - ID attribute matching
  - Name attribute matching
  - Placeholder text matching
  - Label text association
- Handles special fields like `CEP_PRIMEIRO` and `CEP_SEGUNDO`
- Supports various field types: email, name, CPF, phone, address, etc.

### 3. Modular Architecture
- **email_generator.py**: Handles temporary email creation via mail.tm
- **data_handler.py**: Generates realistic test data for form fields
- **selenium_utils.py**: Provides browser configuration and Selenium utilities
- **form_filler.py**: Implements intelligent form field recognition and filling
- **consolidated_script.py**: Main orchestration script

### 4. Error Handling & Logging
- Comprehensive error handling throughout all modules
- Configurable logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Detailed logging of operations and issues
- Graceful failure handling with cleanup

### 5. Browser Configuration
- Compatible Chrome browser setup
- Headless mode support
- Anti-detection measures
- Configurable timeouts and waits

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install ChromeDriver:
- Download from https://chromedriver.chromium.org/
- Ensure it's in your PATH or specify the path in the script

## Usage

### Basic Usage
```bash
python consolidated_script.py https://example.com/form
```

### Advanced Options
```bash
# Run in headless mode
python consolidated_script.py https://example.com/form --headless

# Fill form but don't submit
python consolidated_script.py https://example.com/form --no-submit

# Disable screenshots
python consolidated_script.py https://example.com/form --no-screenshot

# Set log level to DEBUG
python consolidated_script.py https://example.com/form --log-level DEBUG
```

## Module Documentation

### EmailGenerator
Handles temporary email account creation and management.

```python
from email_generator import EmailGenerator

email_gen = EmailGenerator()
email, password = email_gen.create_account()
email_gen.login()
messages = email_gen.get_messages()
```

### DataHandler
Generates realistic Brazilian form data.

```python
from data_handler import DataHandler

data_handler = DataHandler()
data = data_handler.generate_form_data(email="test@example.com")
# Returns: nome, sobrenome, cpf, telefone, cep, cep_primeiro, cep_segundo, etc.
```

### SeleniumHelper
Provides safe Selenium operations with error handling.

```python
from selenium_utils import BrowserConfig, SeleniumHelper

driver = BrowserConfig.create_driver()
helper = SeleniumHelper(driver)
helper.send_keys_safe(By.ID, "email", "test@example.com")
```

### FormFiller
Intelligently finds and fills form fields.

```python
from form_filler import FormFiller

form_filler = FormFiller(selenium_helper)
form_filler.fill_field('email', 'test@example.com')
results = form_filler.fill_form(data)
```

## Field Type Support

The script supports automatic detection and filling of these field types:

- **email**: Email address fields
- **nome**: First name fields
- **sobrenome**: Last name fields
- **nome_completo**: Full name fields
- **cpf**: Brazilian CPF (ID) fields
- **telefone**: Phone number fields
- **celular**: Mobile phone fields
- **cep**: Brazilian postal code (single field)
- **cep_primeiro**: First part of split CEP (5 digits)
- **cep_segundo**: Second part of split CEP (3 digits)
- **data_nascimento**: Date of birth fields
- **senha**: Password fields
- **confirmar_senha**: Password confirmation fields

## Error Handling

The script includes comprehensive error handling:

- Network errors when creating email accounts
- Browser initialization failures
- Element not found scenarios
- Timeout situations
- Stale element references
- Element not interactable issues

All errors are logged with appropriate detail levels.

## Logging

Configure logging level to see different amounts of detail:

- **DEBUG**: All operations and element searches
- **INFO**: Major operations and success/failure (default)
- **WARNING**: Issues that don't prevent execution
- **ERROR**: Errors that affect functionality
- **CRITICAL**: Fatal errors

## Screenshots

The script automatically takes screenshots:
- `form_filled.png`: After filling the form
- `form_submitted.png`: After submitting (if enabled)
- `error_screenshot.png`: When errors occur

## Examples

### Example 1: Test a Registration Form
```bash
python consolidated_script.py https://example.com/register --log-level INFO
```

### Example 2: Fill Without Submitting (Testing)
```bash
python consolidated_script.py https://example.com/form --no-submit
```

### Example 3: Headless Automation
```bash
python consolidated_script.py https://example.com/form --headless --no-screenshot
```

## Best Practices

1. **Testing**: Use `--no-submit` flag when testing to avoid actually submitting forms
2. **Debugging**: Use `--log-level DEBUG` to see detailed operation logs
3. **Production**: Use `--headless` for server environments
4. **Error Analysis**: Check screenshots and logs when automation fails

## Troubleshooting

### ChromeDriver Issues
- Ensure ChromeDriver version matches your Chrome browser version
- Check if ChromeDriver is in your PATH
- Specify driver path explicitly if needed

### Field Detection Issues
- Use DEBUG logging to see which fields are being detected
- Check if field IDs/names match expected patterns
- Verify page has loaded completely before filling

### Email Generation Issues
- Check internet connectivity
- Verify mail.tm service is accessible
- Try creating email account manually first

## Contributing

To extend the script:

1. Add new field patterns to `form_filler.py`
2. Add new data generators to `data_handler.py`
3. Add new Selenium utilities to `selenium_utils.py`
4. Update documentation

## License

This script is provided as-is for educational and testing purposes.

## Security Notes

- Never use this script on production systems without permission
- Temporary emails expire after a period
- Generated data is random and for testing only
- Always respect websites' terms of service
