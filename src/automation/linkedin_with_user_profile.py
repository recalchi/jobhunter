import time
import random
import logging
import os
import platform
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class LinkedInWithUserProfile:
    def __init__(self, headless=False, user_data_dir=None, profile_name="Default"):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.profile_name = profile_name
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
        
    def setup_logging(self):
        """Configura o logging detalhado"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def detailed_log(self, message, level="INFO"):
        """Log detalhado com timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] LinkedIn Profile: {message}"
        self.logger.info(formatted_message)
        print(formatted_message)
        
    def get_default_user_data_dir(self):
        """Detecta automaticamente o diretório padrão do perfil do Chrome"""
        system = platform.system()
        
        if system == "Windows":
            # Windows
            user_profile = os.environ.get('USERPROFILE', '')
            return os.path.join(user_profile, 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
        elif system == "Darwin":
            # macOS
            user_home = os.path.expanduser('~')
            return os.path.join(user_home, 'Library', 'Application Support', 'Google', 'Chrome')
        else:
            # Linux
            user_home = os.path.expanduser('~')
            return os.path.join(user_home, '.config', 'google-chrome')
            
    def setup_driver(self):
        """Configura o driver do Chrome com perfil de usuário"""
        try:
            self.detailed_log("Configurando driver do Chrome com perfil de usuário...")
            
            chrome_options = Options()
            
            # Configurações básicas
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Configurações de perfil de usuário
            if self.user_data_dir:
                if os.path.exists(self.user_data_dir):
                    chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
                    chrome_options.add_argument(f"--profile-directory={self.profile_name}")
                    self.detailed_log(f"Usando perfil personalizado: {self.user_data_dir}/{self.profile_name}")
                else:
                    self.detailed_log(f"Diretório de perfil não encontrado: {self.user_data_dir}", "WARNING")
                    self.detailed_log("Tentando detectar perfil padrão...")
                    default_dir = self.get_default_user_data_dir()
                    if os.path.exists(default_dir):
                        chrome_options.add_argument(f"--user-data-dir={default_dir}")
                        chrome_options.add_argument(f"--profile-directory={self.profile_name}")
                        self.detailed_log(f"Usando perfil padrão detectado: {default_dir}")
                    else:
                        self.detailed_log("Perfil padrão não encontrado, usando modo anônimo", "WARNING")
            else:
                # Tenta detectar automaticamente o perfil padrão
                default_dir = self.get_default_user_data_dir()
                if os.path.exists(default_dir):
                    chrome_options.add_argument(f"--user-data-dir={default_dir}")
                    chrome_options.add_argument(f"--profile-directory={self.profile_name}")
                    self.detailed_log(f"Usando perfil padrão detectado: {default_dir}")
                else:
                    self.detailed_log("Perfil padrão não encontrado, usando modo anônimo", "WARNING")
            
            # Configurações de segurança e performance
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Configurações adicionais para evitar detecção
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-extensions")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove propriedades de automação
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 15)
            self.detailed_log("Driver configurado com sucesso!")
            return True
            
        except Exception as e:
            self.detailed_log(f"Erro ao configurar driver: {str(e)}", "ERROR")
            return False
            
    def check_login_status(self):
        """Verifica se o usuário já está logado no LinkedIn"""
        try:
            self.detailed_log("Verificando status de login...")
            
            # Navega para página inicial do LinkedIn
            self.driver.get("https://www.linkedin.com/feed/")
            time.sleep(3)
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            # Verifica indicadores de login
            if "feed" in current_url or "mynetwork" in current_url:
                self.detailed_log("Usuário já está logado!", "SUCCESS")
                return True
            elif "login" in current_url or "uas/login" in current_url:
                self.detailed_log("Usuário não está logado", "INFO")
                return False
            else:
                # Verifica elementos da página
                try:
                    # Procura por elementos que indicam login
                    profile_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                        ".global-nav__me, .nav-item__profile-member-photo, [data-control-name='identity_profile_photo']")
                    
                    if profile_elements:
                        self.detailed_log("Login detectado através de elementos da página", "SUCCESS")
                        return True
                    else:
                        self.detailed_log("Login não detectado", "INFO")
                        return False
                        
                except Exception:
                    self.detailed_log("Não foi possível determinar status de login", "WARNING")
                    return False
                    
        except Exception as e:
            self.detailed_log(f"Erro ao verificar login: {str(e)}", "ERROR")
            return False
            
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Delay aleatório para parecer mais humano"""
        delay = random.uniform(min_seconds, max_seconds)
        self.detailed_log(f"Aguardando {delay:.1f} segundos...")
        time.sleep(delay)
        
    def human_type(self, element, text):
        """Digita texto de forma mais humana"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))
            
    def login_if_needed(self, username=None, password=None):
        """Faz login apenas se necessário"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
                    
            # Verifica se já está logado
            if self.check_login_status():
                self.detailed_log("Login não necessário - usuário já autenticado", "SUCCESS")
                return True
                
            # Se não está logado e não tem credenciais, falha
            if not username or not password:
                self.detailed_log("Login necessário mas credenciais não fornecidas", "ERROR")
                return False
                
            # Executa login
            self.detailed_log("Login necessário - iniciando processo...")
            return self.login_linkedin(username, password)
            
        except Exception as e:
            self.detailed_log(f"Erro no processo de login: {str(e)}", "ERROR")
            return False
            
    def login_linkedin(self, username, password):
        """Faz login no LinkedIn seguindo as URLs específicas"""
        try:
            # Tenta primeira URL de login
            self.detailed_log("Navegando para página de login...")
            self.driver.get(self.login_urls[0])
            self.random_delay(3, 5)
            
            # Verifica se já está logado após navegar
            current_url = self.driver.current_url
            if "feed" in current_url or "jobs" in current_url:
                self.detailed_log("Login automático detectado!", "SUCCESS")
                return True
            
            # Se não conseguir na primeira URL, tenta a segunda
            if "login" not in current_url.lower():
                self.detailed_log("Tentando segunda URL de login...")
                self.driver.get(self.login_urls[1])
                self.random_delay(3, 5)
            
            self.detailed_log("Preenchendo credenciais de login...")
            
            # Busca campo de email/username
            email_selectors = [
                "#username",
                "input[name='session_key']",
                "input[type='email']",
                "input[autocomplete='username']"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
                    
            if not email_field:
                self.detailed_log("Campo de email não encontrado", "ERROR")
                return False
                
            self.detailed_log("Preenchendo email...")
            self.human_type(email_field, username)
            self.random_delay(1, 2)
            
            # Busca campo de senha
            password_selectors = [
                "#password",
                "input[name='session_password']",
                "input[type='password']",
                "input[autocomplete='current-password']"
            ]
            
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if not password_field:
                self.detailed_log("Campo de senha não encontrado", "ERROR")
                return False
                
            self.detailed_log("Preenchendo senha...")
            self.human_type(password_field, password)
            self.random_delay(1, 2)
            
            # Busca botão de login
            login_selectors = [
                "button[type='submit']",
                "button[data-id='sign-in-form__submit-btn']",
                ".btn__primary--large",
                "input[type='submit']"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if not login_button:
                self.detailed_log("Botão de login não encontrado", "ERROR")
                return False
                
            self.detailed_log("Clicando no botão de login...")
            login_button.click()
            self.random_delay(5, 8)
            
            # Verifica resultado do login
            current_url = self.driver.current_url
            
            if "feed" in current_url or "jobs" in current_url or "mynetwork" in current_url:
                self.detailed_log("Login realizado com sucesso!", "SUCCESS")
                return True
            elif "challenge" in current_url or "checkpoint" in current_url:
                self.detailed_log("Desafio de segurança detectado", "WARNING")
                self.detailed_log(f"URL atual: {current_url}")
                self.detailed_log("ATENÇÃO: Resolva manualmente o desafio no navegador")
                
                # Aguarda resolução manual por até 2 minutos
                for i in range(24):  # 24 * 5 = 120 segundos
                    time.sleep(5)
                    current_url = self.driver.current_url
                    if "feed" in current_url or "jobs" in current_url:
                        self.detailed_log("Desafio resolvido - login completado!", "SUCCESS")
                        return True
                    self.detailed_log(f"Aguardando resolução... ({i*5}s)")
                
                self.detailed_log("Timeout na resolução do desafio", "ERROR")
                return False
            else:
                self.detailed_log(f"Login falhou - URL: {current_url}", "ERROR")
                return False
                
        except Exception as e:
            self.detailed_log(f"Erro durante o login: {str(e)}", "ERROR")
            return False
            
    def navigate_to_jobs_section(self):
        """Navega para a seção de vagas conforme instruções"""
        try:
            self.detailed_log("Navegando para seção de vagas...")
            
            # Vai para página inicial de vagas
            self.driver.get(self.jobs_home_url)
            self.random_delay(3, 5)
            
            # Procura por "Exibir todas" ou link para vagas recomendadas
            show_all_selectors = [
                "a[href*='collections/recommended']",
                "a[data-control-name='jobs_home_jymbii_see_all']",
                ".jobs-home-jymbii__see-all-link"
            ]
            
            show_all_link = None
            for selector in show_all_selectors:
                try:
                    show_all_link = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if show_all_link:
                self.detailed_log("Clicando em 'Exibir todas' as vagas...")
                show_all_link.click()
                self.random_delay(3, 5)
            else:
                # Se não encontrar, navega diretamente para URL de vagas recomendadas
                self.detailed_log("Navegando diretamente para vagas recomendadas...")
                self.driver.get(self.recommended_jobs_url)
                self.random_delay(3, 5)
                
            self.detailed_log("Navegação para seção de vagas concluída")
            return True
            
        except Exception as e:
            self.detailed_log(f"Erro ao navegar para seção de vagas: {str(e)}", "ERROR")
            return False
            
    def apply_filters(self, location="São Paulo, SP"):
        """Aplica filtros de localização e candidatura simplificada"""
        try:
            self.detailed_log("Aplicando filtros de busca...")
            
            # Procura por botão de filtros
            filter_selectors = [
                "button[aria-label*='filtro']",
                "button[data-control-name='filter_button']",
                ".jobs-search-box__filter-button"
            ]
            
            filter_button = None
            for selector in filter_selectors:
                try:
                    filter_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if filter_button:
                self.detailed_log("Abrindo painel de filtros...")
                filter_button.click()
                self.random_delay(2, 3)
                
                # Aplica filtro de localização
                self.apply_location_filter(location)
                
                # Aplica filtro de candidatura simplificada
                self.apply_easy_apply_filter()
                
                # Aplica filtros
                apply_button_selectors = [
                    "button[data-control-name='filter_show_results']",
                    ".jobs-search-box__submit-button"
                ]
                
                for selector in apply_button_selectors:
                    try:
                        apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        self.detailed_log("Aplicando filtros...")
                        apply_button.click()
                        self.random_delay(3, 5)
                        break
                    except NoSuchElementException:
                        continue
                        
            self.detailed_log("Filtros aplicados com sucesso")
            return True
            
        except Exception as e:
            self.detailed_log(f"Erro ao aplicar filtros: {str(e)}", "ERROR")
            return False
            
    def apply_location_filter(self, location):
        """Aplica filtro de localização"""
        try:
            location_selectors = [
                "input[placeholder*='localização']",
                "input[placeholder*='Localização']",
                "input[aria-label*='localização']"
            ]
            
            for selector in location_selectors:
                try:
                    location_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.detailed_log(f"Definindo localização: {location}")
                    self.human_type(location_field, location)
                    self.random_delay(1, 2)
                    break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.detailed_log(f"Erro ao aplicar filtro de localização: {str(e)}", "WARNING")
            
    def apply_easy_apply_filter(self):
        """Aplica filtro de candidatura simplificada"""
        try:
            easy_apply_selectors = [
                "input[value='easy-apply']",
                "label[for*='easy-apply']"
            ]
            
            for selector in easy_apply_selectors:
                try:
                    easy_apply_checkbox = self.driver.find_element(By.CSS_SELECTOR, selector)
                    self.detailed_log("Ativando filtro de candidatura simplificada...")
                    easy_apply_checkbox.click()
                    self.random_delay(1, 2)
                    break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.detailed_log(f"Erro ao aplicar filtro Easy Apply: {str(e)}", "WARNING")
            
    def search_and_apply_jobs(self, job_types, max_applications=3):
        """Busca e aplica para vagas dos tipos especificados"""
        try:
            self.detailed_log(f"Iniciando busca por vagas: {', '.join(job_types)}")
            
            applications_sent = 0
            jobs_found = []
            
            # Busca cards de vagas na página
            job_card_selectors = [
                ".job-search-card",
                ".jobs-search-results__list-item",
                ".job-card-container",
                "[data-job-id]"
            ]
            
            job_cards = []
            for selector in job_card_selectors:
                try:
                    job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_cards:
                        break
                except:
                    continue
                    
            self.detailed_log(f"Encontrados {len(job_cards)} cards de vagas")
            
            for i, card in enumerate(job_cards):
                if applications_sent >= max_applications:
                    break
                    
                try:
                    self.detailed_log(f"Analisando vaga {i+1}/{len(job_cards)}")
                    
                    # Extrai informações da vaga
                    job_info = self.extract_job_info(card)
                    
                    if not job_info:
                        continue
                        
                    # Verifica se a vaga é relevante para os tipos especificados
                    if self.is_relevant_job(job_info['title'], job_types):
                        self.detailed_log(f"Vaga relevante encontrada: {job_info['title']} - {job_info['company']}")
                        
                        # Tenta aplicar para a vaga
                        if self.apply_to_job(card, job_info):
                            applications_sent += 1
                            job_info['status'] = 'applied'
                            self.applied_jobs.append(job_info)
                            self.detailed_log(f"✅ Aplicação {applications_sent}/{max_applications} enviada!", "SUCCESS")
                            
                            # Delay entre aplicações
                            if applications_sent < max_applications:
                                delay_time = random.uniform(15, 25)
                                self.detailed_log(f"Aguardando {delay_time:.1f}s antes da próxima aplicação...")
                                time.sleep(delay_time)
                        else:
                            job_info['status'] = 'failed'
                            self.failed_applications.append(job_info)
                            
                        jobs_found.append(job_info)
                    
                    self.random_delay(2, 4)
                    
                except Exception as e:
                    self.detailed_log(f"Erro ao processar vaga {i+1}: {str(e)}", "WARNING")
                    continue
            
            # Relatório final
            self.detailed_log("=== RELATÓRIO FINAL ===", "SUCCESS")
            self.detailed_log(f"Vagas analisadas: {len(job_cards)}")
            self.detailed_log(f"Vagas relevantes: {len(jobs_found)}")
            self.detailed_log(f"Aplicações enviadas: {applications_sent}")
            self.detailed_log(f"Aplicações falharam: {len(self.failed_applications)}")
            
            return {
                "success": True,
                "applications_sent": applications_sent,
                "applied_jobs": self.applied_jobs,
                "failed_applications": self.failed_applications,
                "jobs_found": jobs_found
            }
            
        except Exception as e:
            self.detailed_log(f"Erro na busca e aplicação: {str(e)}", "ERROR")
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
                "[data-control-name='job_search_job_title']"
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
                "h4 a"
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
                ".job-card-container__metadata-item"
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
        
    def apply_to_job(self, job_card, job_info):
        """Aplica para uma vaga específica"""
        try:
            self.detailed_log(f"Tentando aplicar para: {job_info['title']}")
            
            # Procura botão de candidatura simplificada
            easy_apply_selectors = [
                ".jobs-apply-button--top-card",
                ".job-search-card__easy-apply-button",
                "button[aria-label*='Candidatura simplificada']"
            ]
            
            easy_apply_button = None
            for selector in easy_apply_selectors:
                try:
                    easy_apply_button = job_card.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
                    
            if not easy_apply_button:
                self.detailed_log("Botão de candidatura simplificada não encontrado", "WARNING")
                return False
                
            # Clica no botão de candidatura
            self.detailed_log("Clicando em candidatura simplificada...")
            easy_apply_button.click()
            self.random_delay(3, 5)
            
            # Processa modal de candidatura
            return self.process_application_modal(job_info)
            
        except Exception as e:
            self.detailed_log(f"Erro ao aplicar para vaga: {str(e)}", "ERROR")
            return False
            
    def process_application_modal(self, job_info):
        """Processa o modal de candidatura com perguntas"""
        try:
            self.detailed_log("Processando modal de candidatura...")
            
            max_steps = 5  # Máximo de etapas para evitar loop infinito
            current_step = 0
            
            while current_step < max_steps:
                current_step += 1
                self.detailed_log(f"Processando etapa {current_step}/{max_steps}")
                
                # Verifica se há perguntas para responder
                if self.answer_application_questions():
                    self.random_delay(2, 3)
                
                # Procura botão "Avançar" ou "Revisar"
                next_button_selectors = [
                    "button[aria-label*='Avançar']",
                    "button[aria-label*='Revisar']"
                ]
                
                next_button = None
                for selector in next_button_selectors:
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                        
                if next_button:
                    self.detailed_log("Clicando em 'Avançar'...")
                    next_button.click()
                    self.random_delay(2, 4)
                else:
                    # Se não há botão avançar, procura botão "Enviar candidatura"
                    submit_button_selectors = [
                        "button[aria-label*='Enviar candidatura']"
                    ]
                    
                    submit_button = None
                    for selector in submit_button_selectors:
                        try:
                            submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                            continue
                            
                    if submit_button:
                        self.detailed_log("Enviando candidatura...")
                        submit_button.click()
                        self.random_delay(3, 5)
                        
                        # Verifica se candidatura foi enviada
                        if self.verify_application_sent():
                            return True
                        else:
                            return False
                    else:
                        self.detailed_log("Botão de envio não encontrado", "WARNING")
                        return False
                        
            self.detailed_log("Máximo de etapas atingido", "WARNING")
            return False
            
        except Exception as e:
            self.detailed_log(f"Erro ao processar modal: {str(e)}", "ERROR")
            return False
            
    def answer_application_questions(self):
        """Responde perguntas do formulário de candidatura"""
        try:
            questions_answered = False
            
            # Procura por perguntas comuns
            questions = self.driver.find_elements(By.CSS_SELECTOR, "label, .jobs-easy-apply-form-section__grouping")
            
            for question in questions:
                question_text = question.text.lower()
                
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
                    
            return questions_answered
            
        except Exception as e:
            self.detailed_log(f"Erro ao responder perguntas: {str(e)}", "WARNING")
            return False
            
    def answer_yes_no_question(self, question_element, answer_yes=True):
        """Responde pergunta sim/não"""
        try:
            # Procura por radio buttons ou select
            parent = question_element.find_element(By.XPATH, "..")
            
            if answer_yes:
                options = parent.find_elements(By.XPATH, ".//input[@value='sim' or @value='yes' or @value='true']")
            else:
                options = parent.find_elements(By.XPATH, ".//input[@value='não' or @value='no' or @value='false']")
                
            if options:
                options[0].click()
                self.random_delay(1, 2)
                
        except Exception as e:
            self.detailed_log(f"Erro ao responder sim/não: {str(e)}", "WARNING")
            
    def answer_salary_question(self, question_element, salary):
        """Responde pergunta sobre salário"""
        try:
            parent = question_element.find_element(By.XPATH, "..")
            input_field = parent.find_element(By.CSS_SELECTOR, "input[type='text'], input[type='number']")
            
            self.human_type(input_field, salary)
            self.random_delay(1, 2)
            
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
            else:
                # Se for input, digita o valor
                self.human_type(input_field, score)
                
            self.random_delay(1, 2)
            
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
                "applied"
            ]
            
            page_source = self.driver.page_source.lower()
            
            for indicator in success_indicators:
                if indicator in page_source:
                    self.detailed_log("Candidatura confirmada!", "SUCCESS")
                    return True
                    
            # Aguarda um pouco e verifica novamente
            self.random_delay(2, 3)
            page_source = self.driver.page_source.lower()
            
            for indicator in success_indicators:
                if indicator in page_source:
                    self.detailed_log("Candidatura confirmada após aguardar!", "SUCCESS")
                    return True
                    
            return False
            
        except Exception as e:
            self.detailed_log(f"Erro ao verificar candidatura: {str(e)}", "WARNING")
            return False
            
    def run_full_automation(self, username=None, password=None, job_types=None, max_applications=3):
        """Executa automação completa"""
        try:
            self.detailed_log("=== INICIANDO AUTOMAÇÃO LINKEDIN COM PERFIL ===", "SUCCESS")
            
            # 1. Login (apenas se necessário)
            if not self.login_if_needed(username, password):
                return {"success": False, "error": "Falha no login"}
                
            # 2. Navegar para seção de vagas
            if not self.navigate_to_jobs_section():
                return {"success": False, "error": "Falha ao navegar para vagas"}
                
            # 3. Aplicar filtros
            if not self.apply_filters():
                return {"success": False, "error": "Falha ao aplicar filtros"}
                
            # 4. Buscar e aplicar para vagas
            if not job_types:
                job_types = ["analista financeiro"]
                
            results = self.search_and_apply_jobs(job_types, max_applications)
            
            return results
            
        except Exception as e:
            self.detailed_log(f"Erro na automação completa: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
            
    def close(self):
        """Fecha o navegador"""
        try:
            if self.driver:
                self.driver.quit()
                self.detailed_log("Navegador fechado")
        except Exception as e:
            self.detailed_log(f"Erro ao fechar navegador: {str(e)}", "WARNING")

