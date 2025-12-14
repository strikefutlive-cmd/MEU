"""
Data Handler Module
Manages test data generation and handling for form filling
"""
import random
import string
import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
        senha = self.generate_password()
        
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
            'senha': senha,
            'confirmar_senha': senha,
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
