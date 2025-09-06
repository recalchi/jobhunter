import time
import random
import logging
import os
import json
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from src.models.application_history import ApplicationHistory, db

class LinkedInWithJobHistory:
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
        
        # ID da sessão de automação para rastreamento
        self.session_id = str(uuid.uuid4())
        
    def setup_logging(self):
        """Configura o logging detalhado"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def detailed_log(self, message, level="INFO"):
        """Log detalhado com timestamp e formatação clara"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] LinkedIn History: {message}"
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
            time.sleep(8)  # Aguarda mais tempo para carregamento completo
            
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
            
    def step_5_find_show_all_button(self):
        """ETAPA 5: Encontrar e clicar no botão 'Exibir todas' (APRIMORADO)"""
        try:
            self.detailed_log("=== ETAPA 6: PROCURANDO BOTÃO 'EXIBIR TODAS' ===", "SUCCESS")
            
            # Aguarda carregamento completo da página
            self.detailed_log("Aguardando carregamento completo da página...")
            time.sleep(5)
            
            # Rola a página para baixo para carregar conteúdo dinâmico
            self.detailed_log("Rolando página para carregar conteúdo dinâmico...")
            self.driver.execute_script("window.scrollTo(0, 500);")
            time.sleep(3)
            
            # Screenshot antes de procurar o botão
            self.take_debug_screenshot("before_show_all_search")
            
            # Lista expandida de seletores para "Exibir todas" ou similares
            show_all_selectors = [
                # Seletores específicos do LinkedIn
                "a[href*='collections/recommended']",
                "a[data-control-name='jobs_home_jymbii_see_all']",
                ".jobs-home-jymbii__see-all-link",
                "a[data-control-name*='see_all']",
                
                # Seletores por texto (português)
                "//a[contains(text(), 'Exibir todas')]",
                "//a[contains(text(), 'Ver todas')]",
                "//a[contains(text(), 'Mostrar todas')]",
                "//button[contains(text(), 'Exibir todas')]",
                "//button[contains(text(), 'Ver todas')]",
                
                # Seletores por texto (inglês)
                "//a[contains(text(), 'See all')]",
                "//a[contains(text(), 'Show all')]",
                "//a[contains(text(), 'View all')]",
                "//button[contains(text(), 'See all')]",
                "//button[contains(text(), 'Show all')]",
                
                # Seletores genéricos
                "a[class*='see-all']",
                "a[class*='show-all']",
                "button[class*='see-all']",
                "button[class*='show-all']",
                
                # Seletores por aria-label
                "a[aria-label*='See all']",
                "a[aria-label*='Exibir todas']",
                "button[aria-label*='See all']",
                "button[aria-label*='Exibir todas']"
            ]
            
            show_all_element = None
            found_selector = None
            
            for i, selector in enumerate(show_all_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}/{len(show_all_selectors)}: {selector}")
                    
                    if selector.startswith("//"):
                        # XPath selector
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS selector
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            show_all_element = element
                            found_selector = selector
                            self.detailed_log(f"✅ Elemento 'Exibir todas' encontrado!")
                            self.detailed_log(f"Seletor usado: {selector}")
                            self.detailed_log(f"Texto do elemento: '{element.text}'")
                            self.detailed_log(f"Tag: {element.tag_name}")
                            
                            # Verifica se tem href (para links)
                            href = element.get_attribute('href')
                            if href:
                                self.detailed_log(f"URL do link: {href}")
                            
                            break
                    
                    if show_all_element:
                        break
                        
                except Exception as e:
                    self.detailed_log(f"Erro com seletor {selector}: {str(e)}")
                    continue
            
            if not show_all_element:
                self.detailed_log("❌ Botão 'Exibir todas' não encontrado", "WARNING")
                self.detailed_log("Tentando navegar diretamente para vagas recomendadas...")
                
                # Screenshot do estado atual
                self.take_debug_screenshot("show_all_not_found")
                
                # Navega diretamente para URL de vagas recomendadas
                return self.navigate_directly_to_recommended()
            
            # Screenshot antes de clicar
            self.take_debug_screenshot("before_click_show_all")
            
            # Rola até o elemento para garantir que está visível
            self.detailed_log("Rolando até o elemento...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", show_all_element)
            time.sleep(2)
            
            # Tenta clicar no elemento
            self.detailed_log("Clicando no botão 'Exibir todas'...")
            
            try:
                # Tenta clique normal primeiro
                show_all_element.click()
                self.detailed_log("✅ Clique normal realizado")
            except ElementClickInterceptedException:
                self.detailed_log("Clique interceptado, tentando JavaScript...")
                # Se clique normal falhar, usa JavaScript
                self.driver.execute_script("arguments[0].click();", show_all_element)
                self.detailed_log("✅ Clique via JavaScript realizado")
            
            # Aguarda navegação
            self.detailed_log("Aguardando navegação...")
            time.sleep(8)
            
            current_url = self.driver.current_url
            self.detailed_log(f"URL após clicar: {current_url}")
            
            # Screenshot após clicar
            self.take_debug_screenshot("after_click_show_all")
            
            # Verifica se navegou para vagas recomendadas
            if "jobs" in current_url and ("recommended" in current_url or "collections" in current_url):
                self.detailed_log("✅ Navegou para vagas recomendadas com sucesso!", "SUCCESS")
                return True
            elif "jobs" in current_url:
                self.detailed_log("✅ Está na seção de vagas (pode não ser recomendadas)", "SUCCESS")
                return True
            else:
                self.detailed_log(f"⚠️ URL inesperada após clique: {current_url}", "WARNING")
                return False
                
        except Exception as e:
            self.detailed_log(f"❌ Erro ao procurar botão 'Exibir todas': {str(e)}", "ERROR")
            self.take_debug_screenshot("show_all_search_error")
            return False
            
    def navigate_directly_to_recommended(self):
        """Navega diretamente para vagas recomendadas se botão não for encontrado"""
        try:
            self.detailed_log("=== NAVEGAÇÃO DIRETA PARA VAGAS RECOMENDADAS ===", "INFO")
            
            self.detailed_log(f"Navegando diretamente para: {self.recommended_jobs_url}")
            self.driver.get(self.recommended_jobs_url)
            
            self.detailed_log("Aguardando carregamento...")
            time.sleep(8)
            
            current_url = self.driver.current_url
            self.detailed_log(f"URL após navegação direta: {current_url}")
            
            # Screenshot após navegação direta
            self.take_debug_screenshot("direct_navigation_to_recommended")
            
            if "jobs" in current_url:
                self.detailed_log("✅ Navegação direta bem-sucedida", "SUCCESS")
                return True
            else:
                self.detailed_log(f"❌ Falha na navegação direta: {current_url}", "ERROR")
                return False
                
        except Exception as e:
            self.detailed_log(f"❌ Erro na navegação direta: {str(e)}", "ERROR")
            return False
            
    def step_6_find_and_apply_jobs(self, job_types, max_applications=3):
        """ETAPA 6: Encontrar e aplicar para vagas com histórico no banco"""
        try:
            self.detailed_log("=== ETAPA 7: ENCONTRANDO E APLICANDO PARA VAGAS ===", "SUCCESS")
            self.detailed_log(f"Tipos de vaga procurados: {', '.join(job_types)}")
            self.detailed_log(f"Máximo de aplicações: {max_applications}")
            self.detailed_log(f"ID da sessão: {self.session_id}")
            
            applications_sent = 0
            jobs_found = []
            
            # Aguarda carregamento completo
            self.detailed_log("Aguardando carregamento completo da página de vagas...")
            time.sleep(5)
            
            # Rola a página para carregar vagas
            self.detailed_log("Rolando página para carregar vagas...")
            self.driver.execute_script("window.scrollTo(0, 800);")
            time.sleep(3)
            
            # Screenshot da página de vagas
            self.take_debug_screenshot("jobs_page_ready")
            
            # Procura cards de vagas
            self.detailed_log("Procurando cards de vagas na página...")
            
            job_card_selectors = [
                ".job-search-card",
                ".jobs-search-results__list-item",
                ".job-card-container",
                "[data-job-id]",
                ".jobs-search-results-list__item",
                ".job-card",
                ".jobs-search__results-list li",
                ".scaffold-layout__list-item"
            ]
            
            job_cards = []
            for i, selector in enumerate(job_card_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        # Filtra apenas cards visíveis
                        visible_cards = [card for card in cards if card.is_displayed()]
                        if visible_cards:
                            job_cards = visible_cards
                            self.detailed_log(f"✅ Encontrados {len(job_cards)} cards visíveis com seletor: {selector}")
                            break
                except Exception as e:
                    self.detailed_log(f"Erro com seletor {selector}: {str(e)}")
                    continue
                    
            if not job_cards:
                self.detailed_log("❌ Nenhum card de vaga encontrado", "ERROR")
                self.take_debug_screenshot("no_job_cards")
                return {
                    "success": False,
                    "error": "Nenhuma vaga encontrada",
                    "applications_sent": 0,
                    "jobs_found": [],
                    "session_id": self.session_id
                }
                
            # Screenshot dos cards encontrados
            self.take_debug_screenshot("job_cards_found")
            
            # Processa cada card
            for i, card in enumerate(job_cards):
                if applications_sent >= max_applications:
                    self.detailed_log(f"Limite de aplicações atingido: {applications_sent}/{max_applications}")
                    break
                    
                try:
                    self.detailed_log(f"--- Processando vaga {i+1}/{len(job_cards)} ---")
                    
                    # Extrai informações da vaga
                    job_info = self.extract_job_info(card)
                    
                    if not job_info:
                        self.detailed_log("Não foi possível extrair informações da vaga")
                        continue
                        
                    self.detailed_log(f"Vaga encontrada: {job_info['title']} - {job_info['company']}")
                    
                    # Verifica se já foi aplicada recentemente
                    duplicate = ApplicationHistory.check_duplicate_application(
                        job_info.get('job_id'), 
                        job_info.get('url'), 
                        days=30
                    )
                    
                    if duplicate:
                        self.detailed_log(f"⚠️ Vaga já aplicada em {duplicate.attempted_at.strftime('%d/%m/%Y')}", "WARNING")
                        continue
                    
                    # Verifica se é relevante
                    if self.is_relevant_job(job_info['title'], job_types):
                        self.detailed_log(f"✅ Vaga relevante para os tipos procurados", "SUCCESS")
                        
                        # Cria registro no banco de dados
                        job_info['job_type'] = self.determine_job_type(job_info['title'], job_types)
                        application_record = ApplicationHistory.create_application_record(
                            job_info, 
                            status='pending', 
                            session_id=self.session_id
                        )
                        
                        self.detailed_log(f"📝 Registro criado no banco: ID {application_record.id}")
                        
                        # Tenta aplicar
                        if self.apply_to_job(card, job_info, i+1, application_record):
                            applications_sent += 1
                            job_info['status'] = 'applied'
                            self.applied_jobs.append(job_info)
                            
                            # Atualiza registro no banco
                            application_record.update_status('success')
                            
                            self.detailed_log(f"🎉 APLICAÇÃO {applications_sent}/{max_applications} ENVIADA COM SUCESSO!", "SUCCESS")
                            
                            # Delay entre aplicações
                            if applications_sent < max_applications:
                                delay_time = random.uniform(15, 25)
                                self.detailed_log(f"Aguardando {delay_time:.1f}s antes da próxima aplicação...")
                                time.sleep(delay_time)
                        else:
                            job_info['status'] = 'failed'
                            self.failed_applications.append(job_info)
                            
                            # Atualiza registro no banco
                            application_record.update_status('failed', error_message="Falha na aplicação")
                            
                            self.detailed_log("❌ Falha ao aplicar para esta vaga")
                            
                        jobs_found.append(job_info)
                    else:
                        self.detailed_log(f"Vaga não relevante: {job_info['title']}")
                    
                    # Delay entre análises
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    self.detailed_log(f"Erro ao processar vaga {i+1}: {str(e)}", "WARNING")
                    continue
            
            # Relatório final
            self.detailed_log("=== RELATÓRIO FINAL DE APLICAÇÕES ===", "SUCCESS")
            self.detailed_log(f"📊 Vagas analisadas: {len(job_cards)}")
            self.detailed_log(f"🎯 Vagas relevantes encontradas: {len(jobs_found)}")
            self.detailed_log(f"✅ Aplicações enviadas com sucesso: {applications_sent}")
            self.detailed_log(f"❌ Aplicações que falharam: {len(self.failed_applications)}")
            self.detailed_log(f"🗄️ Registros salvos no banco de dados")
            
            # Screenshot final
            self.take_debug_screenshot("final_results")
            
            return {
                "success": True,
                "applications_sent": applications_sent,
                "applied_jobs": self.applied_jobs,
                "failed_applications": self.failed_applications,
                "jobs_found": jobs_found,
                "session_id": self.session_id
            }
            
        except Exception as e:
            self.detailed_log(f"❌ Erro na busca e aplicação: {str(e)}", "ERROR")
            self.take_debug_screenshot("job_search_error")
            return {"success": False, "error": str(e), "session_id": self.session_id}
            
    def extract_job_info(self, job_card):
        """Extrai informações de um card de vaga"""
        try:
            job_info = {}
            
            # Título da vaga
            title_selectors = [
                ".job-search-card__title a",
                ".job-card-list__title a",
                "h3 a",
                "[data-control-name='job_search_job_title']",
                ".jobs-search-results__list-item h3 a",
                ".job-card__title a",
                "a[data-control-name*='job_title']"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = job_card.find_element(By.CSS_SELECTOR, selector)
                    job_info['title'] = title_element.text.strip()
                    job_info['url'] = title_element.get_attribute('href')
                    break
                except NoSuchElementException:
                    continue
                    
            if not job_info.get('title'):
                return None
                
            # Empresa
            company_selectors = [
                ".job-search-card__subtitle a",
                ".job-card-container__company-name a",
                "h4 a",
                ".jobs-search-results__list-item h4 a",
                ".job-card__subtitle a"
            ]
            
            for selector in company_selectors:
                try:
                    company_element = job_card.find_element(By.CSS_SELECTOR, selector)
                    job_info['company'] = company_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
                    
            job_info['company'] = job_info.get('company', 'Empresa não identificada')
            
            # Localização
            location_selectors = [
                ".job-search-card__location",
                ".job-card-container__metadata-item",
                ".jobs-search-results__list-item .job-search-card__location",
                ".job-card__location"
            ]
            
            for selector in location_selectors:
                try:
                    location_element = job_card.find_element(By.CSS_SELECTOR, selector)
                    job_info['location'] = location_element.text.strip()
                    break
                except NoSuchElementException:
                    continue
                    
            job_info['location'] = job_info.get('location', 'São Paulo, SP')
            
            # ID da vaga
            job_id = job_card.get_attribute('data-job-id')
            if not job_id and job_info.get('url'):
                # Extrai ID da URL
                url_parts = job_info['url'].split('/')
                for part in url_parts:
                    if part.isdigit():
                        job_id = part
                        break
            job_info['job_id'] = job_id or f"job_{int(time.time())}"
            
            return job_info
            
        except Exception as e:
            self.detailed_log(f"Erro ao extrair informações da vaga: {str(e)}", "WARNING")
            return None
            
    def is_relevant_job(self, job_title, job_types):
        """Verifica se a vaga é relevante para os tipos especificados"""
        job_title_lower = job_title.lower()
        
        relevance_keywords = {
            "analista financeiro": ["analista financeiro", "financial analyst", "financeiro"],
            "contas a pagar": ["contas a pagar", "accounts payable", "pagar", "ap"],
            "contas a receber": ["contas a receber", "accounts receivable", "receber", "ar"],
            "analista de precificacao": ["precificação", "pricing", "preço"],
            "custos": ["custos", "cost", "custo"]
        }
        
        for job_type in job_types:
            job_type_lower = job_type.lower()
            if job_type_lower in relevance_keywords:
                keywords = relevance_keywords[job_type_lower]
                for keyword in keywords:
                    if keyword in job_title_lower:
                        return True
                        
        return False
        
    def determine_job_type(self, job_title, job_types):
        """Determina o tipo específico da vaga"""
        job_title_lower = job_title.lower()
        
        if "contas a pagar" in job_title_lower or "accounts payable" in job_title_lower:
            return "Contas a Pagar"
        elif "contas a receber" in job_title_lower or "accounts receivable" in job_title_lower:
            return "Contas a Receber"
        elif "precificação" in job_title_lower or "pricing" in job_title_lower:
            return "Analista de Precificação"
        elif "custos" in job_title_lower or "cost" in job_title_lower:
            return "Custos"
        else:
            return "Analista Financeiro"
            
    def apply_to_job(self, job_card, job_info, card_number, application_record):
        """Aplica para uma vaga específica com registro no banco"""
        try:
            self.detailed_log(f"Tentando aplicar para: {job_info['title']}")
            
            # Procura botão de candidatura simplificada
            easy_apply_selectors = [
                ".jobs-apply-button--top-card",
                ".job-search-card__easy-apply-button",
                "button[aria-label*='Candidatura simplificada']",
                ".jobs-search-results__list-item .jobs-apply-button",
                "button:contains('Candidatura simplificada')",
                "button[data-control-name*='easy_apply']",
                ".job-card__easy-apply-button"
            ]
            
            easy_apply_button = None
            for i, selector in enumerate(easy_apply_selectors):
                try:
                    self.detailed_log(f"Procurando botão Easy Apply - seletor {i+1}: {selector}")
                    if ":contains" in selector:
                        easy_apply_button = job_card.find_element(By.XPATH, ".//button[contains(text(), 'Candidatura simplificada') or contains(text(), 'Easy Apply')]")
                    else:
                        easy_apply_button = job_card.find_element(By.CSS_SELECTOR, selector)
                        
                    if easy_apply_button.is_displayed() and easy_apply_button.is_enabled():
                        self.detailed_log(f"✅ Botão Easy Apply encontrado: {selector}")
                        self.detailed_log(f"Texto do botão: {easy_apply_button.text}")
                        break
                    else:
                        easy_apply_button = None
                except Exception:
                    continue
                    
            if not easy_apply_button:
                self.detailed_log("❌ Botão de candidatura simplificada não encontrado", "WARNING")
                application_record.update_status('failed', error_message="Botão Easy Apply não encontrado")
                return False
                
            # Screenshot antes de clicar
            screenshot_path = self.take_debug_screenshot(f"before_apply_job_{card_number}")
            
            # Clica no botão de candidatura
            self.detailed_log("Clicando em candidatura simplificada...")
            easy_apply_button.click()
            
            self.detailed_log("Aguardando abertura do modal de candidatura...")
            time.sleep(5)
            
            # Screenshot do modal
            modal_screenshot = self.take_debug_screenshot(f"application_modal_job_{card_number}")
            application_record.update_status('pending', screenshot_path=modal_screenshot)
            
            # Processa modal de candidatura
            result = self.process_application_modal(job_info, card_number, application_record)
            
            return result
            
        except Exception as e:
            self.detailed_log(f"❌ Erro ao aplicar para vaga: {str(e)}", "ERROR")
            error_screenshot = self.take_debug_screenshot(f"apply_error_job_{card_number}")
            application_record.update_status('failed', error_message=str(e), screenshot_path=error_screenshot)
            return False
            
    def process_application_modal(self, job_info, card_number, application_record):
        """Processa o modal de candidatura com perguntas e registro no banco"""
        try:
            self.detailed_log("Processando modal de candidatura...")
            
            max_steps = 5
            current_step = 0
            questions_answered = []
            
            while current_step < max_steps:
                current_step += 1
                self.detailed_log(f"--- Etapa do modal {current_step}/{max_steps} ---")
                
                # Screenshot da etapa atual
                self.take_debug_screenshot(f"modal_step_{current_step}_job_{card_number}")
                
                # Responde perguntas se houver
                step_questions = self.answer_application_questions()
                if step_questions:
                    questions_answered.extend(step_questions)
                    self.detailed_log("Perguntas respondidas, aguardando...")
                    time.sleep(3)
                
                # Procura botão "Avançar" ou "Revisar"
                next_button_selectors = [
                    "button[aria-label*='Avançar']",
                    "button[aria-label*='Revisar']",
                    "button:contains('Avançar')",
                    "button:contains('Revisar')",
                    "button:contains('Next')",
                    "button:contains('Review')"
                ]
                
                next_button = None
                for selector in next_button_selectors:
                    try:
                        if ":contains" in selector:
                            text = selector.split(":contains('")[1].rstrip("')")
                            next_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                        else:
                            next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                        if next_button.is_displayed() and next_button.is_enabled():
                            self.detailed_log(f"Botão 'Avançar' encontrado: {next_button.text}")
                            break
                        else:
                            next_button = None
                    except Exception:
                        continue
                        
                if next_button:
                    self.detailed_log("Clicando em 'Avançar'...")
                    next_button.click()
                    time.sleep(4)
                else:
                    # Procura botão "Enviar candidatura"
                    submit_button_selectors = [
                        "button[aria-label*='Enviar candidatura']",
                        "button:contains('Enviar candidatura')",
                        "button:contains('Enviar')",
                        "button:contains('Submit application')",
                        "button:contains('Submit')"
                    ]
                    
                    submit_button = None
                    for selector in submit_button_selectors:
                        try:
                            if ":contains" in selector:
                                text = selector.split(":contains('")[1].rstrip("')")
                                submit_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                            else:
                                submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                
                            if submit_button.is_displayed() and submit_button.is_enabled():
                                self.detailed_log(f"Botão 'Enviar' encontrado: {submit_button.text}")
                                break
                            else:
                                submit_button = None
                        except Exception:
                            continue
                            
                    if submit_button:
                        self.detailed_log("Enviando candidatura...")
                        submit_button.click()
                        time.sleep(5)
                        
                        # Screenshot após enviar
                        final_screenshot = self.take_debug_screenshot(f"after_submit_job_{card_number}")
                        
                        # Verifica se candidatura foi enviada
                        if self.verify_application_sent():
                            self.detailed_log("✅ Candidatura enviada com sucesso!", "SUCCESS")
                            
                            # Atualiza registro no banco com sucesso
                            application_record.update_status(
                                'success', 
                                questions=json.dumps(questions_answered) if questions_answered else None,
                                screenshot_path=final_screenshot
                            )
                            
                            return True
                        else:
                            self.detailed_log("❌ Falha ao verificar envio da candidatura")
                            application_record.update_status(
                                'failed', 
                                error_message="Falha na verificação de envio",
                                screenshot_path=final_screenshot
                            )
                            return False
                    else:
                        self.detailed_log("❌ Botão de envio não encontrado", "WARNING")
                        # Screenshot do estado atual
                        error_screenshot = self.take_debug_screenshot(f"no_submit_button_job_{card_number}")
                        application_record.update_status(
                            'failed', 
                            error_message="Botão de envio não encontrado",
                            screenshot_path=error_screenshot
                        )
                        return False
                        
            self.detailed_log("❌ Máximo de etapas atingido sem sucesso", "WARNING")
            application_record.update_status('failed', error_message="Máximo de etapas atingido")
            return False
            
        except Exception as e:
            self.detailed_log(f"❌ Erro ao processar modal: {str(e)}", "ERROR")
            error_screenshot = self.take_debug_screenshot(f"modal_error_job_{card_number}")
            application_record.update_status('failed', error_message=str(e), screenshot_path=error_screenshot)
            return False
            
    def answer_application_questions(self):
        """Responde perguntas do formulário de candidatura e retorna lista de perguntas respondidas"""
        try:
            questions_answered = []
            
            # Procura por perguntas comuns
            questions = self.driver.find_elements(By.CSS_SELECTOR, "label, .jobs-easy-apply-form-section__grouping")
            
            self.detailed_log(f"Encontradas {len(questions)} possíveis perguntas")
            
            for i, question in enumerate(questions):
                try:
                    question_text = question.text.lower()
                    self.detailed_log(f"Pergunta {i+1}: {question_text[:100]}...")
                    
                    # Pergunta sobre PJ
                    if "pj" in question_text or "pessoa jurídica" in question_text:
                        self.detailed_log("Respondendo pergunta sobre PJ...")
                        if self.answer_yes_no_question(question, True):
                            questions_answered.append({"question": question_text[:100], "answer": "Sim"})
                        
                    # Pergunta sobre remuneração
                    elif "remuneração" in question_text or "salário" in question_text:
                        self.detailed_log("Respondendo pergunta sobre remuneração...")
                        if self.answer_salary_question(question, "1900"):
                            questions_answered.append({"question": question_text[:100], "answer": "R$ 1900"})
                        
                    # Pergunta sobre Excel
                    elif "excel" in question_text:
                        self.detailed_log("Respondendo pergunta sobre Excel...")
                        if self.answer_skill_question(question, "8"):
                            questions_answered.append({"question": question_text[:100], "answer": "8"})
                        
                    # Pergunta sobre ERP
                    elif "erp" in question_text:
                        self.detailed_log("Respondendo pergunta sobre ERP...")
                        if self.answer_skill_question(question, "9"):
                            questions_answered.append({"question": question_text[:100], "answer": "9"})
                        
                except Exception as e:
                    self.detailed_log(f"Erro ao processar pergunta {i+1}: {str(e)}", "WARNING")
                    continue
                    
            if questions_answered:
                self.detailed_log(f"✅ {len(questions_answered)} perguntas respondidas")
            else:
                self.detailed_log("Nenhuma pergunta reconhecida encontrada")
                
            return questions_answered
            
        except Exception as e:
            self.detailed_log(f"Erro ao responder perguntas: {str(e)}", "WARNING")
            return []
            
    def answer_yes_no_question(self, question_element, answer_yes=True):
        """Responde pergunta sim/não"""
        try:
            parent = question_element.find_element(By.XPATH, "..")
            
            if answer_yes:
                options = parent.find_elements(By.XPATH, ".//input[@value='sim' or @value='yes' or @value='true'] | .//button[contains(text(), 'Sim') or contains(text(), 'Yes')]")
            else:
                options = parent.find_elements(By.XPATH, ".//input[@value='não' or @value='no' or @value='false'] | .//button[contains(text(), 'Não') or contains(text(), 'No')]")
                
            if options:
                options[0].click()
                self.detailed_log("✅ Pergunta sim/não respondida")
                time.sleep(2)
                return True
                
        except Exception as e:
            self.detailed_log(f"Erro ao responder sim/não: {str(e)}", "WARNING")
        return False
            
    def answer_salary_question(self, question_element, salary):
        """Responde pergunta sobre salário"""
        try:
            parent = question_element.find_element(By.XPATH, "..")
            input_field = parent.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='number']")
            
            input_field.clear()
            time.sleep(1)
            
            # Digita salário
            for char in salary:
                input_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.1))
                
            self.detailed_log("✅ Pergunta sobre salário respondida")
            time.sleep(2)
            return True
            
        except Exception as e:
            self.detailed_log(f"Erro ao responder salário: {str(e)}", "WARNING")
        return False
            
    def answer_skill_question(self, question_element, score):
        """Responde pergunta sobre habilidade (nota 0-10)"""
        try:
            parent = question_element.find_element(By.XPATH, "..")
            
            # Procura por input de número ou select
            input_field = parent.find_element(By.CSS_SELECTOR, "input[type='number'], input[type='text'], select")
            
            if input_field.tag_name == "select":
                # Se for select, procura pela opção
                options = input_field.find_elements(By.CSS_SELECTOR, f"option[value='{score}']")
                if options:
                    options[0].click()
                    self.detailed_log("✅ Pergunta sobre habilidade respondida (select)")
                    time.sleep(2)
                    return True
            else:
                # Se for input, digita o valor
                input_field.clear()
                time.sleep(1)
                
                for char in score:
                    input_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.1))
                    
                self.detailed_log("✅ Pergunta sobre habilidade respondida (input)")
                time.sleep(2)
                return True
                
        except Exception as e:
            self.detailed_log(f"Erro ao responder habilidade: {str(e)}", "WARNING")
        return False
            
    def verify_application_sent(self):
        """Verifica se a candidatura foi enviada com sucesso"""
        try:
            # Procura por mensagem de confirmação
            success_indicators = [
                "candidatou-se",
                "application sent",
                "candidatura enviada",
                "applied",
                "sua candidatura foi enviada"
            ]
            
            page_source = self.driver.page_source.lower()
            
            for indicator in success_indicators:
                if indicator in page_source:
                    self.detailed_log(f"Confirmação encontrada: {indicator}")
                    return True
                    
            # Aguarda um pouco e verifica novamente
            time.sleep(3)
            page_source = self.driver.page_source.lower()
            
            for indicator in success_indicators:
                if indicator in page_source:
                    self.detailed_log(f"Confirmação encontrada após aguardar: {indicator}")
                    return True
                    
            self.detailed_log("Nenhuma confirmação de envio encontrada")
            return False
            
        except Exception as e:
            self.detailed_log(f"Erro ao verificar candidatura: {str(e)}", "WARNING")
            return False
            
    def run_full_automation(self, username, password, job_types=None, max_applications=3):
        """Executa automação completa com histórico no banco de dados"""
        try:
            self.detailed_log("🚀 INICIANDO AUTOMAÇÃO LINKEDIN COM HISTÓRICO NO BANCO 🚀", "SUCCESS")
            self.detailed_log(f"ID da sessão: {self.session_id}")
            
            # Etapa 1: Configurar driver
            if not self.setup_driver():
                return {"success": False, "error": "Falha ao configurar driver", "session_id": self.session_id}
                
            # Etapa 2: Navegar para login
            if not self.step_1_navigate_to_login():
                return {"success": False, "error": "Falha ao navegar para página de login", "session_id": self.session_id}
                
            # Etapa 3: Preencher formulário
            if not self.step_2_fill_login_form(username, password):
                return {"success": False, "error": "Falha ao preencher formulário de login", "session_id": self.session_id}
                
            # Etapa 4: Submeter login
            login_result = self.step_3_submit_login()
            
            if login_result == "security_verification":
                # Pausa para verificação manual
                if not self.handle_security_verification():
                    return {"success": False, "error": "Verificação de segurança não concluída", "session_id": self.session_id}
            elif login_result == "login_error":
                return {"success": False, "error": "Erro nas credenciais de login", "session_id": self.session_id}
            elif login_result != "login_success" and login_result != "security_verification":
                return {"success": False, "error": f"Resultado de login inesperado: {login_result}", "session_id": self.session_id}
                
            # Etapa 5: Navegar para vagas
            if not self.step_4_navigate_to_jobs():
                return {"success": False, "error": "Falha ao navegar para vagas", "session_id": self.session_id}
                
            # Etapa 6: Encontrar botão "Exibir todas"
            if not self.step_5_find_show_all_button():
                return {"success": False, "error": "Falha ao encontrar botão 'Exibir todas'", "session_id": self.session_id}
                
            # Etapa 7: Buscar e aplicar para vagas
            if not job_types:
                job_types = ["analista financeiro"]
                
            results = self.step_6_find_and_apply_jobs(job_types, max_applications)
            
            self.detailed_log("🎉 AUTOMAÇÃO CONCLUÍDA COM SUCESSO! 🎉", "SUCCESS")
            self.detailed_log(f"📊 Consulte o histórico completo usando session_id: {self.session_id}")
            
            return results
            
        except Exception as e:
            self.detailed_log(f"❌ Erro na automação completa: {str(e)}", "ERROR")
            self.take_debug_screenshot("automation_error")
            return {"success": False, "error": str(e), "session_id": self.session_id}
            
    def close(self):
        """Fecha o navegador"""
        try:
            if self.driver:
                self.driver.quit()
                self.detailed_log("Navegador fechado")
        except Exception as e:
            self.detailed_log(f"Erro ao fechar navegador: {str(e)}", "WARNING")

