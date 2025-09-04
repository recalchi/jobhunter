import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class BaseAutomation:
    def __init__(self, headless=True):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def setup_driver(self):
        """Configura o driver do Chrome"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def close_driver(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()
            
    def wait_and_click(self, by, value, timeout=10):
        """Espera um elemento aparecer e clica nele"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            return True
        except TimeoutException:
            self.logger.error(f"Elemento não encontrado para clicar: {value}")
            return False
            
    def wait_and_send_keys(self, by, value, text, timeout=10):
        """Espera um elemento aparecer e envia texto"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            element.clear()
            element.send_keys(text)
            return True
        except TimeoutException:
            self.logger.error(f"Elemento não encontrado para enviar texto: {value}")
            return False
            
    def wait_for_element(self, by, value, timeout=10):
        """Espera um elemento aparecer"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.error(f"Elemento não encontrado: {value}")
            return None
            
    def safe_sleep(self, seconds):
        """Sleep seguro com log"""
        self.logger.info(f"Aguardando {seconds} segundos...")
        time.sleep(seconds)
        
    def scroll_to_bottom(self):
        """Rola a página até o final"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.safe_sleep(2)
        
    def scroll_to_element(self, element):
        """Rola até um elemento específico"""
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        self.safe_sleep(1)

