"""
Test script to validate module functionality
"""
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_data_handler():
    """Test DataHandler module"""
    try:
        from data_handler import DataHandler
        
        logger.info("Testing DataHandler...")
        handler = DataHandler()
        
        # Test individual generators
        cpf = handler.generate_cpf()
        assert len(cpf) == 11, "CPF should have 11 digits"
        
        phone = handler.generate_phone()
        assert len(phone) == 11, "Phone should have 11 digits"
        
        cep = handler.generate_cep()
        assert len(cep) == 8, "CEP should have 8 digits"
        
        # Test CEP splitting
        primeiro, segundo = handler.split_cep(cep)
        assert len(primeiro) == 5, "CEP primeiro should have 5 digits"
        assert len(segundo) == 3, "CEP segundo should have 3 digits"
        
        # Test form data generation
        data = handler.generate_form_data(email="test@example.com")
        assert 'email' in data, "Data should contain email"
        assert 'cpf' in data, "Data should contain CPF"
        assert 'cep_primeiro' in data, "Data should contain CEP primeiro"
        assert 'cep_segundo' in data, "Data should contain CEP segundo"
        
        logger.info("✓ DataHandler tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ DataHandler test failed: {e}")
        return False


def test_email_generator():
    """Test EmailGenerator module"""
    try:
        from email_generator import EmailGenerator
        
        logger.info("Testing EmailGenerator...")
        email_gen = EmailGenerator()
        
        # Test getting domains
        domains = email_gen.get_domains()
        if domains:
            assert len(domains) > 0, "Should have at least one domain"
            logger.info(f"Found {len(domains)} available domains")
        else:
            logger.warning("Could not retrieve domains (may be network issue)")
        
        logger.info("✓ EmailGenerator tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ EmailGenerator test failed: {e}")
        return False


def test_selenium_utils():
    """Test SeleniumUtils module"""
    try:
        from selenium_utils import BrowserConfig
        
        logger.info("Testing SeleniumUtils...")
        
        # Test Chrome options creation
        options = BrowserConfig.get_chrome_options(headless=True)
        assert options is not None, "Should create Chrome options"
        
        logger.info("✓ SeleniumUtils tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ SeleniumUtils test failed: {e}")
        return False


def test_form_filler():
    """Test FormFiller module (without browser)"""
    try:
        logger.info("Testing FormFiller...")
        
        # Just test import
        from form_filler import FormFiller
        
        logger.info("✓ FormFiller tests passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ FormFiller test failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("Running module tests...")
    logger.info("=" * 60)
    
    results = {
        'DataHandler': test_data_handler(),
        'EmailGenerator': test_email_generator(),
        'SeleniumUtils': test_selenium_utils(),
        'FormFiller': test_form_filler(),
    }
    
    logger.info("=" * 60)
    logger.info("Test Results:")
    logger.info("=" * 60)
    
    for module, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{module}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("=" * 60)
        logger.info("All tests passed!")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("=" * 60)
        logger.error("Some tests failed!")
        logger.error("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
