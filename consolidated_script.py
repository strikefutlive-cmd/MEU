"""
Consolidated Form Automation Script

This script consolidates features from multiple automation scripts:
1. Temporary email creation using mail.tm
2. Robust field recognition and data filling (including CEP_PRIMEIRO and CEP_SEGUNDO)
3. Modular architecture for maintainability
4. Comprehensive error handling and logging
5. Compatible browser configurations
"""

import logging
import sys
import argparse
from typing import Optional
import time

# Import our modules
from email_generator import EmailGenerator
from data_handler import DataHandler
from selenium_utils import BrowserConfig, SeleniumHelper
from form_filler import FormFiller


# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Setup logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to write logs to
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers
    )


class FormAutomation:
    """Main class for form automation with email generation"""
    
    def __init__(self, url: str, headless: bool = False, log_level: str = "INFO"):
        """
        Initialize the form automation
        
        Args:
            url: URL of the form to fill
            headless: Run browser in headless mode
            log_level: Logging level
        """
        setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        self.url = url
        self.headless = headless
        
        # Initialize components
        self.email_gen = None
        self.data_handler = None
        self.driver = None
        self.selenium_helper = None
        self.form_filler = None
        
        self.logger.info("FormAutomation initialized")
    
    def setup_email(self) -> bool:
        """
        Setup temporary email account
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Setting up temporary email account...")
            self.email_gen = EmailGenerator()
            
            # Create email account
            result = self.email_gen.create_account()
            if not result:
                self.logger.error("Failed to create email account")
                return False
            
            email, password = result
            self.logger.info(f"Created temporary email: {email}")
            
            # Login to get token
            if not self.email_gen.login():
                self.logger.error("Failed to login to email account")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up email: {e}")
            return False
    
    def setup_browser(self) -> bool:
        """
        Setup browser and Selenium components
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Setting up browser...")
            
            # Configure browser options
            options = BrowserConfig.get_chrome_options(
                headless=self.headless,
                disable_images=False
            )
            
            # Create driver
            self.driver = BrowserConfig.create_driver(options)
            
            # Create helper
            self.selenium_helper = SeleniumHelper(self.driver, default_timeout=10)
            
            # Create form filler
            self.form_filler = FormFiller(self.selenium_helper)
            
            self.logger.info("Browser setup complete")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting up browser: {e}")
            return False
    
    def generate_data(self) -> bool:
        """
        Generate form data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Generating form data...")
            self.data_handler = DataHandler()
            
            # Get email from email generator
            email = self.email_gen.email if self.email_gen else None
            
            # Generate complete form data
            data = self.data_handler.generate_form_data(email=email)
            
            self.logger.info(f"Generated data for {len(data)} fields")
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating data: {e}")
            return False
    
    def navigate_to_form(self) -> bool:
        """
        Navigate to the form URL
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Navigating to: {self.url}")
            self.driver.get(self.url)
            
            # Wait for page to load
            if not self.selenium_helper.wait_for_page_load():
                self.logger.warning("Page load timeout, but continuing...")
            
            self.logger.info("Successfully navigated to form")
            return True
            
        except Exception as e:
            self.logger.error(f"Error navigating to form: {e}")
            return False
    
    def fill_form(self) -> bool:
        """
        Fill the form with generated data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Starting form filling process...")
            
            # Get data
            data = self.data_handler.data
            
            # Handle special fields first (like split CEP)
            self.form_filler.handle_special_fields(data)
            
            # Fill all other fields
            results = self.form_filler.fill_form(data)
            
            # Calculate success rate
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            success_rate = (successful / total * 100) if total > 0 else 0
            
            self.logger.info(f"Form filling complete: {successful}/{total} fields ({success_rate:.1f}%)")
            
            # Consider successful if at least 50% of fields were filled
            return success_rate >= 50
            
        except Exception as e:
            self.logger.error(f"Error filling form: {e}")
            return False
    
    def submit_form(self, button_texts: list = None) -> bool:
        """
        Submit the form
        
        Args:
            button_texts: Optional list of button texts to look for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("Attempting to submit form...")
            
            if self.form_filler.submit_form(button_texts):
                self.logger.info("Form submitted successfully")
                return True
            else:
                self.logger.warning("Could not submit form automatically")
                return False
                
        except Exception as e:
            self.logger.error(f"Error submitting form: {e}")
            return False
    
    def take_screenshot(self, filename: str = "screenshot.png") -> bool:
        """
        Take a screenshot
        
        Args:
            filename: Filename for the screenshot
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return self.selenium_helper.take_screenshot(filename)
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return False
    
    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Starting cleanup...")
        
        # Close browser
        if self.selenium_helper:
            try:
                self.selenium_helper.close_driver()
            except Exception as e:
                self.logger.error(f"Error closing driver: {e}")
        
        # Cleanup email (optional - email will expire anyway)
        if self.email_gen:
            try:
                # Uncomment if you want to delete the email account
                # self.email_gen.cleanup()
                pass
            except Exception as e:
                self.logger.error(f"Error cleaning up email: {e}")
        
        self.logger.info("Cleanup complete")
    
    def run(self, submit: bool = True, screenshot: bool = True) -> bool:
        """
        Run the complete automation workflow
        
        Args:
            submit: Whether to submit the form
            screenshot: Whether to take a screenshot
            
        Returns:
            True if successful, False otherwise
        """
        success = False
        
        try:
            # Setup email
            if not self.setup_email():
                self.logger.error("Failed to setup email")
                return False
            
            # Setup browser
            if not self.setup_browser():
                self.logger.error("Failed to setup browser")
                return False
            
            # Generate data
            if not self.generate_data():
                self.logger.error("Failed to generate data")
                return False
            
            # Navigate to form
            if not self.navigate_to_form():
                self.logger.error("Failed to navigate to form")
                return False
            
            # Fill form
            if not self.fill_form():
                self.logger.error("Form filling had issues")
                # Continue anyway to see what was filled
            
            # Take screenshot if requested
            if screenshot:
                self.take_screenshot("form_filled.png")
            
            # Submit form if requested
            if submit:
                self.submit_form()
                time.sleep(2)  # Wait a bit after submission
                
                if screenshot:
                    self.take_screenshot("form_submitted.png")
            
            success = True
            self.logger.info("Automation completed successfully")
            
        except Exception as e:
            self.logger.error(f"Automation failed with error: {e}")
            
            # Try to take error screenshot
            try:
                if self.selenium_helper:
                    self.take_screenshot("error_screenshot.png")
            except:
                pass
        
        finally:
            self.cleanup()
        
        return success


def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description='Automated form filling with temporary email generation'
    )
    
    parser.add_argument(
        'url',
        help='URL of the form to fill'
    )
    
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    parser.add_argument(
        '--no-submit',
        action='store_true',
        help='Do not submit the form (fill only)'
    )
    
    parser.add_argument(
        '--no-screenshot',
        action='store_true',
        help='Do not take screenshots'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Set the logging level'
    )
    
    args = parser.parse_args()
    
    # Create and run automation
    automation = FormAutomation(
        url=args.url,
        headless=args.headless,
        log_level=args.log_level
    )
    
    success = automation.run(
        submit=not args.no_submit,
        screenshot=not args.no_screenshot
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
