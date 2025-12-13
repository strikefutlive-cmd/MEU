"""
Example usage of the consolidated form automation script

This demonstrates how to use the various modules programmatically
instead of using the command-line interface.
"""

import logging
from email_generator import EmailGenerator
from data_handler import DataHandler
from selenium_utils import BrowserConfig, SeleniumHelper
from form_filler import FormFiller

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_email_generation():
    """Example: Generate a temporary email"""
    logger.info("=== Example: Email Generation ===")
    
    email_gen = EmailGenerator()
    
    # Create account
    result = email_gen.create_account()
    if result:
        email, password = result
        logger.info(f"Created email: {email}")
        logger.info(f"Password: {password}")
        
        # Login
        if email_gen.login():
            logger.info("Successfully logged in")
            
            # You could wait for emails here
            # message = email_gen.wait_for_email(timeout=60)
    else:
        logger.error("Failed to create email")


def example_data_generation():
    """Example: Generate form data"""
    logger.info("=== Example: Data Generation ===")
    
    data_handler = DataHandler()
    
    # Generate complete form data
    data = data_handler.generate_form_data(email="custom@example.com")
    
    logger.info("Generated form data:")
    for field, value in data.items():
        logger.info(f"  {field}: {value}")
    
    # Generate specific fields
    logger.info("\nGenerate specific fields:")
    logger.info(f"  CPF: {data_handler.generate_cpf()}")
    logger.info(f"  Phone: {data_handler.generate_phone()}")
    
    cep = data_handler.generate_cep()
    primeiro, segundo = data_handler.split_cep(cep)
    logger.info(f"  CEP: {primeiro}-{segundo}")


def example_browser_setup():
    """Example: Setup browser (requires ChromeDriver)"""
    logger.info("=== Example: Browser Setup ===")
    
    try:
        # Create browser with options
        options = BrowserConfig.get_chrome_options(headless=True)
        driver = BrowserConfig.create_driver(options)
        
        # Create helper
        helper = SeleniumHelper(driver)
        
        logger.info("Browser created successfully")
        
        # Navigate to a page
        driver.get("https://www.google.com")
        logger.info(f"Page title: {driver.title}")
        
        # Cleanup
        helper.close_driver()
        logger.info("Browser closed")
        
    except Exception as e:
        logger.error(f"Browser setup failed: {e}")
        logger.info("Make sure ChromeDriver is installed and in PATH")


def example_form_filling():
    """Example: Fill a form (conceptual)"""
    logger.info("=== Example: Form Filling (Conceptual) ===")
    
    # This is a conceptual example showing the workflow
    # In reality, you'd need a real form URL
    
    logger.info("Workflow:")
    logger.info("1. Create email account")
    logger.info("2. Generate form data with that email")
    logger.info("3. Setup browser and navigate to form")
    logger.info("4. Use FormFiller to fill fields")
    logger.info("5. Submit form")
    logger.info("6. Clean up resources")
    
    logger.info("\nSample code:")
    code = '''
    # Create email
    email_gen = EmailGenerator()
    email, _ = email_gen.create_account()
    email_gen.login()
    
    # Generate data
    data_handler = DataHandler()
    data = data_handler.generate_form_data(email=email)
    
    # Setup browser
    driver = BrowserConfig.create_driver()
    helper = SeleniumHelper(driver)
    form_filler = FormFiller(helper)
    
    # Navigate and fill
    driver.get("https://example.com/form")
    form_filler.fill_form(data)
    form_filler.submit_form()
    
    # Cleanup
    helper.close_driver()
    '''
    logger.info(code)


def main():
    """Run all examples"""
    logger.info("=" * 60)
    logger.info("Consolidated Script - Example Usage")
    logger.info("=" * 60)
    
    # Example 1: Email generation
    try:
        example_email_generation()
    except Exception as e:
        logger.error(f"Email example failed: {e}")
    
    print()
    
    # Example 2: Data generation
    try:
        example_data_generation()
    except Exception as e:
        logger.error(f"Data example failed: {e}")
    
    print()
    
    # Example 3: Browser setup (may fail if no ChromeDriver)
    try:
        example_browser_setup()
    except Exception as e:
        logger.error(f"Browser example failed: {e}")
    
    print()
    
    # Example 4: Form filling workflow
    try:
        example_form_filling()
    except Exception as e:
        logger.error(f"Form filling example failed: {e}")
    
    logger.info("=" * 60)
    logger.info("Examples complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
