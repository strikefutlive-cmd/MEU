"""
Selenium Utilities Module
Provides browser configuration and common Selenium operations
"""
import logging
import time
from typing import Optional, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementNotInteractableException,
    StaleElementReferenceException
)

logger = logging.getLogger(__name__)


class BrowserConfig:
    """Handles browser configuration and initialization"""
    
    @staticmethod
    def get_chrome_options(headless: bool = False, disable_images: bool = False) -> Options:
        """
        Get Chrome options with best practices
        
        Args:
            headless: Run browser in headless mode
            disable_images: Disable image loading for faster performance
            
        Returns:
            Configured Chrome options
        """
        options = Options()
        
        # Basic options for stability
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Window size
        options.add_argument('--window-size=1920,1080')
        
        # Headless mode
        if headless:
            options.add_argument('--headless')
            logger.info("Browser configured in headless mode")
        
        # Disable images for performance
        if disable_images:
            prefs = {"profile.managed_default_content_settings.images": 2}
            options.add_experimental_option("prefs", prefs)
            logger.info("Image loading disabled")
        
        # Additional privacy and security settings
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        
        logger.info("Chrome options configured")
        return options
    
    @staticmethod
    def create_driver(options: Options = None, driver_path: str = None) -> webdriver.Chrome:
        """
        Create and configure Chrome WebDriver
        
        Args:
            options: Chrome options to use
            driver_path: Path to chromedriver executable
            
        Returns:
            Configured Chrome WebDriver instance
        """
        try:
            if options is None:
                options = BrowserConfig.get_chrome_options()
            
            if driver_path:
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)
            
            # Set implicit wait
            driver.implicitly_wait(10)
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            logger.info("WebDriver created successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Error creating WebDriver: {e}")
            raise


class SeleniumHelper:
    """Helper class for common Selenium operations"""
    
    def __init__(self, driver: webdriver.Chrome, default_timeout: int = 10):
        self.driver = driver
        self.default_timeout = default_timeout
        self.wait = WebDriverWait(driver, default_timeout)
    
    def find_element_safe(self, by: By, value: str, timeout: int = None) -> Optional[object]:
        """
        Safely find an element with timeout and error handling
        
        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Custom timeout (uses default if None)
            
        Returns:
            WebElement if found, None otherwise
        """
        try:
            wait_time = timeout if timeout is not None else self.default_timeout
            wait = WebDriverWait(self.driver, wait_time)
            element = wait.until(EC.presence_of_element_located((by, value)))
            logger.debug(f"Found element: {by}={value}")
            return element
        except TimeoutException:
            logger.warning(f"Timeout finding element: {by}={value}")
            return None
        except Exception as e:
            logger.error(f"Error finding element {by}={value}: {e}")
            return None
    
    def find_elements_safe(self, by: By, value: str) -> List:
        """
        Safely find multiple elements
        
        Args:
            by: Selenium By locator type
            value: Locator value
            
        Returns:
            List of WebElements (empty list if none found)
        """
        try:
            elements = self.driver.find_elements(by, value)
            logger.debug(f"Found {len(elements)} elements: {by}={value}")
            return elements
        except Exception as e:
            logger.error(f"Error finding elements {by}={value}: {e}")
            return []
    
    def click_element(self, by: By, value: str, timeout: int = None) -> bool:
        """
        Click an element with retry logic
        
        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Custom timeout
            
        Returns:
            True if clicked successfully, False otherwise
        """
        try:
            element = self.find_element_safe(by, value, timeout)
            if not element:
                return False
            
            # Wait for element to be clickable
            wait_time = timeout if timeout is not None else self.default_timeout
            wait = WebDriverWait(self.driver, wait_time)
            clickable_element = wait.until(EC.element_to_be_clickable((by, value)))
            
            clickable_element.click()
            logger.info(f"Clicked element: {by}={value}")
            return True
            
        except Exception as e:
            logger.error(f"Error clicking element {by}={value}: {e}")
            return False
    
    def send_keys_safe(self, by: By, value: str, keys: str, clear_first: bool = True, timeout: int = None) -> bool:
        """
        Send keys to an element with error handling
        
        Args:
            by: Selenium By locator type
            value: Locator value
            keys: Keys to send
            clear_first: Clear field before sending keys
            timeout: Custom timeout
            
        Returns:
            True if successful, False otherwise
        """
        try:
            element = self.find_element_safe(by, value, timeout)
            if not element:
                return False
            
            if clear_first:
                element.clear()
            
            element.send_keys(keys)
            logger.info(f"Sent keys to element: {by}={value}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending keys to {by}={value}: {e}")
            return False
    
    def scroll_to_element(self, element) -> bool:
        """
        Scroll to an element
        
        Args:
            element: WebElement to scroll to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)  # Small delay for scroll to complete
            logger.debug("Scrolled to element")
            return True
        except Exception as e:
            logger.error(f"Error scrolling to element: {e}")
            return False
    
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """
        Wait for page to load completely
        
        Args:
            timeout: Maximum time to wait
            
        Returns:
            True if page loaded, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            logger.debug("Page loaded completely")
            return True
        except TimeoutException:
            logger.warning("Page load timeout")
            return False
    
    def take_screenshot(self, filename: str) -> bool:
        """
        Take a screenshot
        
        Args:
            filename: Path to save screenshot
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.driver.save_screenshot(filename)
            logger.info(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return False
    
    def close_driver(self):
        """Close the browser and quit the driver"""
        try:
            self.driver.quit()
            logger.info("WebDriver closed successfully")
        except Exception as e:
            logger.error(f"Error closing WebDriver: {e}")
