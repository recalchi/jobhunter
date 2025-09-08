import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import platform
import os
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests


class BaseAutomation:
    def __init__(self, headless=True, captcha_api_key: str = None):
        self.driver = None
        self.wait = None
        self.headless = headless
        self.captcha_api_key = captcha_api_key  # 🔑 chave do 2captcha
        self.setup_logging()
        self.setup_driver()

    def _connect_existing_chrome(self):
        """Tenta conectar em um Chrome já aberto com remote debugging"""
        try:
            chrome_options = Options()
            chrome_options.debugger_address = "127.0.0.1:9222"
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            self.logger.info("✅ Conectado ao Chrome já aberto (remote debugging).")
            return True
        except Exception as e:
            self.logger.warning(f"⚠️ Não foi possível conectar ao Chrome já aberto: {e}")
            return False

    def _solve_recaptcha(self, site_key, url, max_wait=120):
        """Resolve reCAPTCHA v2 via 2Captcha"""
        if not self.captcha_api_key:
            self.logger.error("❌ Nenhuma API key do 2Captcha configurada.")
            return None

        try:
            # Envia solicitação para o 2Captcha
            self.logger.info("🤖 Enviando desafio reCAPTCHA ao 2Captcha...")
            resp = requests.post("http://2captcha.com/in.php", data={
                "key": self.captcha_api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": url,
                "json": 1
            }).json()

            if resp.get("status") != 1:
                self.logger.error(f"❌ Erro ao enviar captcha: {resp}")
                return None

            request_id = resp["request"]

            # Consulta até resolver
            result = None
            for i in range(max_wait // 5):
                self.logger.info(f"⏳ Aguardando resposta do 2Captcha... ({i*5}s)")
                time.sleep(5)
                check = requests.get(f"http://2captcha.com/res.php?key={self.captcha_api_key}&action=get&id={request_id}&json=1").json()
                if check.get("status") == 1:
                    result = check["request"]
                    break

            if not result:
                self.logger.error("❌ Timeout ao resolver reCAPTCHA no 2Captcha.")
                return None

            self.logger.info("✅ reCAPTCHA resolvido com sucesso!")
            return result
        except Exception as e:
            self.logger.error(f"❌ Erro ao resolver reCAPTCHA: {e}")
            return None

    def setup_driver(self):
        """
        Configura o driver:
        1. Conecta ao Chrome já aberto (porta 9222).
        2. Procura aba já logada no LinkedIn (feed).
        3. Se não encontrar, abre nova sessão com perfil Selenium.
        """
        # 🔹 Primeiro tenta conectar no Chrome já aberto
        try:
            chrome_options = Options()
            chrome_options.debugger_address = "127.0.0.1:9222"
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            self.logger.info("✅ Conectado ao Chrome já aberto (remote debugging).")

            # Verifica abas abertas
            found_tab = False
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                url = self.driver.current_url
                title = self.driver.title
                if "linkedin.com/feed" in url or "Feed | LinkedIn" in title:
                    self.logger.info(f"🔗 Aba existente do LinkedIn encontrada: {url}")
                    found_tab = True
                    break

            if not found_tab:
                self.logger.warning("⚠️ Nenhuma aba do LinkedIn encontrada. Abrindo linkedin.com...")
                self.driver.execute_script("window.open('https://www.linkedin.com/feed/');")
                self.driver.switch_to.window(self.driver.window_handles[-1])

            return
        except Exception as e:
            self.logger.warning(f"⚠️ Não foi possível conectar ao Chrome já aberto: {e}")
            self.logger.info("➡️ Iniciando nova sessão do Chrome...")

        # 🔹 Caso falhe, abre nova sessão Selenium (plano B)
        chrome_options = Options()
        automation_profile = os.path.abspath("./chrome_automation_profile")
        os.makedirs(automation_profile, exist_ok=True)

        chrome_options.add_argument(f"user-data-dir={automation_profile}")
        chrome_options.add_argument("profile-directory=Default")
        self.logger.info(f"👤 Usando perfil exclusivo da automação em: {automation_profile}")

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-site-isolation-trials")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.default_content_setting_values.notifications": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        if self.headless:
            chrome_options.add_argument("--headless=new")

        if platform.system().lower() == "linux" and os.path.exists("/usr/bin/google-chrome-stable"):
            chrome_options.binary_location = "/usr/bin/google-chrome-stable"
            service = Service("./chromedriver-linux64/chromedriver")
        else:
            service = Service(ChromeDriverManager().install())

        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
            )
        except Exception as e:
            self.logger.warning(f"⚠️ Não foi possível aplicar stealth mode: {e}")

        self.wait = WebDriverWait(self.driver, 20)
        try:
            self.driver.maximize_window()
        except Exception:
            pass

        self.logger.info("✅ Nova sessão ChromeDriver inicializada com sucesso!")

    def _load_cookies(self):
        """Carrega cookies salvos para evitar login manual"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                self.driver.get("https://www.linkedin.com/")
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                self.driver.refresh()
                self.logger.info("🍪 Cookies carregados, usuário pode estar logado automaticamente.")
            except Exception as e:
                self.logger.warning(f"⚠️ Falha ao carregar cookies: {e}")

    def save_cookies(self):
        """Salva cookies atuais do navegador"""
        try:
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, "w", encoding="utf-8") as f:
                json.dump(cookies, f, indent=2)
            self.logger.info("🍪 Cookies salvos com sucesso.")
        except Exception as e:
            self.logger.warning(f"⚠️ Falha ao salvar cookies: {e}")

    def solve_captcha(self, site_key, url):
        """Usa 2captcha/anticaptcha para resolver captchas"""
        if not self.anticaptcha_key:
            self.logger.error("❌ API key do anticaptcha não configurada.")
            return None

        try:
            # Criar task
            create_task = requests.post(
                "https://api.anti-captcha.com/createTask",
                json={
                    "clientKey": self.anticaptcha_key,
                    "task": {
                        "type": "NoCaptchaTaskProxyless",
                        "websiteURL": url,
                        "websiteKey": site_key
                    }
                }
            ).json()

            task_id = create_task.get("taskId")
            if not task_id:
                self.logger.error(f"❌ Erro ao criar task no anticaptcha: {create_task}")
                return None

            # Esperar resultado
            result = None
            for _ in range(20):  # até ~60s
                time.sleep(3)
                res = requests.post(
                    "https://api.anti-captcha.com/getTaskResult",
                    json={"clientKey": self.anticaptcha_key, "taskId": task_id}
                ).json()
                if res.get("status") == "ready":
                    result = res["solution"]["gRecaptchaResponse"]
                    break

            if result:
                self.logger.info("✅ Captcha resolvido automaticamente via anticaptcha.")
            else:
                self.logger.error("❌ Timeout ao tentar resolver captcha.")
            return result
        except Exception as e:
            self.logger.error(f"❌ Erro no solve_captcha: {e}")
            return None

    def close_driver(self):
        """Fecha o driver e salva cookies"""
        if self.driver:
            self.save_cookies()
            self.driver.quit()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        )
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
