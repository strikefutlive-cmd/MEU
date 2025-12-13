"""
Form Filler Module
Handles intelligent form field recognition and data entry
"""
import logging
import time
from typing import Dict, Any, List
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException
from selenium_utils import SeleniumHelper

logger = logging.getLogger(__name__)


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
