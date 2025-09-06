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

class LinkedInSuperRobustDriver:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.applied_jobs = []
        self.failed_applications = []
        self.setup_logging()
        
        # URLs específicas conforme instruções do usuário
        self.login_urls = [
            "https://www.linkedin.com/uas/login?session_redirect=%2Fm%2Flogout%2F",
            "https://www.linkedin.com/checkpoint/lg/sign-in-another-account"
        ]
        self.jobs_home_url = "https://www.linkedin.com/jobs"
        self.recommended_jobs_url = "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4278856149&discover=recommended&discoveryOrigin=JOBS_HOME_JYMBII"
        
        # Contador de screenshots para debug
        self.screenshot_counter = 0
        
    def setup_logging(self):
        """Configura o logging detalhado"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def detailed_log(self, message, level="INFO"):
        """Log detalhado com timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] LinkedIn Debug: {message}"
        self.logger.info(formatted_message)
        print(formatted_message)
        
    def take_debug_screenshot(self, step_name):
        """Tira screenshot para debug"""
        try:
            if self.driver:
                self.screenshot_counter += 1
                filename = f"debug_step_{self.screenshot_counter:02d}_{step_name}.png"
                filepath = os.path.join("/tmp", filename)
                self.driver.save_screenshot(filepath)
                self.detailed_log(f"Screenshot salvo: {filename}")
                return filepath
        except Exception as e:
            self.detailed_log(f"Erro ao salvar screenshot: {str(e)}", "WARNING")
        return None
        
    def setup_driver(self):
        """Configura o driver do Chrome com opções robustas"""
        try:
            self.detailed_log("=== ETAPA 1: CONFIGURANDO DRIVER DO CHROME (ROBUSTO) ===", "SUCCESS")
            
            chrome_options = Options()
            
            # Configurações básicas
            if self.headless:
                chrome_options.add_argument("--headless")
                self.detailed_log("Modo headless ativado")
            else:
                self.detailed_log("Modo visual ativado (não headless)")
            
            # Argumentos para iniciar o Chrome de forma limpa e robusta
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-session-crashed-bubble")
            chrome_options.add_argument("--incognito") # Ajuda a garantir uma sessão limpa
            chrome_options.add_argument("--disable-infobars") # Desabilita a barra de informações 'Chrome está sendo controlado por software de teste automatizado'
            chrome_options.add_argument("--disable-notifications") # Desabilita notificações do navegador
            chrome_options.add_argument("--disable-logging") # Desabilita logs do navegador
            chrome_options.add_argument("--log-level=3") # Apenas erros fatais
            chrome_options.add_argument("--silent") # Não mostra mensagens de erro no console
            chrome_options.add_argument("--disable-gpu") # Desabilita aceleração de hardware da GPU
            chrome_options.add_argument("--window-size=1920,1080") # Define um tamanho de janela padrão
            
            # User agent realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            self.detailed_log("Iniciando Chrome WebDriver...")
            
            # Tenta instalar e iniciar o driver
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            except WebDriverException as e:
                self.detailed_log(f"❌ Erro inicial ao iniciar Chrome: {str(e)}", "ERROR")
                self.detailed_log("Tentando iniciar Chrome com opções de fallback...")
                
                # Tenta com opções mais básicas
                chrome_options = Options()
                if self.headless:
                    chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--window-size=1920,1080")
                
                try:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                except WebDriverException as e_fallback:
                    self.detailed_log(f"❌ Erro ao iniciar Chrome mesmo com fallback: {str(e_fallback)}", "ERROR")
                    self.detailed_log("Verifique se o Chrome está instalado e se não há processos residuais.", "ERROR")
                    return False
            
            # Remove propriedades de automação
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 15)
            self.detailed_log("✅ Driver configurado com sucesso!")
            
            # Screenshot inicial
            self.take_debug_screenshot("driver_setup")
            
            return True
            
        except Exception as e:
            self.detailed_log(f"❌ Erro geral ao configurar driver: {str(e)}", "ERROR")
            return False
            
    def step_1_navigate_to_login(self):
        """ETAPA 1: Navegar para página de login"""
        try:
            self.detailed_log("=== ETAPA 2: NAVEGANDO PARA PÁGINA DE LOGIN ===", "SUCCESS")
            
            # Tenta primeira URL de login conforme instruções
            login_url = self.login_urls[0]
            self.detailed_log(f"Navegando para: {login_url}")
            
            self.driver.get(login_url)
            self.detailed_log("Aguardando carregamento da página...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.detailed_log(f"URL atual: {current_url}")
            self.detailed_log(f"Título da página: {page_title}")
            
            # Screenshot da página de login
            self.take_debug_screenshot("login_page")
            
            # Verifica se chegou na página de login ou se já está logado
            if "login" in current_url.lower() or "uas/login" in current_url.lower():
                self.detailed_log("✅ Chegou na página de login")
                return "login_page"
            elif "feed" in current_url or "jobs" in current_url:
                self.detailed_log("✅ Usuário já está logado - redirecionado automaticamente")
                return "already_logged_in"
            else:
                self.detailed_log(f"⚠️ URL inesperada: {current_url}")
                # Tenta segunda URL
                self.detailed_log("Tentando segunda URL de login...")
                self.driver.get(self.login_urls[1])
                time.sleep(5)
                
                current_url = self.driver.current_url
                self.detailed_log(f"Nova URL: {current_url}")
                self.take_debug_screenshot("second_login_attempt")
                
                if "login" in current_url.lower():
                    return "login_page"
                else:
                    return "unknown_state"
                    
        except Exception as e:
            self.detailed_log(f"❌ Erro na navegação para login: {str(e)}", "ERROR")
            self.take_debug_screenshot("login_navigation_error")
            return "error"
            
    def step_2_fill_login_form(self, username, password):
        """ETAPA 2: Preencher formulário de login"""
        try:
            self.detailed_log("=== ETAPA 3: PREENCHENDO FORMULÁRIO DE LOGIN ===", "SUCCESS")
            
            # Procura campo de email/username
            self.detailed_log("Procurando campo de email...")
            email_selectors = [
                "#username",
                "input[name='session_key']",
                "input[type='email']",
                "input[autocomplete='username']",
                "input[id*='username']"
            ]
            
            email_field = None
            for i, selector in enumerate(email_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    email_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if email_field.is_displayed():
                        self.detailed_log(f"✅ Campo de email encontrado com seletor: {selector}")
                        break
                    else:
                        self.detailed_log(f"Campo encontrado mas não visível: {selector}")
                        email_field = None
                except TimeoutException:
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
            
            # Digita de forma humana
            for char in username:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
            self.detailed_log("✅ Email preenchido")
            time.sleep(2)
            
            # Procura campo de senha
            self.detailed_log("Procurando campo de senha...")
            password_selectors = [
                "#password",
                "input[name='session_password']",
                "input[type='password']",
                "input[autocomplete='current-password']"
            ]
            
            password_field = None
            for i, selector in enumerate(password_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field.is_displayed():
                        self.detailed_log(f"✅ Campo de senha encontrado com seletor: {selector}")
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
            
            # Digita de forma humana
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
                
            self.detailed_log("✅ Senha preenchida")
            time.sleep(2)
            
            # Screenshot após preencher formulário
            self.take_debug_screenshot("form_filled")
            
            return True
            
        except Exception as e:
            self.detailed_log(f"❌ Erro ao preencher formulário: {str(e)}", "ERROR")
            self.take_debug_screenshot("form_fill_error")
            return False
            
    def step_3_submit_login(self):
        """ETAPA 3: Submeter formulário de login"""
        try:
            self.detailed_log("=== ETAPA 4: SUBMETENDO FORMULÁRIO DE LOGIN ===", "SUCCESS")
            
            # Procura botão de login
            self.detailed_log("Procurando botão de login...")
            login_selectors = [
                "button[type='submit']",
                "button[data-id='sign-in-form__submit-btn']",
                ".btn__primary--large",
                "input[type='submit']",
                "button[aria-label*='Sign in']",
                ".sign-in-form__submit-button"
            ]
            
            login_button = None
            for i, selector in enumerate(login_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_button.is_displayed() and login_button.is_enabled():
                        self.detailed_log(f"✅ Botão de login encontrado com seletor: {selector}")
                        break
                    else:
                        self.detailed_log(f"Botão encontrado mas não clicável: {selector}")
                        login_button = None
                except NoSuchElementException:
                    self.detailed_log(f"Seletor não encontrado: {selector}")
                    continue
                    
            if not login_button:
                self.detailed_log("❌ Botão de login não encontrado", "ERROR")
                self.take_debug_screenshot("login_button_not_found")
                return False
                
            # Clica no botão de login
            self.detailed_log("Clicando no botão de login...")
            login_button.click()
            
            self.detailed_log("Aguardando processamento do login...")
            time.sleep(8)  # Aguarda mais tempo para processamento
            
            # Verifica resultado
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.detailed_log(f"URL após login: {current_url}")
            self.detailed_log(f"Título após login: {page_title}")
            
            # Screenshot após login
            self.take_debug_screenshot("after_login")
            
            # Analisa resultado
            if "feed" in current_url or "jobs" in current_url or "mynetwork" in current_url:
                self.detailed_log("✅ Login realizado com sucesso!")
                return "success"
            elif "challenge" in current_url or "checkpoint" in current_url:
                self.detailed_log("⚠️ Desafio de segurança detectado")
                return "challenge"
            elif "login" in current_url:
                self.detailed_log("❌ Login falhou - ainda na página de login")
                return "failed"
            else:
                self.detailed_log(f"⚠️ Estado desconhecido após login: {current_url}")
                return "unknown"
                
        except Exception as e:
            self.detailed_log(f"❌ Erro ao submeter login: {str(e)}", "ERROR")
            self.take_debug_screenshot("login_submit_error")
            return "error"
            
    def step_4_navigate_to_jobs(self):
        """ETAPA 4: Navegar para seção de vagas"""
        try:
            self.detailed_log("=== ETAPA 5: NAVEGANDO PARA SEÇÃO DE VAGAS ===", "SUCCESS")
            
            # Navega para página de vagas
            self.detailed_log(f"Navegando para: {self.jobs_home_url}")
            self.driver.get(self.jobs_home_url)
            
            self.detailed_log("Aguardando carregamento da página de vagas...")
            time.sleep(5)
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            self.detailed_log(f"URL atual: {current_url}")
            self.detailed_log(f"Título da página: {page_title}")
            
            # Screenshot da página de vagas
            self.take_debug_screenshot("jobs_page")
            
            # Verifica se chegou na página de vagas
            if "jobs" in current_url:
                self.detailed_log("✅ Chegou na página de vagas")
                return True
            elif "login" in current_url:
                self.detailed_log("❌ Redirecionado para login - usuário não está logado")
                return False
            else:
                self.detailed_log(f"⚠️ URL inesperada: {current_url}")
                return False
                
        except Exception as e:
            self.detailed_log(f"❌ Erro ao navegar para vagas: {str(e)}", "ERROR")
            self.take_debug_screenshot("jobs_navigation_error")
            return False
            
    def step_5_navigate_to_recommended_jobs(self):
        """ETAPA 5: Navegar para vagas recomendadas"""
        try:
            self.detailed_log("=== ETAPA 6: NAVEGANDO PARA VAGAS RECOMENDADAS ===", "SUCCESS")
            
            # Procura link "Exibir todas" ou similar
            self.detailed_log("Procurando link para vagas recomendadas...")
            
            show_all_selectors = [
                "a[href*='collections/recommended']",
                "a[data-control-name='jobs_home_jymbii_see_all']",
                ".jobs-home-jymbii__see-all-link"
            ]
            
            show_all_link = None
            for i, selector in enumerate(show_all_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            show_all_link = element
                            self.detailed_log(f"✅ Link encontrado com seletor: {selector}")
                            self.detailed_log(f"Texto do link: {element.text}")
                            break
                    if show_all_link:
                        break
                except Exception as e:
                    self.detailed_log(f"Erro com seletor {selector}: {str(e)}")
                    continue
                    
            if show_all_link:
                self.detailed_log("Clicando no link 'Exibir todas'...")
                show_all_link.click()
                
                self.detailed_log("Aguardando carregamento das vagas recomendadas...")
                time.sleep(5)
                
                current_url = self.driver.current_url
                self.detailed_log(f"URL após clicar: {current_url}")
                
                # Screenshot após clicar
                self.take_debug_screenshot("recommended_jobs")
                
            else:
                # Se não encontrar link, navega diretamente
                self.detailed_log("Link não encontrado - navegando diretamente para vagas recomendadas...")
                self.driver.get(self.recommended_jobs_url)
                time.sleep(5)
                
                current_url = self.driver.current_url
                self.detailed_log(f"URL após navegação direta: {current_url}")
                
                # Screenshot após navegação direta
                self.take_debug_screenshot("direct_recommended_jobs")
                
            # Verifica se chegou nas vagas recomendadas
            if "jobs" in current_url and ("recommended" in current_url or "collections" in current_url):
                self.detailed_log("✅ Chegou na seção de vagas recomendadas")
                return True
            elif "jobs" in current_url:
                self.detailed_log("✅ Está na seção de vagas (pode não ser recomendadas)")
                return True
            else:
                self.detailed_log(f"⚠️ URL inesperada: {current_url}")
                return False
                
        except Exception as e:
            self.detailed_log(f"❌ Erro ao navegar para vagas recomendadas: {str(e)}", "ERROR")
            self.take_debug_screenshot("recommended_jobs_error")
            return False
            
    def step_6_apply_filters(self, location="São Paulo, SP"):
        """ETAPA 6: Aplicar filtros de busca"""
        try:
            self.detailed_log("=== ETAPA 7: APLICANDO FILTROS DE BUSCA ===", "SUCCESS")
            
            # Procura botão de filtros
            self.detailed_log("Procurando botão de filtros...")
            
            filter_selectors = [
                "button[aria-label*='filtro']",
                "button[aria-label*='Filtro']",
                "button[data-control-name='filter_button']",
                ".jobs-search-box__filter-button",
                "button:contains('Filtros')"
            ]
            
            filter_button = None
            for i, selector in enumerate(filter_selectors):
                try:
                    self.detailed_log(f"Tentando seletor {i+1}: {selector}")
                    if ":contains" in selector:
                        # Para seletores com texto, usa XPath
                        filter_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Filtros') or contains(text(), 'filtros')]")
                    else:
                        filter_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                    if filter_button.is_displayed():
                        self.detailed_log(f"✅ Botão de filtros encontrado: {selector}")
                        self.detailed_log(f"Texto do botão: {filter_button.text}")
                        break
                    else:
                        filter_button = None
                except Exception as e:
                    self.detailed_log(f"Seletor não encontrado: {selector}")
                    continue
                    
            if filter_button:
                self.detailed_log("Clicando no botão de filtros...")
                filter_button.click()
                
                self.detailed_log("Aguardando abertura do painel de filtros...")
                time.sleep(3)
                
                # Screenshot do painel de filtros
                self.take_debug_screenshot("filters_panel")
                
                # Aplica filtro de localização
                self.apply_location_filter(location)
                
                # Aplica filtro de candidatura simplificada
                self.apply_easy_apply_filter()
                
                # Aplica os filtros
                self.detailed_log("Procurando botão para aplicar filtros...")
                apply_selectors = [
                    "button[data-control-name='filter_show_results']",
                    ".jobs-search-box__submit-button",
                    "button:contains('Mostrar resultados')",
                    "button:contains('Aplicar')"
                ]
                
                for selector in apply_selectors:
                    try:
                        if ":contains" in selector:
                            text = selector.split(":contains('")[1].rstrip("')")
                            apply_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                        else:
                            apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            
                        if apply_button.is_displayed():
                            self.detailed_log(f"Clicando em aplicar filtros: {selector}")
                            apply_button.click()
                            time.sleep(5)
                            break
                    except Exception:
                        continue
                        
                # Screenshot após aplicar filtros
                self.take_debug_screenshot("filters_applied")
                
            else:
                self.detailed_log("⚠️ Botão de filtros não encontrado - continuando sem filtros")
                
            self.detailed_log("✅ Etapa de filtros concluída")
            return True
            
        except Exception as e:
            self.detailed_log(f"❌ Erro ao aplicar filtros: {str(e)}", "ERROR")
            self.take_debug_screenshot("filters_error")
            return False
            
    def apply_location_filter(self, location):
        """Aplica filtro de localização"""
        try:
            self.detailed_log(f"Aplicando filtro de localização: {location}")
            
            location_selectors = [
                "input[placeholder*='localização']",
                "input[placeholder*='Localização']",
                "input[aria-label*='localização']",
                "input[id*='location']"
            ]
            
            for selector in location_selectors:
                try:
                    location_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if location_field.is_displayed():
                        self.detailed_log(f"Campo de localização encontrado: {selector}")
                        location_field.clear()
                        time.sleep(1)
                        
                        # Digita localização
                        for char in location:
                            location_field.send_keys(char)
                            time.sleep(random.uniform(0.05, 0.1))
                            
                        self.detailed_log("✅ Localização preenchida")
                        time.sleep(2)
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            self.detailed_log(f"Erro ao aplicar filtro de localização: {str(e)}", "WARNING")
            
    def apply_easy_apply_filter(self):
        """Aplica filtro de candidatura simplificada"""
        try:
            self.detailed_log("Aplicando filtro de candidatura simplificada...")
            
            easy_apply_selectors = [
                "input[value='easy-apply']",
                "label[for*='easy-apply']",
                "input[id*='easy-apply']"
            ]
            
            for selector in easy_apply_selectors:
                try:
                    easy_apply_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if easy_apply_element.is_displayed():
                        self.detailed_log(f"Filtro Easy Apply encontrado: {selector}")
                        
                        # Se for input, verifica se já está marcado
                        if easy_apply_element.tag_name == "input":
                            if not easy_apply_element.is_selected():
                                easy_apply_element.click()
                                self.detailed_log("✅ Filtro Easy Apply ativado")
                            else:
                                self.detailed_log("Filtro Easy Apply já estava ativo")
                        else:
                            # Se for label, clica nele
                            easy_apply_element.click()
                            self.detailed_log("✅ Filtro Easy Apply ativado")
                            
                        time.sleep(2)
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            self.detailed_log(f"Erro ao aplicar filtro Easy Apply: {str(e)}", "WARNING")
            
    def step_7_find_and_apply_jobs(self, job_types, max_applications=3):
        """ETAPA 7: Encontrar e aplicar para vagas"""
        try:
            self.detailed_log("=== ETAPA 8: ENCONTRANDO E APLICANDO PARA VAGAS ===", "SUCCESS")
            self.detailed_log(f"Tipos de vaga procurados: {', '.join(job_types)}")
            self.detailed_log(f"Máximo de aplicações: {max_applications}")
            
            applications_sent = 0
            jobs_found = []
            
            # Procura cards de vagas
            self.detailed_log("Procurando cards de vagas na página...")
            
            job_card_selectors = [
                ".job-search-card",
                ".jobs-search-results__list-item",
                ".job-card-container",
                "[data-job-id]",
                ".jobs-search-results-list__item"
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
                    "jobs_found": []
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
                    
                    # Verifica se é relevante
                    if self.is_relevant_job(job_info['title'], job_types):
                        self.detailed_log(f"✅ Vaga relevante para os tipos procurados", "SUCCESS")
                        
                        # Tenta aplicar
                        if self.apply_to_job(card, job_info, i+1):
                            applications_sent += 1
                            job_info['status'] = 'applied'
                            self.applied_jobs.append(job_info)
                            self.detailed_log(f"🎉 APLICAÇÃO {applications_sent}/{max_applications} ENVIADA COM SUCESSO!", "SUCCESS")
                            
                            # Delay entre aplicações
                            if applications_sent < max_applications:
                                delay_time = random.uniform(15, 25)
                                self.detailed_log(f"Aguardando {delay_time:.1f}s antes da próxima aplicação...")
                                time.sleep(delay_time)
                        else:
                            job_info['status'] = 'failed'
                            self.failed_applications.append(job_info)
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
            
            # Screenshot final
            self.take_debug_screenshot("final_results")
            
            return {
                "success": True,
                "applications_sent": applications_sent,
                "applied_jobs": self.applied_jobs,
                "failed_applications": self.failed_applications,
                "jobs_found": jobs_found
            }
            
        except Exception as e:
            self.detailed_log(f"❌ Erro na busca e aplicação: {str(e)}", "ERROR")
            self.take_debug_screenshot("job_search_error")
            return {"success": False, "error": str(e)}
            
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
                ".jobs-search-results__list-item h3 a"
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
                ".jobs-search-results__list-item h4 a"
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
                ".jobs-search-results__list-item .job-search-card__location"
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
        
    def apply_to_job(self, job_card, job_info, card_number):
        """Aplica para uma vaga específica"""
        try:
            self.detailed_log(f"Tentando aplicar para: {job_info['title']}")
            
            # Procura botão de candidatura simplificada
            easy_apply_selectors = [
                ".jobs-apply-button--top-card",
                ".job-search-card__easy-apply-button",
                "button[aria-label*='Candidatura simplificada']",
                ".jobs-search-results__list-item .jobs-apply-button",
                "button:contains('Candidatura simplificada')"
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
                return False
                
            # Screenshot antes de clicar
            self.take_debug_screenshot(f"before_apply_job_{card_number}")
            
            # Clica no botão de candidatura
            self.detailed_log("Clicando em candidatura simplificada...")
            easy_apply_button.click()
            
            self.detailed_log("Aguardando abertura do modal de candidatura...")
            time.sleep(5)
            
            # Screenshot do modal
            self.take_debug_screenshot(f"application_modal_job_{card_number}")
            
            # Processa modal de candidatura
            result = self.process_application_modal(job_info, card_number)
            
            return result
            
        except Exception as e:
            self.detailed_log(f"❌ Erro ao aplicar para vaga: {str(e)}", "ERROR")
            self.take_debug_screenshot(f"apply_error_job_{card_number}")
            return False
            
    def process_application_modal(self, job_info, card_number):
        """Processa o modal de candidatura com perguntas"""
        try:
            self.detailed_log("Processando modal de candidatura...")
            
            max_steps = 5
            current_step = 0
            
            while current_step < max_steps:
                current_step += 1
                self.detailed_log(f"--- Etapa do modal {current_step}/{max_steps} ---")
                
                # Screenshot da etapa atual
                self.take_debug_screenshot(f"modal_step_{current_step}_job_{card_number}")
                
                # Responde perguntas se houver
                questions_answered = self.answer_application_questions()
                if questions_answered:
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
                        self.take_debug_screenshot(f"after_submit_job_{card_number}")
                        
                        # Verifica se candidatura foi enviada
                        if self.verify_application_sent():
                            self.detailed_log("✅ Candidatura enviada com sucesso!", "SUCCESS")
                            return True
                        else:
                            self.detailed_log("❌ Falha ao verificar envio da candidatura")
                            return False
                    else:
                        self.detailed_log("❌ Botão de envio não encontrado", "WARNING")
                        # Screenshot do estado atual
                        self.take_debug_screenshot(f"no_submit_button_job_{card_number}")
                        return False
                        
            self.detailed_log("❌ Máximo de etapas atingido sem sucesso", "WARNING")
            return False
            
        except Exception as e:
            self.detailed_log(f"❌ Erro ao processar modal: {str(e)}", "ERROR")
            self.take_debug_screenshot(f"modal_error_job_{card_number}")
            return False
            
    def answer_application_questions(self):
        """Responde perguntas do formulário de candidatura"""
        try:
            questions_answered = False
            
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
                        self.answer_yes_no_question(question, True)
                        questions_answered = True
                        
                    # Pergunta sobre remuneração
                    elif "remuneração" in question_text or "salário" in question_text:
                        self.detailed_log("Respondendo pergunta sobre remuneração...")
                        self.answer_salary_question(question, "1900")
                        questions_answered = True
                        
                    # Pergunta sobre Excel
                    elif "excel" in question_text:
                        self.detailed_log("Respondendo pergunta sobre Excel...")
                        self.answer_skill_question(question, "8")
                        questions_answered = True
                        
                    # Pergunta sobre ERP
                    elif "erp" in question_text:
                        self.detailed_log("Respondendo pergunta sobre ERP...")
                        self.answer_skill_question(question, "9")
                        questions_answered = True
                        
                except Exception as e:
                    self.detailed_log(f"Erro ao processar pergunta {i+1}: {str(e)}", "WARNING")
                    continue
                    
            if questions_answered:
                self.detailed_log("✅ Perguntas respondidas")
            else:
                self.detailed_log("Nenhuma pergunta reconhecida encontrada")
                
            return questions_answered
            
        except Exception as e:
            self.detailed_log(f"Erro ao responder perguntas: {str(e)}", "WARNING")
            return False
            
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
                
        except Exception as e:
            self.detailed_log(f"Erro ao responder sim/não: {str(e)}", "WARNING")
            
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
            
        except Exception as e:
            self.detailed_log(f"Erro ao responder salário: {str(e)}", "WARNING")
            
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
            else:
                # Se for input, digita o valor
                input_field.clear()
                time.sleep(1)
                
                for char in score:
                    input_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.1))
                    
                self.detailed_log("✅ Pergunta sobre habilidade respondida (input)")
                
            time.sleep(2)
            
        except Exception as e:
            self.detailed_log(f"Erro ao responder habilidade: {str(e)}", "WARNING")
            
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
            
    def run_full_automation(self, username=None, password=None, job_types=None, max_applications=3):
        """Executa automação completa passo a passo com debug"""
        try:
            self.detailed_log("🚀 INICIANDO AUTOMAÇÃO LINKEDIN STEP-BY-STEP DEBUG 🚀", "SUCCESS")
            
            # Etapa 1: Configurar driver
            if not self.setup_driver():
                return {"success": False, "error": "Falha ao configurar driver"}
                
            # Etapa 2: Navegar para login
            login_status = self.step_1_navigate_to_login()
            
            if login_status == "error":
                return {"success": False, "error": "Falha ao navegar para login"}
            elif login_status == "already_logged_in":
                self.detailed_log("Usuário já logado - pulando etapas de login")
            elif login_status == "login_page":
                # Etapa 3: Preencher formulário
                if not username or not password:
                    return {"success": False, "error": "Credenciais necessárias para login"}
                    
                if not self.step_2_fill_login_form(username, password):
                    return {"success": False, "error": "Falha ao preencher formulário"}
                    
                # Etapa 4: Submeter login
                submit_result = self.step_3_submit_login()
                if submit_result not in ["success", "challenge"]:
                    return {"success": False, "error": f"Falha no login: {submit_result}"}
                    
                if submit_result == "challenge":
                    self.detailed_log("Aguarde resolver o desafio de segurança manualmente...")
                    time.sleep(60)  # Aguarda 1 minuto para resolução manual
            
            # Etapa 5: Navegar para vagas
            if not self.step_4_navigate_to_jobs():
                return {"success": False, "error": "Falha ao navegar para vagas"}
                
            # Etapa 6: Navegar para vagas recomendadas
            if not self.step_5_navigate_to_recommended_jobs():
                return {"success": False, "error": "Falha ao navegar para vagas recomendadas"}
                
            # Etapa 7: Aplicar filtros
            if not self.step_6_apply_filters():
                return {"success": False, "error": "Falha ao aplicar filtros"}
                
            # Etapa 8: Encontrar e aplicar para vagas
            if not job_types:
                job_types = ["analista financeiro"]
                
            results = self.step_7_find_and_apply_jobs(job_types, max_applications)
            
            self.detailed_log("🎉 AUTOMAÇÃO CONCLUÍDA COM SUCESSO! 🎉", "SUCCESS")
            
            return results
            
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

