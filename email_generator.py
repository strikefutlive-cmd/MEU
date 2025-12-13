"""
Email Generator Module
Handles temporary email creation using mail.tm API
"""
import requests
import logging
import time
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)


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
                import random
                import string
                username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            
            self.email = f"{username}@{domain}"
            self.password = ''.join([chr(random.randint(65, 122)) for _ in range(12)])
            
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
