# Architecture Documentation

## Overview

This consolidated form automation script combines the best features of multiple automation approaches into a single, maintainable, and robust solution.

## Design Principles

1. **Modularity**: Each functional area is separated into its own module
2. **Error Handling**: Comprehensive error handling with graceful degradation
3. **Logging**: Detailed logging at multiple levels for debugging and monitoring
4. **Configurability**: Key behaviors can be configured via parameters
5. **Maintainability**: Clear separation of concerns and well-documented code

## Module Architecture

```
consolidated_script.py (Main orchestrator)
    ├── email_generator.py (Email management)
    ├── data_handler.py (Data generation)
    ├── selenium_utils.py (Browser utilities)
    └── form_filler.py (Form interaction)
```

### Module Details

#### 1. email_generator.py
**Purpose**: Handles temporary email account creation and management using mail.tm API

**Key Classes**:
- `EmailGenerator`: Main class for email operations

**Key Methods**:
- `get_domains()`: Retrieves available email domains
- `create_account()`: Creates a new temporary email account
- `login()`: Authenticates with the email service
- `get_messages()`: Retrieves inbox messages
- `wait_for_email()`: Polls for new emails with timeout
- `cleanup()`: Deletes the temporary account

**Features**:
- Automatic domain selection
- Random username generation
- Secure password generation
- Message retrieval and parsing
- Email polling with configurable timeout

#### 2. data_handler.py
**Purpose**: Generates realistic Brazilian form data for testing

**Key Classes**:
- `DataHandler`: Main class for data generation

**Key Methods**:
- `generate_cpf()`: Creates valid CPF numbers
- `generate_phone()`: Creates valid Brazilian phone numbers
- `generate_cep()`: Creates postal codes
- `split_cep()`: Splits CEP into two parts (for forms requiring separate fields)
- `generate_form_data()`: Creates complete dataset for forms

**Features**:
- Valid CPF generation with check digits
- Brazilian phone format (DDD + 9 digits)
- Complete Brazilian area code support
- CEP handling (both single and split fields)
- Date of birth generation with age constraints
- Random but realistic names

#### 3. selenium_utils.py
**Purpose**: Provides browser configuration and common Selenium operations

**Key Classes**:
- `BrowserConfig`: Handles browser setup
- `SeleniumHelper`: Provides safe Selenium operations

**BrowserConfig Methods**:
- `get_chrome_options()`: Configures Chrome with best practices
- `create_driver()`: Initializes WebDriver

**SeleniumHelper Methods**:
- `find_element_safe()`: Finds elements with timeout and error handling
- `click_element()`: Clicks with retry logic
- `send_keys_safe()`: Sends keys with error handling
- `scroll_to_element()`: Scrolls element into view
- `wait_for_page_load()`: Waits for complete page load
- `take_screenshot()`: Captures screenshots

**Features**:
- Headless mode support
- Anti-detection measures
- Configurable timeouts
- Automatic waits
- Error recovery
- Screenshot capability

#### 4. form_filler.py
**Purpose**: Intelligently identifies and fills form fields

**Key Classes**:
- `FormFiller`: Main class for form interaction

**Key Methods**:
- `find_field_by_patterns()`: Multi-strategy field detection
- `fill_field()`: Fills a single field with retry
- `fill_form()`: Fills complete form
- `handle_special_fields()`: Handles CEP_PRIMEIRO/SEGUNDO
- `submit_form()`: Finds and clicks submit button

**Field Detection Strategies**:
1. **ID matching**: Searches input[id*='pattern']
2. **Name matching**: Searches input[name*='pattern']
3. **Placeholder matching**: Searches input[placeholder*='pattern']
4. **Label matching**: Finds labels and associated inputs

**Supported Field Types**:
- email, nome, sobrenome, nome_completo
- cpf, telefone, celular
- cep, cep_primeiro, cep_segundo
- data_nascimento, senha, confirmar_senha

**Special Handling**:
- Split CEP fields (CEP_PRIMEIRO and CEP_SEGUNDO)
- Retry logic for flaky elements
- Scroll-to-view before interaction
- Visibility and enabled state checks

#### 5. consolidated_script.py
**Purpose**: Main orchestration script that ties everything together

**Key Classes**:
- `FormAutomation`: Main automation controller

**Workflow**:
1. Setup temporary email account
2. Setup browser and Selenium components
3. Generate form data (using the email from step 1)
4. Navigate to target form
5. Fill form fields intelligently
6. Take screenshots (optional)
7. Submit form (optional)
8. Cleanup resources

**CLI Options**:
- `url`: Target form URL (required)
- `--headless`: Run in headless mode
- `--no-submit`: Fill but don't submit
- `--no-screenshot`: Disable screenshots
- `--log-level`: Set logging level

## Data Flow

```
1. User runs script with URL
   ↓
2. EmailGenerator creates temp email
   ↓
3. DataHandler generates form data (includes temp email)
   ↓
4. BrowserConfig creates Chrome driver
   ↓
5. SeleniumHelper wraps driver with safe operations
   ↓
6. Driver navigates to form URL
   ↓
7. FormFiller detects fields on page
   ↓
8. FormFiller fills fields with generated data
   ↓
9. FormFiller submits form (if requested)
   ↓
10. SeleniumHelper takes screenshots
   ↓
11. Resources cleaned up
```

