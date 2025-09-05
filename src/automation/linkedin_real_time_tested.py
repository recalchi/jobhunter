import time
import random
import logging
import os
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class LinkedInRealTimeTested:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.applied_jobs = []
        self.failed_applications = []
        self.setup_logging()
        
        # URLs baseadas no teste em tempo real
        self.login_url = "https://www.linkedin.com/checkpoint/lg/sign-in-another-account"
        self.jobs_home_url = "https://www.linkedin.com/jobs"
        self.recommended_jobs_url = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4278856149&discover=recommended&discoveryOrigin=JOBS_HOME_JYMBII"
        
        # Contador de screenshots para debug
        self.screenshot_counter = 0
        
    def setup_logging(self):
        """Configura o logging detalhado"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def detailed_log(self, message, level="INFO"):
        """Log detalhado com timestamp e formatação clara"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] LinkedIn Real: {message}"
        self.logger.info(formatted_message)
        print(formatted_message)
        
    def take_debug_screenshot(self, step_name):
        """Tira screenshot para debug com nome descritivo"""
        try:
            if self.driver:
                self.screenshot_counter += 1
                filename = f"linkedin_step_{self.screenshot_counter:02d}_{step_name}.png"
                filepath = os.path.join("/tmp", filename)
                self.driver.save_screenshot(filepath)
                self.detailed_log(f"📸 Screenshot salvo: {filename}")
                return filepath
        except Exception as e:
            self.detailed_log(f"Erro ao salvar screenshot: {str(e)}", "WARNING")
        return None
        
    def setup_driver(self):
        """Configura o driver do Chrome com opções limpas"""
        try:
            self.detailed_log("=== ETAPA 1: CONFIGURANDO DRIVER DO CHROME ===", "SUCCESS")
            
            chrome_options = Options()
            
            # Configurações básicas para inicialização limpa
            if self.headless:
                chrome_options.add_argument("--headless")
                self.detailed_log("Modo headless ativado")
            else:
                self.detailed_log("Modo visual ativado (recomendado para debug)")
            
            # Argumentos para Chrome limpo
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Configurações para evitar problemas de inicialização
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-session-crashed-bubble")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # User agent realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.detailed_log("Iniciando Chrome WebDriver...")
            
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.detailed_log("✅ Chrome WebDriver iniciado com sucesso!")
            except WebDriverException as e:
                self.detailed_log(f"❌ Erro ao iniciar Chrome: {str(e)}", "ERROR")
                self.detailed_log("💡 Dica: Verifique se não há processos do Chrome rodando em segundo plano", "INFO")
                return False
            
            # Remove propriedades de automação para parecer mais humano
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 15)
            
            # Screenshot inicial
            self.take_debug_screenshot("driver_setup_success")
            
            return True
            
        except Exception as e:
            self.detailed_log(f"❌ Erro geral ao configurar driver: {str(e)}", "ERROR")
            return False
            
    def step_1_navigate_to_login(self):
        """ETAPA 1: Navegar para página de login (baseado no teste real)"""
        try:
            self.detailed_log("=== ETAPA 2: NAVEGANDO PARA PÁGINA DE LOGIN ===", "SUCCESS")
            
            self.detailed_log(f"Navegando para: {self.login_url}")
            self.driver.get(self.login_url)
            
            self.detailed_log("Aguardando carregamento da página de login...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.detailed_log(f"URL atual: {current_url}")
            self.detailed_log(f"Título da página: {page_title}")
            
            # Screenshot da página de login
            self.take_debug_screenshot("login_page_loaded")
            
            # Verifica se chegou na página de login
            if "linkedin.com" in current_url and ("login" in current_url or "sign-in" in current_url or "checkpoint" in current_url):
                self.detailed_log("✅ Chegou na página de login do LinkedIn", "SUCCESS")
                return True
            else:
                self.detailed_log(f"❌ URL inesperada: {current_url}", "ERROR")
                return False
                
        except Exception as e:
            self.detailed_log(f"❌ Erro ao navegar para login: {str(e)}", "ERROR")
            self.take_debug_screenshot("login_navigation_error")
            return False
            
    def step_2_fill_login_form(self, username, password):
        """ETAPA 2: Preencher formulário de login (baseado no teste real)"""
        try:
            self.detailed_log("=== ETAPA 3: PREENCHENDO FORMULÁRIO DE LOGIN ===", "SUCCESS")
            
            # Procura campo de email (baseado no teste: index 3, placeholder=" ")
            self.detailed_log("Procurando campo de email...")
            
            email_selectors = [
                "input[placeholder=' ']",  # Baseado no teste real
                "input[name='session_key']",
                "input[id='username']",
                "input[type='email']",
                "input[aria-label*='Email']"
            ]
            
            email_field = None
            for i, selector in enumerate(email_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if email_field.is_displayed():
                        self.detailed_log(f"✅ Campo de email encontrado: {selector}")
                        break
                    else:
                        email_field = None
                except NoSuchElementException:
                    self.detailed_log(f"Seletor não encontrado: {selector}")
                    continue
                    
            if not email_field:
                self.detailed_log("❌ Campo de email não encontrado", "ERROR")
                self.take_debug_screenshot("email_field_not_found")
                return False
                
            # Preenche email
            self.detailed_log(f"Preenchendo email: {username}")
            email_field.clear()
            time.sleep(1)
            
            # Digita email de forma humana
            for char in username:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
            self.detailed_log("✅ Email preenchido com sucesso")
            
            # Screenshot após preencher email
            self.take_debug_screenshot("email_filled")
            
            # Procura campo de senha (baseado no teste: index 5, aria-label="Password")
            self.detailed_log("Procurando campo de senha...")
            
            password_selectors = [
                "input[aria-label='Password']",  # Baseado no teste real
                "input[name='session_password']",
                "input[id='password']",
                "input[type='password']"
            ]
            
            password_field = None
            for i, selector in enumerate(password_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field.is_displayed():
                        self.detailed_log(f"✅ Campo de senha encontrado: {selector}")
                        break
                    else:
                        password_field = None
                except NoSuchElementException:
                    self.detailed_log(f"Seletor não encontrado: {selector}")
                    continue
                    
            if not password_field:
                self.detailed_log("❌ Campo de senha não encontrado", "ERROR")
                self.take_debug_screenshot("password_field_not_found")
                return False
                
            # Preenche senha
            self.detailed_log("Preenchendo senha...")
            password_field.clear()
            time.sleep(1)
            
            # Digita senha de forma humana
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
            self.detailed_log("✅ Senha preenchida com sucesso")
            
            # Screenshot após preencher senha
            self.take_debug_screenshot("password_filled")
            
            return True
            
        except Exception as e:
            self.detailed_log(f"❌ Erro ao preencher formulário: {str(e)}", "ERROR")
            self.take_debug_screenshot("form_fill_error")
            return False
            
    def step_3_submit_login(self):
        """ETAPA 3: Submeter formulário de login (baseado no teste real)"""
        try:
            self.detailed_log("=== ETAPA 4: SUBMETENDO FORMULÁRIO DE LOGIN ===", "SUCCESS")
            
            # Procura botão de login (baseado no teste: index 9, texto "Sign in")
            self.detailed_log("Procurando botão de login...")
            
            login_button_selectors = [
                "button:contains('Sign in')",  # Baseado no teste real
                "button[type='submit']",
                "input[type='submit']",
                ".btn-primary",
                "button[data-litms-control-urn]"
            ]
            
            login_button = None
            for i, selector in enumerate(login_button_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    if ":contains" in selector:
                        # Para seletores com texto, usa XPath
                        login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Sign in')]")
                    else:
                        login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                    if login_button.is_displayed() and login_button.is_enabled():
                        self.detailed_log(f"✅ Botão de login encontrado: {selector}")
                        self.detailed_log(f"Texto do botão: {login_button.text}")
                        break
                    else:
                        login_button = None
                except Exception as e:
                    self.detailed_log(f"Seletor não encontrado: {selector}")
                    continue
                    
            if not login_button:
                self.detailed_log("❌ Botão de login não encontrado", "ERROR")
                self.take_debug_screenshot("login_button_not_found")
                return False
                
            # Clica no botão de login
            self.detailed_log("Clicando no botão de login...")
            login_button.click()
            
            self.detailed_log("Aguardando resposta do servidor...")
            time.sleep(8)  # Aguarda mais tempo para processar login
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.detailed_log(f"URL após login: {current_url}")
            self.detailed_log(f"Título após login: {page_title}")
            
            # Screenshot após login
            self.take_debug_screenshot("after_login_submit")
            
            # Verifica resultado do login
            return self.check_login_result()
            
        except Exception as e:
            self.detailed_log(f"❌ Erro ao submeter login: {str(e)}", "ERROR")
            self.take_debug_screenshot("login_submit_error")
            return False
            
    def check_login_result(self):
        """Verifica o resultado do login e identifica próximos passos"""
        try:
            self.detailed_log("=== VERIFICANDO RESULTADO DO LOGIN ===", "INFO")
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Verifica se foi redirecionado para verificação de segurança (baseado no teste real)
            if "checkpoint/challenge" in current_url or "security verification" in page_source:
                self.detailed_log("⚠️ VERIFICAÇÃO DE SEGURANÇA DETECTADA", "WARNING")
                self.detailed_log("Título: Security Verification | LinkedIn")
                self.detailed_log("Mensagem: Let's do a quick security check")
                
                # Procura elementos de verificação
                security_elements = [
                    "start puzzle",
                    "protecting your account",
                    "solve this puzzle",
                    "security check"
                ]
                
                for element_text in security_elements:
                    if element_text in page_source:
                        self.detailed_log(f"Elemento de segurança encontrado: {element_text}")
                        
                self.detailed_log("🔐 AÇÃO NECESSÁRIA: Verificação de segurança manual", "WARNING")
                self.detailed_log("A automação pausará aqui para permitir intervenção manual", "INFO")
                
                return "security_verification"
                
            # Verifica se login foi bem-sucedido (redirecionado para feed ou área logada)
            elif "feed" in current_url or "linkedin.com/in/" in current_url or "mynetwork" in current_url:
                self.detailed_log("✅ LOGIN BEM-SUCEDIDO!", "SUCCESS")
                self.detailed_log("Usuário foi redirecionado para área logada")
                return "login_success"
                
            # Verifica se houve erro de credenciais
            elif "login" in current_url or "sign-in" in current_url:
                error_indicators = [
                    "incorrect email",
                    "wrong password",
                    "couldn't sign you in",
                    "please check",
                    "error"
                ]
                
                for error_text in error_indicators:
                    if error_text in page_source:
                        self.detailed_log(f"❌ ERRO DE LOGIN DETECTADO: {error_text}", "ERROR")
                        return "login_error"
                        
                self.detailed_log("⚠️ Ainda na página de login - possível erro", "WARNING")
                return "login_error"
                
            else:
                self.detailed_log(f"⚠️ Estado de login incerto - URL: {current_url}", "WARNING")
                return "uncertain"
                
        except Exception as e:
            self.detailed_log(f"Erro ao verificar resultado do login: {str(e)}", "WARNING")
            return "error"
            
    def handle_security_verification(self, timeout_minutes=5):
        """Lida com verificação de segurança - pausa para intervenção manual"""
        try:
            self.detailed_log("=== LIDANDO COM VERIFICAÇÃO DE SEGURANÇA ===", "WARNING")
            self.detailed_log("🔐 INTERVENÇÃO MANUAL NECESSÁRIA", "WARNING")
            self.detailed_log("Por favor, complete a verificação de segurança manualmente no navegador", "INFO")
            self.detailed_log(f"A automação aguardará por {timeout_minutes} minutos...", "INFO")
            
            start_time = time.time()
            timeout_seconds = timeout_minutes * 60
            
            while time.time() - start_time < timeout_seconds:
                current_url = self.driver.current_url
                
                # Verifica se saiu da página de verificação
                if "checkpoint/challenge" not in current_url:
                    self.detailed_log("✅ Verificação de segurança concluída!", "SUCCESS")
                    self.detailed_log(f"Nova URL: {current_url}")
                    
                    # Screenshot após verificação
                    self.take_debug_screenshot("security_verification_completed")
                    
                    return True
                    
                # Aguarda 10 segundos antes de verificar novamente
                time.sleep(10)
                remaining_time = timeout_seconds - (time.time() - start_time)
                self.detailed_log(f"Aguardando verificação manual... {remaining_time/60:.1f} min restantes")
                
            self.detailed_log("⏰ Timeout atingido - verificação não foi concluída", "WARNING")
            return False
            
        except Exception as e:
            self.detailed_log(f"Erro durante verificação de segurança: {str(e)}", "ERROR")
            return False
            
    def step_4_navigate_to_jobs(self):
        """ETAPA 4: Navegar para seção de vagas após login bem-sucedido"""
        try:
            self.detailed_log("=== ETAPA 5: NAVEGANDO PARA SEÇÃO DE VAGAS ===", "SUCCESS")
            
            self.detailed_log(f"Navegando para: {self.jobs_home_url}")
            self.driver.get(self.jobs_home_url)
            
            self.detailed_log("Aguardando carregamento da página de vagas...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.detailed_log(f"URL atual: {current_url}")
            self.detailed_log(f"Título da página: {page_title}")
            
            # Screenshot da página de vagas
            self.take_debug_screenshot("jobs_page_loaded")
            
            # Verifica se chegou na página de vagas
            if "jobs" in current_url:
                self.detailed_log("✅ Chegou na página de vagas", "SUCCESS")
                return True
            elif "login" in current_url:
                self.detailed_log("❌ Redirecionado para login - sessão pode ter expirado", "ERROR")
                return False
            else:
                self.detailed_log(f"⚠️ URL inesperada: {current_url}", "WARNING")
                return False
                
        except Exception as e:
            self.detailed_log(f"❌ Erro ao navegar para vagas: {str(e)}", "ERROR")
            self.take_debug_screenshot("jobs_navigation_error")
            return False
            
    def run_full_automation(self, username, password, job_types=None, max_applications=3):
        """Executa automação completa baseada no teste em tempo real"""
        try:
            self.detailed_log("🚀 INICIANDO AUTOMAÇÃO LINKEDIN (BASEADA EM TESTE REAL) 🚀", "SUCCESS")
            
            # Etapa 1: Configurar driver
            if not self.setup_driver():
                return {"success": False, "error": "Falha ao configurar driver"}
                
            # Etapa 2: Navegar para login
            if not self.step_1_navigate_to_login():
                return {"success": False, "error": "Falha ao navegar para página de login"}
                
            # Etapa 3: Preencher formulário
            if not self.step_2_fill_login_form(username, password):
                return {"success": False, "error": "Falha ao preencher formulário de login"}
                
            # Etapa 4: Submeter login
            login_result = self.step_3_submit_login()
            
            if login_result == "security_verification":
                # Pausa para verificação manual
                if not self.handle_security_verification():
                    return {"success": False, "error": "Verificação de segurança não concluída"}
            elif login_result == "login_error":
                return {"success": False, "error": "Erro nas credenciais de login"}
            elif login_result != "login_success" and login_result != "security_verification":
                return {"success": False, "error": f"Resultado de login inesperado: {login_result}"}
                
            # Etapa 5: Navegar para vagas
            if not self.step_4_navigate_to_jobs():
                return {"success": False, "error": "Falha ao navegar para vagas"}
                
            # Aqui continuaria com as próximas etapas (filtros, busca, aplicação)
            self.detailed_log("🎉 AUTOMAÇÃO DE LOGIN CONCLUÍDA COM SUCESSO! 🎉", "SUCCESS")
            self.detailed_log("Próximas etapas: aplicar filtros e buscar vagas", "INFO")
            
            return {
                "success": True,
                "message": "Login realizado com sucesso",
                "next_steps": ["apply_filters", "search_jobs", "apply_to_jobs"]
            }
            
        except Exception as e:
            self.detailed_log(f"❌ Erro na automação completa: {str(e)}", "ERROR")
            self.take_debug_screenshot("automation_error")
            return {"success": False, "error": str(e)}
            
    def close(self):
        """Fecha o navegador"""
        try:
            if self.driver:
                self.driver.quit()
                self.detailed_log("Navegador fechado")
        except Exception as e:
            self.detailed_log(f"Erro ao fechar navegador: {str(e)}", "WARNING")

