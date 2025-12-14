"""
Consolidated Form Automation Script - All-in-One Version

This single-file script consolidates all features from multiple automation scripts:
1. Temporary email creation using mail.tm
2. Robust field recognition and data filling (including CEP_PRIMEIRO and CEP_SEGUNDO)
3. Comprehensive error handling and logging
4. Compatible browser configurations

All modules are included in this single file for easy deployment and use.
"""

import requests
import logging
import time
import random
import string
import sys
import argparse
from typing import Optional, Dict, Tuple, Any, List
from datetime import datetime, timedelta
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


# ==================== EMAIL GENERATOR ====================

class EmailGenerator:
    """Handles temporary email creation and management using mail.tm"""
    
    BASE_URL = "https://api.mail.tm"
    
    def __init__(self):
        self.session = requests.Session()
        self.email = None
        self.password = None
        self.token = None
        self.account_id = None
        
    def get_domains(self) -> Optional[list]:
        """Get available domains from mail.tm"""
        try:
            response = self.session.get(f"{self.BASE_URL}/domains")
            response.raise_for_status()
            domains = response.json().get("hydra:member", [])
            logger.info(f"Retrieved {len(domains)} available domains")
            return domains
        except Exception as e:
            logger.error(f"Error getting domains: {e}")
            return None
    
    def create_account(self, username: str = None) -> Optional[Tuple[str, str]]:
        """
        Create a new temporary email account
        
        Args:
            username: Optional username for the email. If None, generates random.
            
        Returns:
            Tuple of (email, password) if successful, None otherwise
        """
        try:
            # Get available domains
            domains = self.get_domains()
            if not domains:
                logger.error("No domains available")
                return None
            
            # Use first available domain
            domain = domains[0].get("domain")
            
            # Generate username if not provided
            if not username:
                username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            
            self.email = f"{username}@{domain}"
            # Generate secure password with letters, digits, and special characters
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            self.password = ''.join(random.choice(chars) for _ in range(12))
            
            # Create account
            payload = {
                "address": self.email,
                "password": self.password
            }
            
            response = self.session.post(f"{self.BASE_URL}/accounts", json=payload)
            response.raise_for_status()
            
            account_data = response.json()
            self.account_id = account_data.get("id")
            
            logger.info(f"Successfully created email account: {self.email}")
            return self.email, self.password
            
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            return None
    
    def login(self) -> Optional[str]:
        """
        Login to the email account and get authentication token
        
        Returns:
            Authentication token if successful, None otherwise
        """
        try:
            payload = {
                "address": self.email,
                "password": self.password
            }
            
            response = self.session.post(f"{self.BASE_URL}/token", json=payload)
            response.raise_for_status()
            
            self.token = response.json().get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            
            logger.info(f"Successfully logged in to {self.email}")
            return self.token
            
        except Exception as e:
            logger.error(f"Error logging in: {e}")
            return None
    
    def get_messages(self, page: int = 1) -> Optional[list]:
        """
        Get messages from the inbox
        
        Args:
            page: Page number for pagination
            
        Returns:
            List of messages if successful, None otherwise
        """
        try:
            if not self.token:
                logger.warning("Not logged in, attempting to login")
                if not self.login():
                    return None
            
            response = self.session.get(f"{self.BASE_URL}/messages?page={page}")
            response.raise_for_status()
            
            messages = response.json().get("hydra:member", [])
            logger.info(f"Retrieved {len(messages)} messages")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return None
    
    def get_message_content(self, message_id: str) -> Optional[Dict]:
        """
        Get full content of a specific message
        
        Args:
            message_id: ID of the message to retrieve
            
        Returns:
            Message content if successful, None otherwise
        """
        try:
            if not self.token:
                logger.warning("Not logged in, attempting to login")
                if not self.login():
                    return None
            
            response = self.session.get(f"{self.BASE_URL}/messages/{message_id}")
            response.raise_for_status()
            
            logger.info(f"Retrieved message content for ID: {message_id}")
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting message content: {e}")
            return None
    
    def wait_for_email(self, timeout: int = 60, check_interval: int = 5) -> Optional[Dict]:
        """
        Wait for an email to arrive
        
        Args:
            timeout: Maximum time to wait in seconds
            check_interval: Time between checks in seconds
            
        Returns:
            First message received if successful, None otherwise
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            messages = self.get_messages()
            if messages and len(messages) > 0:
                logger.info("Email received")
                return messages[0]
            
            logger.debug(f"No email yet, waiting {check_interval} seconds...")
            time.sleep(check_interval)
        
        logger.warning(f"No email received within {timeout} seconds")
        return None
    
    def cleanup(self):
        """Delete the temporary email account"""
        try:
            if not self.token or not self.account_id:
                logger.warning("Cannot cleanup: not logged in or no account ID")
                return False
            
            response = self.session.delete(f"{self.BASE_URL}/accounts/{self.account_id}")
            response.raise_for_status()
            
            logger.info(f"Successfully deleted account: {self.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting account: {e}")
            return False


# ==================== DATA HANDLER ====================

class DataHandler:
    """Handles generation and management of form data"""
    
    # Brazilian area codes (DDD)
    AREA_CODES = ['11', '12', '13', '14', '15', '16', '17', '18', '19',  # São Paulo
                  '21', '22', '24',  # Rio de Janeiro
                  '27', '28',  # Espírito Santo
                  '31', '32', '33', '34', '35', '37', '38',  # Minas Gerais
                  '41', '42', '43', '44', '45', '46',  # Paraná
                  '47', '48', '49',  # Santa Catarina
                  '51', '53', '54', '55',  # Rio Grande do Sul
                  '61',  # Distrito Federal
                  '62', '64',  # Goiás
                  '63',  # Tocantins
                  '65', '66',  # Mato Grosso
                  '67',  # Mato Grosso do Sul
                  '68',  # Acre
                  '69',  # Rondônia
                  '71', '73', '74', '75', '77',  # Bahia
                  '79',  # Sergipe
                  '81', '87',  # Pernambuco
                  '82',  # Alagoas
                  '83',  # Paraíba
                  '84',  # Rio Grande do Norte
                  '85', '88',  # Ceará
                  '86', '89',  # Piauí
                  '91', '93', '94',  # Pará
                  '92', '97',  # Amazonas
                  '95',  # Roraima
                  '96',  # Amapá
                  '98', '99']  # Maranhão
    
    def __init__(self):
        self.data = {}
    
    @staticmethod
    def generate_name(first_name: bool = True) -> str:
        """Generate a random name"""
        first_names = [
            "João", "Maria", "Pedro", "Ana", "Carlos", "Julia", 
            "Lucas", "Mariana", "Rafael", "Beatriz", "Gabriel", "Laura"
        ]
        last_names = [
            "Silva", "Santos", "Oliveira", "Souza", "Costa", "Ferreira",
            "Rodrigues", "Almeida", "Nascimento", "Lima", "Araújo", "Fernandes"
        ]
        
        if first_name:
            return random.choice(first_names)
        return random.choice(last_names)
    
    @staticmethod
    def generate_cpf() -> str:
        """Generate a valid CPF number (Brazilian ID)"""
        def calculate_digit(digits):
            s = sum(int(digit) * weight for digit, weight in zip(digits, range(len(digits) + 1, 1, -1)))
            remainder = s % 11
            return '0' if remainder < 2 else str(11 - remainder)
        
        # Generate first 9 digits
        cpf = [str(random.randint(0, 9)) for _ in range(9)]
        
        # Calculate first verification digit
        cpf.append(calculate_digit(cpf))
        
        # Calculate second verification digit
        cpf.append(calculate_digit(cpf))
        
        cpf_str = ''.join(cpf)
        logger.debug(f"Generated CPF: {cpf_str}")
        return cpf_str
    
    @classmethod
    def generate_phone(cls) -> str:
        """Generate a Brazilian phone number"""
        ddd = random.choice(cls.AREA_CODES)
        number = '9' + ''.join([str(random.randint(0, 9)) for _ in range(8)])
        phone = f"{ddd}{number}"
        logger.debug(f"Generated phone: {phone}")
        return phone
    
    @staticmethod
    def generate_cep() -> str:
        """Generate a Brazilian postal code (CEP)"""
        cep = ''.join([str(random.randint(0, 9)) for _ in range(8)])
        logger.debug(f"Generated CEP: {cep}")
        return cep
    
    @staticmethod
    def split_cep(cep: str) -> tuple:
        """
        Split CEP into two parts for forms that require separate fields
        
        Args:
            cep: CEP string (8 digits)
            
        Returns:
            Tuple of (first_5_digits, last_3_digits)
        """
        if len(cep) < 8:
            cep = cep.zfill(8)
        
        primeiro = cep[:5]
        segundo = cep[5:8]
        logger.debug(f"Split CEP {cep} into: {primeiro}-{segundo}")
        return primeiro, segundo
    
    @staticmethod
    def generate_date_of_birth(min_age: int = 18, max_age: int = 80) -> str:
        """
        Generate a random date of birth
        
        Args:
            min_age: Minimum age in years
            max_age: Maximum age in years
            
        Returns:
            Date string in DD/MM/YYYY format
        """
        today = datetime.now()
        min_date = today - timedelta(days=max_age * 365)
        max_date = today - timedelta(days=min_age * 365)
        
        random_days = random.randint(0, (max_date - min_date).days)
        birth_date = min_date + timedelta(days=random_days)
        
        date_str = birth_date.strftime("%d/%m/%Y")
        logger.debug(f"Generated date of birth: {date_str}")
        return date_str
    
    @staticmethod
    def generate_password(length: int = 12, include_special: bool = True) -> str:
        """
        Generate a random password
        
        Args:
            length: Length of the password
            include_special: Whether to include special characters
            
        Returns:
            Random password string
        """
        chars = string.ascii_letters + string.digits
        if include_special:
            chars += "!@#$%^&*"
        
        password = ''.join(random.choice(chars) for _ in range(length))
        logger.debug("Generated password")
        return password
    
    def generate_form_data(self, email: str = None) -> Dict[str, Any]:
        """
        Generate a complete set of form data
        
        Args:
            email: Optional email address to use
            
        Returns:
            Dictionary containing all form fields
        """
        cep = self.generate_cep()
        cep_primeiro, cep_segundo = self.split_cep(cep)
        
        data = {
            'nome': self.generate_name(True),
            'sobrenome': self.generate_name(False),
            'nome_completo': f"{self.generate_name(True)} {self.generate_name(False)}",
            'email': email or f"test{random.randint(1000, 9999)}@example.com",
            'cpf': self.generate_cpf(),
            'telefone': self.generate_phone(),
            'celular': self.generate_phone(),
            'cep': cep,
            'cep_primeiro': cep_primeiro,
            'cep_segundo': cep_segundo,
            'data_nascimento': self.generate_date_of_birth(),
            'senha': self.generate_password(),
        }
        
        self.data = data
        logger.info("Generated complete form data")
        return data
    
    def get_field_value(self, field_name: str) -> Any:
        """
        Get value for a specific field
        
        Args:
            field_name: Name of the field
            
        Returns:
            Field value if exists, None otherwise
        """
        return self.data.get(field_name.lower())
    
    def set_field_value(self, field_name: str, value: Any):
        """
        Set value for a specific field
        
        Args:
            field_name: Name of the field
            value: Value to set
        """
        self.data[field_name.lower()] = value
        logger.debug(f"Set field {field_name} to {value}")


# ==================== BROWSER CONFIG & SELENIUM UTILITIES ====================

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


# ==================== FORM FILLER ====================

class FormFiller:
    """Handles form field recognition and filling with robust strategies"""
    
    def __init__(self, selenium_helper: SeleniumHelper):
        self.helper = selenium_helper
        self.driver = selenium_helper.driver
        
        # Field mapping strategies - maps field types to possible identifiers
        self.field_patterns = {
            'email': ['email', 'e-mail', 'mail', 'usuario', 'login'],
            'nome': ['nome', 'name', 'firstname', 'primeironome'],
            'sobrenome': ['sobrenome', 'lastname', 'ultimonome', 'surname'],
            'nome_completo': ['nomecompleto', 'fullname', 'nomeinteiro'],
            'cpf': ['cpf', 'documento', 'doc'],
            'telefone': ['telefone', 'phone', 'tel', 'fone'],
            'celular': ['celular', 'mobile', 'cel'],
            'cep': ['cep', 'postalcode', 'zipcode'],
            'cep_primeiro': ['cep1', 'cepprimeiro', 'cep_1', 'zip1'],
            'cep_segundo': ['cep2', 'cepsegundo', 'cep_2', 'zip2'],
            'data_nascimento': ['nascimento', 'datanascimento', 'dob', 'birthday', 'birthdate'],
            'senha': ['senha', 'password', 'pass', 'pwd'],
            'confirmar_senha': ['confirmarsenha', 'confirmpassword', 'confirmsenha', 'senha2'],
        }
    
    def _normalize_string(self, s: str) -> str:
        """Normalize string for comparison (lowercase, no spaces)"""
        return s.lower().replace(' ', '').replace('-', '').replace('_', '')
    
    def _matches_pattern(self, field_id: str, patterns: List[str]) -> bool:
        """
        Check if field ID matches any pattern
        
        Args:
            field_id: Field identifier (id, name, etc.)
            patterns: List of patterns to match
            
        Returns:
            True if matches any pattern, False otherwise
        """
        normalized_id = self._normalize_string(field_id)
        for pattern in patterns:
            if pattern in normalized_id:
                logger.debug(f"Field '{field_id}' matches pattern '{pattern}'")
                return True
        return False
    
    def find_field_by_patterns(self, field_type: str) -> List:
        """
        Find form fields matching a field type using multiple strategies
        
        Args:
            field_type: Type of field to find (e.g., 'email', 'nome', 'cep_primeiro')
            
        Returns:
            List of matching elements
        """
        if field_type not in self.field_patterns:
            logger.warning(f"Unknown field type: {field_type}")
            return []
        
        patterns = self.field_patterns[field_type]
        matching_elements = []
        
        # Strategy 1: Find by ID
        for pattern in patterns:
            elements = self.helper.find_elements_safe(By.CSS_SELECTOR, f"input[id*='{pattern}']")
            matching_elements.extend(elements)
            
            elements = self.helper.find_elements_safe(By.CSS_SELECTOR, f"textarea[id*='{pattern}']")
            matching_elements.extend(elements)
        
        # Strategy 2: Find by name attribute
        for pattern in patterns:
            elements = self.helper.find_elements_safe(By.CSS_SELECTOR, f"input[name*='{pattern}']")
            matching_elements.extend(elements)
            
            elements = self.helper.find_elements_safe(By.CSS_SELECTOR, f"textarea[name*='{pattern}']")
            matching_elements.extend(elements)
        
        # Strategy 3: Find by placeholder
        for pattern in patterns:
            elements = self.helper.find_elements_safe(By.CSS_SELECTOR, f"input[placeholder*='{pattern}']")
            matching_elements.extend(elements)
        
        # Strategy 4: Find by label text
        try:
            labels = self.driver.find_elements(By.TAG_NAME, "label")
            for label in labels:
                label_text = self._normalize_string(label.text)
                for pattern in patterns:
                    if pattern in label_text:
                        # Try to find associated input
                        label_for = label.get_attribute("for")
                        if label_for:
                            element = self.helper.find_element_safe(By.ID, label_for)
                            if element:
                                matching_elements.append(element)
        except (AttributeError, StaleElementReferenceException) as e:
            logger.debug(f"Error in label strategy: {e}")
        
        # Remove duplicates while preserving order
        unique_elements = []
        seen = set()
        for elem in matching_elements:
            try:
                elem_id = id(elem)
                if elem_id not in seen:
                    seen.add(elem_id)
                    unique_elements.append(elem)
            except (AttributeError, StaleElementReferenceException):
                # Element may have become stale, skip it
                pass
        
        if unique_elements:
            logger.info(f"Found {len(unique_elements)} fields for type '{field_type}'")
        else:
            logger.warning(f"No fields found for type '{field_type}'")
        
        return unique_elements
    
    def fill_field(self, field_type: str, value: str, retry: int = 2) -> bool:
        """
        Fill a field with the given value
        
        Args:
            field_type: Type of field to fill
            value: Value to fill
            retry: Number of retries on failure
            
        Returns:
            True if successfully filled, False otherwise
        """
        for attempt in range(retry + 1):
            try:
                elements = self.find_field_by_patterns(field_type)
                
                if not elements:
                    logger.warning(f"No fields found for '{field_type}' (attempt {attempt + 1}/{retry + 1})")
                    if attempt < retry:
                        time.sleep(1)
                        continue
                    return False
                
                # Try to fill the first visible and enabled element
                for element in elements:
                    try:
                        if element.is_displayed() and element.is_enabled():
                            # Scroll to element
                            self.helper.scroll_to_element(element)
                            
                            # Clear and fill
                            element.clear()
                            element.send_keys(value)
                            
                            logger.info(f"Successfully filled '{field_type}' with value")
                            return True
                    except Exception as e:
                        logger.debug(f"Could not fill element: {e}")
                        continue
                
                logger.warning(f"All found elements for '{field_type}' were not fillable")
                if attempt < retry:
                    time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error filling field '{field_type}': {e}")
                if attempt < retry:
                    time.sleep(1)
        
        return False
    
    def fill_form(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """
        Fill an entire form with provided data
        
        Args:
            data: Dictionary mapping field types to values
            
        Returns:
            Dictionary mapping field types to success status
        """
        results = {}
        
        logger.info(f"Starting to fill form with {len(data)} fields")
        
        for field_type, value in data.items():
            if value is None:
                logger.debug(f"Skipping field '{field_type}' - no value provided")
                results[field_type] = False
                continue
            
            success = self.fill_field(field_type, str(value))
            results[field_type] = success
            
            # Small delay between fields
            time.sleep(0.5)
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Form filling complete: {successful}/{len(data)} fields filled successfully")
        
        return results
    
    def handle_special_fields(self, data: Dict[str, Any]) -> bool:
        """
        Handle special field cases like CEP_PRIMEIRO and CEP_SEGUNDO
        
        Args:
            data: Data dictionary containing field values
            
        Returns:
            True if all special fields handled successfully
        """
        success = True
        
        # Handle split CEP fields
        if 'cep_primeiro' in data or 'cep_segundo' in data:
            logger.info("Handling split CEP fields")
            
            if 'cep_primeiro' in data:
                if not self.fill_field('cep_primeiro', data['cep_primeiro']):
                    logger.warning("Failed to fill CEP_PRIMEIRO")
                    success = False
            
            if 'cep_segundo' in data:
                if not self.fill_field('cep_segundo', data['cep_segundo']):
                    logger.warning("Failed to fill CEP_SEGUNDO")
                    success = False
        
        # Handle single CEP field if split fields not found
        elif 'cep' in data:
            logger.info("Handling single CEP field")
            if not self.fill_field('cep', data['cep']):
                logger.warning("Failed to fill CEP")
                success = False
        
        return success
    
    def submit_form(self, button_texts: List[str] = None) -> bool:
        """
        Find and click the submit button
        
        Args:
            button_texts: List of possible button texts to look for
            
        Returns:
            True if button clicked successfully, False otherwise
        """
        if button_texts is None:
            button_texts = ['submit', 'enviar', 'cadastrar', 'registrar', 'continuar', 'próximo']
        
        # Try to find submit button by text
        for text in button_texts:
            try:
                # Try button elements
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if text.lower() in button.text.lower():
                        if button.is_displayed() and button.is_enabled():
                            self.helper.scroll_to_element(button)
                            button.click()
                            logger.info(f"Clicked submit button with text: {button.text}")
                            return True
                
                # Try input[type=submit]
                submits = self.driver.find_elements(By.CSS_SELECTOR, "input[type='submit']")
                for submit in submits:
                    value = submit.get_attribute("value") or ""
                    if text.lower() in value.lower():
                        if submit.is_displayed() and submit.is_enabled():
                            self.helper.scroll_to_element(submit)
                            submit.click()
                            logger.info(f"Clicked submit input with value: {value}")
                            return True
                
            except Exception as e:
                logger.debug(f"Error trying button text '{text}': {e}")
        
        logger.warning("Could not find submit button")
        return False


# ==================== MAIN AUTOMATION CLASS ====================

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


# ==================== MAIN ENTRY POINT ====================

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description='Automated form filling with temporary email generation - All-in-One Version'
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