## Error Handling Strategy

### Levels of Error Handling

1. **Module Level**: Each method has try-except blocks
2. **Operation Level**: Safe wrappers for Selenium operations
3. **Workflow Level**: Main script continues even on partial failures
4. **Cleanup Level**: Ensures resources are freed even on errors

### Error Scenarios

- **Network errors**: Gracefully handled in email generation
- **Element not found**: Logged and continues with other fields
- **Timeout**: Configurable timeouts with fallbacks
- **Stale elements**: Automatic retry logic
- **Browser crashes**: Proper cleanup in finally blocks

## Logging Strategy

### Log Levels

- **DEBUG**: Element searches, detailed operations
- **INFO**: Major operations, success/failure status (default)
- **WARNING**: Issues that don't prevent execution
- **ERROR**: Errors affecting functionality
- **CRITICAL**: Fatal errors

### Log Output

- Console output (stdout)
- Optional file output
- Structured format with timestamps

## Configuration Options

### Browser Configuration
- Headless mode: On/Off
- Image loading: Enabled/Disabled
- Window size: 1920x1080
- Timeouts: Configurable

### Email Configuration
- Domain: Auto-selected
- Username: Random or custom
- Password: Randomly generated

### Form Filling Configuration
- Retry attempts: Configurable per field
- Submit: Optional
- Screenshots: Optional
- Button texts: Customizable list

## Security Considerations

1. **Password Generation**: Uses secure random with proper character sets
2. **No Hardcoded Credentials**: All credentials generated at runtime
3. **Temporary Data**: Email accounts and data are temporary
4. **No Data Persistence**: No sensitive data saved to disk
5. **Clean Separation**: API keys and credentials isolated

## Testing Strategy

### Unit Tests
- Individual module functionality
- Data generation validation
- Field detection logic

### Integration Tests
- Module interaction
- Workflow completion
- Error recovery

### Manual Testing
- Real form filling
- Different field layouts
- Various submit button types

## Extensibility

### Adding New Field Types

1. Add patterns to `form_filler.py` field_patterns dict
2. Add generator to `data_handler.py` if needed
3. Update documentation

### Adding New Data Generators

1. Add static method to `DataHandler`
2. Include in `generate_form_data()` if needed
3. Document format and constraints

### Adding New Selenium Utilities

1. Add method to `SeleniumHelper`
2. Follow safe wrapper pattern
3. Include proper error handling

### Adding New Email Providers

1. Create new class similar to `EmailGenerator`
2. Implement same interface
3. Update `FormAutomation` to use new provider

## Performance Considerations

1. **Parallel Operations**: Not implemented (sequential for reliability)
2. **Caching**: No caching (each run is independent)
3. **Resource Usage**: One browser instance per run
4. **Network**: Minimal (only email API calls)
5. **Memory**: Released in cleanup phase

## Best Practices

1. **Always use --no-submit for testing**: Prevents actual form submissions
2. **Use DEBUG logging when developing**: See all operations
3. **Check screenshots on failures**: Visual debugging
4. **Handle cleanup properly**: Always close resources
5. **Validate field patterns**: Test with actual forms first

## Known Limitations

1. **Captcha**: Cannot handle captcha challenges
2. **JavaScript-heavy forms**: May have timing issues
3. **Dynamic fields**: May miss fields loaded via AJAX
4. **Custom widgets**: May not recognize non-standard inputs
5. **Multi-page forms**: Designed for single-page forms

## Future Enhancements

1. **Multi-page form support**: Navigate through form steps
2. **JavaScript wait strategies**: Better AJAX handling
3. **OCR for captcha**: Basic captcha solving
4. **Form state persistence**: Save and resume
5. **Parallel execution**: Multiple forms at once
6. **More data types**: Additional field types
7. **Configuration files**: YAML/JSON configuration
8. **API mode**: Use as a service

## Troubleshooting Guide

### Issue: Fields not being filled
**Solution**: Use DEBUG logging to see detection strategy, check field patterns

### Issue: Elements not found
**Solution**: Increase timeouts, check if page fully loaded

### Issue: Email not created
**Solution**: Check internet connection, try different email provider

### Issue: Browser won't start
**Solution**: Verify ChromeDriver version matches Chrome, check PATH

### Issue: Form won't submit
**Solution**: Check button text patterns, verify button is visible/enabled

## Maintenance

### Regular Tasks
1. Update ChromeDriver when Chrome updates
2. Review and update field patterns
3. Check mail.tm API status
4. Update area codes if needed

### Dependencies
- Review and update `requirements.txt` periodically
- Test with latest Selenium versions
- Monitor for deprecation warnings

## Support

For issues or questions:
1. Check logs with DEBUG level
2. Review screenshots
3. Verify form structure
4. Test with simple forms first
5. Check documentation
