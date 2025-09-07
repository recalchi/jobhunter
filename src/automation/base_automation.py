import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class BaseAutomation:
    def __init__(self, headless=True):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.setup_logging()
        
    def setup_driver(self):
        """Configura o driver do Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-site-isolation-trials")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        chrome_options.binary_location = "/usr/bin/google-chrome-stable"
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--remote-debugging-port=9222")

        service = Service("./chromedriver-linux64/chromedriver")
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        self.wait = WebDriverWait(self.driver, 10)
        
    def close_driver(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()
            
    def setup_logging(self):
        logging.basicConfig(level=logging.DEBUG, 
                            format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s',
                            datefmt='%H:%M:%S')
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def wait_and_click(self, by, value, timeout=10):
        """Espera um elemento aparecer e clica nele"""
        try:
            self.logger.debug(f"Tentando clicar no elemento: {value} (By: {by})")
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            self.logger.info(f"✅ Clicado no elemento: {value}")
            return True
        except TimeoutException:
            self.logger.error(f"❌ Timeout: Elemento não encontrado ou não clicável: {value}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erro ao clicar no elemento {value}: {str(e)}")
            return False
            
    def wait_and_send_keys(self, by, value, text, timeout=10):
        """Espera um elemento aparecer e envia texto"""
        try:
            self.logger.debug(f"Tentando enviar texto '{text}' para o elemento: {value} (By: {by})")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            element.clear()
            element.send_keys(text)
            self.logger.info(f"✅ Texto '{text}' enviado para o elemento: {value}")
            return True
        except TimeoutException:
            self.logger.error(f"❌ Timeout: Elemento não encontrado para enviar texto: {value}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar texto para o elemento {value}: {str(e)}")
            return False
            
    def wait_for_element(self, by, value, timeout=10):
        """Espera um elemento aparecer"""
        try:
            self.logger.debug(f"Aguardando elemento: {value} (By: {by})")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            self.logger.info(f"✅ Elemento encontrado: {value}")
            return element
        except TimeoutException:
            self.logger.error(f"❌ Timeout: Elemento não encontrado: {value}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Erro ao aguardar elemento {value}: {str(e)}")
            return None
            
    def safe_sleep(self, seconds):
        """Sleep seguro com log"""
        self.logger.info(f"Aguardando {seconds} segundos...")
        time.sleep(seconds)
        
    def scroll_to_bottom(self):
        """Rola a página até o final"""
        self.logger.info("Rolando a página até o final...")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        self.safe_sleep(2)
        
    def scroll_to_element(self, element):
        """Rola até um elemento específico"""
        self.logger.info("Rolando até o elemento...")
        self.driver.execute_script("arguments[0].scrollIntoView();", element)
        self.safe_sleep(1)


