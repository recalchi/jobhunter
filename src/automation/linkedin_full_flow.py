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

class LinkedInFullFlow:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.applied_jobs = []
        self.failed_applications = []
        self.setup_logging()
        
        # URLs baseadas no teste em tempo real e feedback do usuário
        self.login_url = "https://www.linkedin.com/checkpoint/lg/sign-in-another-account"
        self.jobs_home_url = "https://www.linkedin.com/jobs"
        
        # URL de busca com filtros pré-aplicados (São Paulo, Candidatura Simplificada)
        # Construída dinamicamente para maior robustez
        self.filtered_jobs_base_url = "https://www.linkedin.com/jobs/search/?f_AL=true&geoId=104746682&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true&sortBy=R"
        
        # Contador de screenshots para debug
        self.screenshot_counter = 0
        self.session_id = None # Será definido na chamada do start_full_automation

        
        # ID da sessão de automação para rastreamento

        
    def setup_logging(self):
        """Configura o logging detalhado"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def detailed_log(self, message, level="INFO"):
        """Log detalhado com timestamp e formatação clara"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] LinkedIn Full Flow: {message}"
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
        """Configura o driver do Chrome com opções limpas e robustas"""
        try:
            self.detailed_log("=== ETAPA 1: CONFIGURANDO DRIVER DO CHROME ===", "SUCCESS")
            
            chrome_options = Options()
            
            # Configurações básicas para inicialização limpa
            if self.headless:
                chrome_options.add_argument("--headless")
                self.detailed_log("Modo headless ativado")
            else:
                self.detailed_log("Modo visual ativado (recomendado para debug)")
            
            # Argumentos para Chrome limpo e evitar detecção
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            
            # Configurações para evitar problemas de inicialização e restauração
            chrome_options.add_argument("--no-default-browser-check")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-session-crashed-bubble")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--start-maximized") # Abre o navegador em tela cheia
            chrome_options.add_argument("--incognito") # Inicia em modo anônimo para sessão limpa
            
            # Desabilita o popup de salvar senha
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            chrome_options.add_experimental_option("prefs", prefs)

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
            self.driver.execute_script("Object.defineProperty(navigator, \'webdriver\', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 20) # Aumenta o tempo de espera
            
            # Screenshot inicial
            self.take_debug_screenshot("driver_setup_success")
            
            return True
            
        except Exception as e:
            self.detailed_log(f"❌ Erro geral ao configurar driver: {str(e)}", "ERROR")
            return False
            
    def is_logged_in(self):
        """Verifica se o usuário já está logado no LinkedIn"""
        self.detailed_log("Verificando status de login...")
        try:
            # Tenta encontrar um elemento que só aparece quando logado (ex: ícone de perfil)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#global-nav-typeahead")))
            self.detailed_log("✅ Elemento de usuário logado encontrado. Parece que já estamos logados.", "SUCCESS")
            return True
        except TimeoutException:
            self.detailed_log("❌ Elemento de usuário logado não encontrado. Não estamos logados.", "INFO")
            return False

    def step_2_login(self, username, password):
        """ETAPA 2: Realiza o login no LinkedIn"""
        self.detailed_log("=== ETAPA 2: REALIZANDO LOGIN ===", "SUCCESS")
        
        # Tenta navegar para a página de login
        try:
            self.detailed_log(f"Navegando para a página de login: {self.login_url}")
            self.driver.get(self.login_url)
            self.wait.until(EC.url_contains("linkedin.com/checkpoint/lg/sign-in-another-account"))
            self.take_debug_screenshot("login_page_loaded")
            self.detailed_log("✅ Página de login carregada.")
        except TimeoutException:
            self.detailed_log("❌ Não foi possível carregar a página de login esperada.", "ERROR")
            return False

        try:
            # Preenche email
            self.detailed_log("Procurando campo de email...")
            email_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#username")))
            self.detailed_log("✅ Campo de email encontrado.")
            email_field.clear()
            for char in username:
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            self.detailed_log("✅ Email preenchido.")
            self.take_debug_screenshot("email_filled")

            # Preenche senha
            self.detailed_log("Procurando campo de senha...")
            password_field = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#password")))
            self.detailed_log("✅ Campo de senha encontrado.")
            password_field.clear()
            for char in password:
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            self.detailed_log("✅ Senha preenchida.")
            self.take_debug_screenshot("password_filled")

            # Clica no botão de login
            self.detailed_log("Procurando botão de login...")
            login_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type=\'submit\']")))
            self.detailed_log("✅ Botão de login encontrado.")
            login_button.click()
            self.detailed_log("✅ Botão de login clicado.")
            self.take_debug_screenshot("login_button_clicked")

            # Aguarda o redirecionamento após o login
            self.detailed_log("Aguardando redirecionamento após login...")
            self.wait.until(EC.url_changes(self.login_url))
            self.detailed_log("✅ Redirecionamento detectado.")
            self.take_debug_screenshot("after_login_redirect")

            # Verifica se houve verificação de segurança
            if "checkpoint/challenge" in self.driver.current_url:
                self.detailed_log("⚠️ Verificação de segurança detectada. Intervenção manual pode ser necessária.", "WARNING")
                self.take_debug_screenshot("security_challenge")
                # Aqui você pode adicionar uma pausa ou notificação para o usuário
                time.sleep(10) # Pausa para o usuário resolver o captcha
                if "checkpoint/challenge" in self.driver.current_url: # Verifica se ainda está no captcha
                    self.detailed_log("❌ Usuário não resolveu o captcha a tempo ou falha na verificação.", "ERROR")
                    return False

            if self.is_logged_in():
                self.detailed_log("✅ Login bem-sucedido!", "SUCCESS")
                return True
            else:
                self.detailed_log("❌ Login falhou ou não foi detectado corretamente.", "ERROR")
                return False

        except Exception as e:
            self.detailed_log(f"❌ Erro durante o processo de login: {str(e)}", "ERROR")
            self.take_debug_screenshot("login_process_error")
            return False

    def step_3_navigate_to_filtered_jobs(self, job_types):
        """ETAPA 3: Navega para a página inicial de vagas, clica em 'Exibir todas' e aplica filtros"""
        self.detailed_log("=== ETAPA 3: NAVEGANDO PARA VAGAS E APLICANDO FILTROS ===", "SUCCESS")

        try:
            self.detailed_log(f"Navegando para a página inicial de vagas: {self.jobs_home_url}")
            self.driver.get(self.jobs_home_url)
            self.wait.until(EC.url_contains("linkedin.com/jobs"))
            self.take_debug_screenshot("jobs_home_page_loaded")
            self.detailed_log("✅ Página inicial de vagas carregada.")

            # Clicar em 'Exibir todas' ou similar
            self.detailed_log("Procurando e clicando em 'Exibir todas'...")
            try:
                # Tentativa 1: Botão 'Exibir todas' para todas as vagas
                view_all_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/jobs/search/') and contains(., 'Exibir todas')]" )))
                view_all_button.click()
                self.detailed_log("✅ Botão 'Exibir todas' clicado.")
                self.take_debug_screenshot("view_all_jobs_clicked")
                self.wait.until(EC.url_contains("linkedin.com/jobs/search"))
                self.detailed_log("✅ Redirecionado para a página de busca de vagas.")
            except TimeoutException:
                self.detailed_log("⚠️ Botão 'Exibir todas' não encontrado ou não clicável. Tentando alternativa.", "WARNING")
                # Se o botão não for encontrado, pode ser que já esteja na página de busca ou o seletor mudou.
                # Tentar navegar diretamente para a URL de busca padrão se o botão não for encontrado.
                self.driver.get("https://www.linkedin.com/jobs/search/")
                self.wait.until(EC.url_contains("linkedin.com/jobs/search"))
                self.detailed_log("✅ Navegado diretamente para a página de busca de vagas.")
                self.take_debug_screenshot("direct_jobs_search_page")

            # Agora, aplicar os filtros de busca
            self.detailed_log("Aplicando termos de busca e localização...")
            
            # Preencher campo de busca de vagas
            search_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id^=\'jobs-search-box-keyword-id-\']")))
            search_input.clear()
            search_terms = " OR ".join([f'"{jt}"' for jt in job_types])
            search_input.send_keys(search_terms)

            # Preencher campo de localização
            location_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[id^=\'jobs-search-box-location-id-\"]")))

            location_input.clear()
            location_text = "São Paulo, SP"
            location_input.send_keys(location_text)
            location_input.send_keys(Keys.RETURN) # Pressiona Enter para aplicar a localização
            time.sleep(random.uniform(1, 2)) # Pequena pausa para garantir que a localização seja processada
            self.detailed_log(f"✅ Localização \'{location_text}\' aplicada.")
            self.take_debug_screenshot("location_applied")
            time.sleep(random.uniform(2, 4)) # Aguarda a página recarregar com os filtros

            # Clicar em "Todos os filtros"
            self.detailed_log("Clicando em \"Todos os filtros\"...")
            all_filters_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., \'Todos os filtros\')]" )))
            all_filters_button.click()
            self.detailed_log("✅ Botão \"Todos os filtros\" clicado.")
            self.take_debug_screenshot("all_filters_clicked")
            time.sleep(random.uniform(2, 4)) # Aguarda o modal de filtros abrir

            # Ativar filtro de Candidatura Simplificada (Easy Apply) dentro do modal
            self.detailed_log("Ativando filtro \"Candidatura Simplificada\"...")
            try:
                # Rola para baixo no modal de filtros para garantir que o elemento esteja visível
                modal_content = self.driver.find_element(By.CSS_SELECTOR, ".artdeco-modal__content")
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", modal_content)
                time.sleep(random.uniform(1, 2))
                self.take_debug_screenshot("scrolled_filters_modal")

                easy_apply_toggle = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(., 'Candidatura simplificada')]/ancestor::li//input[@type='checkbox']")))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", easy_apply_toggle)
                time.sleep(random.uniform(1, 2)) # Garante que o elemento esteja visível após rolagem
                if not easy_apply_toggle.is_selected():
                    self.driver.execute_script("arguments[0].click();", easy_apply_toggle)
                    self.detailed_log("✅ Filtro \"Candidatura Simplificada\" ativado.")
                    self.take_debug_screenshot("easy_apply_filter_activated")
                else:
                    self.detailed_log("ℹ️ Filtro \"Candidatura Simplificada\" já estava ativado.", "INFO")
            except TimeoutException:
                self.detailed_log("❌ Toggle de \"Candidatura Simplificada\" não encontrado ou não clicável.", "ERROR")
                self.take_debug_screenshot("easy_apply_toggle_not_found")
                return False

            # Clicar no botão "Exibir resultados" ou similar no modal de filtros
            self.detailed_log("Clicando em \"Exibir resultados\" no modal de filtros...")
            show_results_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., \'Exibir resultados\')]" )))
            show_results_button.click()
            self.detailed_log("✅ Botão \"Exibir resultados\" clicado.")
            self.take_debug_screenshot("show_results_clicked")
            self.wait.until(EC.url_contains("linkedin.com/jobs/search")) # Aguarda a página recarregar com os filtros
            self.detailed_log("✅ Página de vagas com filtros atualizados carregada.")
            return True

        except TimeoutException:
            self.detailed_log("❌ Erro de timeout ao navegar ou aplicar filtros.", "ERROR")
            self.take_debug_screenshot("navigation_filter_timeout_error")
            return False
        except Exception as e:
            self.detailed_log(f"💥 Erro geral na navegação e aplicação de filtros: {str(e)}", "ERROR")
            self.take_debug_screenshot("navigation_filter_general_error")
            return False

    def step_4_process_jobs(self, job_types, max_applications):
        """ETAPA 4: Processa as vagas encontradas"""
        self.detailed_log("=== ETAPA 4: PROCESSANDO VAGAS ===", "SUCCESS")
        applications_sent_count = 0
        processed_job_ids = set() # Para evitar processar a mesma vaga múltiplas vezes

        while applications_sent_count < max_applications:
            self.detailed_log("Aguardando carregamento dos cards de vagas...")
            try:
                # Espera por um dos seletores de cards de vaga
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results__list-item")))
                self.take_debug_screenshot("job_cards_loaded")
                self.detailed_log("✅ Cards de vagas carregados.")
            except TimeoutException:
                self.detailed_log("❌ Nenhum card de vaga encontrado após espera.", "ERROR")
                break

            # Tenta encontrar os cards de vaga com múltiplos seletores
            job_cards = []
            selectors = [
                ".jobs-search-results__list-item",
                ".job-card-container",
                "li.job-card-list__item",
                "li.jobs-search-results__list-item",
                "div.job-card-container__metadata", # Pode ser o container da metadata
                "a.job-card-list__title", # Link do título da vaga
                "div.job-card-container__content"
            ]
            
            for i, selector in enumerate(selectors):
                try:
                    self.detailed_log(f"Tentando seletor de card {i+1}: {selector}")
                    found_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if found_cards:
                        job_cards.extend(found_cards)
                        self.detailed_log(f"✅ Encontrados {len(found_cards)} cards com seletor {selector}")
                        # Remove duplicatas se houver
                        job_cards = list(set(job_cards))
                        break # Sai do loop de seletores se encontrar
                except NoSuchElementException:
                    self.detailed_log(f"Seletor {selector} não encontrado.")
                    continue
            
            if not job_cards:
                self.detailed_log("❌ Nenhum card de vaga encontrado após tentar todos os seletores.", "ERROR")
                self.take_debug_screenshot("no_job_cards_found")
                break

            self.detailed_log(f"Total de {len(job_cards)} cards de vaga para processar.")

            for card_index, job_card in enumerate(job_cards):
                if applications_sent_count >= max_applications:
                    self.detailed_log("Limite de aplicações atingido.")
                    break

                try:
                    # Extrai informações básicas do card
                    job_title_element = job_card.find_element(By.CSS_SELECTOR, ".job-card-list__title")
                    job_title = job_title_element.text.strip()
                    job_url = job_title_element.get_attribute("href")
                    job_id = job_url.split("currentJobId=")[1].split("&")[0] if "currentJobId=" in job_url else None

                    if job_id in processed_job_ids:
                        self.detailed_log(f"Vaga {job_title} (ID: {job_id}) já processada, pulando.")
                        continue

                    company_element = job_card.find_element(By.CSS_SELECTOR, ".job-card-list__company-name")
                    company_name = company_element.text.strip()
                    location_element = job_card.find_element(By.CSS_SELECTOR, ".job-card-list__location")
                    location = location_element.text.strip()

                    self.detailed_log(f"Processando vaga: {job_title} na {company_name} ({location})")

                    # Clica no card para carregar a descrição à direita
                    self.detailed_log("Clicando no card da vaga para ver detalhes...")
                    job_card.click()
                    time.sleep(random.uniform(2, 4)) # Pequena pausa para carregar detalhes
                    self.take_debug_screenshot(f"job_card_clicked_{job_id}")

                    # Espera a descrição da vaga carregar
                    self.detailed_log("Aguardando descrição da vaga carregar...")
                    job_description_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-description-content__text")))
                    job_description = job_description_element.text.lower()
                    self.detailed_log("✅ Descrição da vaga carregada.")

                    # Verifica relevância da vaga
                    is_relevant = self.check_job_relevance(job_title, job_description, job_types)
                    if not is_relevant:
                        self.detailed_log(f"Vaga \'{job_title}\' não é relevante, pulando.")
                        processed_job_ids.add(job_id)
                        continue

                    self.detailed_log(f"Vaga \'{job_title}\' é relevante. Verificando Candidatura Simplificada...")

                    # Verifica se é Candidatura Simplificada e aplica
                    try:
                        easy_apply_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".jobs-apply-button[data-job-id]")))
                        if "Candidatura simplificada" in easy_apply_button.text or "Easy Apply" in easy_apply_button.text:
                            self.detailed_log("✅ Botão \'Candidatura simplificada\' encontrado.")
                            easy_apply_button.click()
                            self.detailed_log("✅ Clicado em \'Candidatura simplificada\'.")
                            self.take_debug_screenshot(f"easy_apply_clicked_{job_id}")

                            # Processa o modal de candidatura
                            if self.process_easy_apply_modal(job_id):
                                applications_sent_count += 1
                                self.detailed_log(f"🎉 Candidatura para \'{job_title}\' enviada com sucesso! Total: {applications_sent_count}", "SUCCESS")
                                self.applied_jobs.append({
                                    "title": job_title,
                                    "company": company_name,
                                    "location": location,
                                    "url": job_url,
                                    "job_id": job_id,
                                    "status": "applied"
                                })
                            else:
                                self.detailed_log(f"❌ Falha ao processar candidatura para \'{job_title}\'", "ERROR")
                                self.failed_applications.append({
                                    "title": job_title,
                                    "company": company_name,
                                    "location": location,
                                    "url": job_url,
                                    "job_id": job_id,
                                    "status": "failed"
                                })
                        else:
                            self.detailed_log(f"Botão de aplicação para \'{job_title}\' não é \'Candidatura simplificada\', pulando.")
                    except TimeoutException:
                        self.detailed_log(f"❌ Botão \'Candidatura simplificada\' não encontrado para \'{job_title}\'", "WARNING")
                        self.failed_applications.append({
                            "title": job_title,
                            "company": company_name,
                            "location": location,
                            "url": job_url,
                            "job_id": job_id,
                            "status": "skipped_no_easy_apply"
                        })
                    except Exception as e:
                        self.detailed_log(f"❌ Erro ao tentar aplicar para \'{job_title}\': {str(e)}", "ERROR")
                        self.failed_applications.append({
                            "title": job_title,
                            "company": company_name,
                            "location": location,
                            "url": job_url,
                            "job_id": job_id,
                            "status": "failed_exception"
                        })

                    processed_job_ids.add(job_id)

                except Exception as e:
                    self.detailed_log(f"❌ Erro ao processar card de vaga: {str(e)}", "ERROR")
                    self.take_debug_screenshot(f"error_processing_card_{card_index}")
                    # Continua para o próximo card mesmo em caso de erro

            # Rola a página para carregar mais vagas
            self.detailed_log("Rolando a página para carregar mais vagas...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(3, 5)) # Espera para carregar novas vagas
            self.take_debug_screenshot("page_scrolled")

            # Verifica se novas vagas foram carregadas, se não, sai do loop
            new_job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")
            if len(new_job_cards) == len(job_cards): # Se o número de cards não aumentou
                self.detailed_log("Não há mais vagas para carregar ou limite de rolagem atingido.")
                break
            job_cards = new_job_cards # Atualiza a lista de cards para a próxima iteração

        return applications_sent_count

    def check_job_relevance(self, job_title, job_description, job_types):
        """Verifica se a vaga é relevante com base no título e descrição"""
        job_title_lower = job_title.lower()
        
        # Palavras-chave gerais para analista financeiro e áreas relacionadas
        keywords = {
            "analista financeiro": ["analista financeiro", "financial analyst", "finanças", "financeiro", "fp&a", "planejamento financeiro", "controladoria"],
            "contas a pagar": ["contas a pagar", "accounts payable", "ap", "pagamentos", "fornecedores"],
            "contas a receber": ["contas a receber", "accounts receivable", "ar", "recebimentos", "clientes"],
            "analista de precificacao": ["precificação", "pricing", "analista de precificação", "pricing analyst"],
            "custos": ["custos", "cost analyst", "orçamento", "budget"],
            "backoffice": ["backoffice", "suporte administrativo", "assistente administrativo", "operações", "apoio operacional", "processos internos"]
        }

        # Verifica se o título ou descrição contém alguma das palavras-chave relevantes
        for job_type in job_types:
            for keyword in keywords.get(job_type, []):
                if keyword in job_title_lower or keyword in job_description:
                    self.detailed_log(f"Vaga relevante encontrada para \'{job_type}\' com a palavra-chave \'{keyword}\'")
                    return True
        
        # Se não encontrar nenhuma palavra-chave específica, verifica por termos mais amplos
        general_keywords = ["analista", "financeiro", "contas", "custos", "precificação"]
        for keyword in general_keywords:
            if keyword in job_title_lower or keyword in job_description:
                self.detailed_log(f"Vaga potencialmente relevante encontrada com a palavra-chave geral \'{keyword}\'")
                return True

        return False

    def process_easy_apply_modal(self, job_id):
        """Processa o modal de Candidatura Simplificada"""
        self.detailed_log("Iniciando processamento do modal de Candidatura Simplificada...")
        try:
            # Espera o modal aparecer
            modal_selector = ".artdeco-modal-overlay"
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, modal_selector)))
            self.detailed_log("✅ Modal de candidatura simplificada detectado.")
            self.take_debug_screenshot(f"easy_apply_modal_opened_{job_id}")

            # Loop para navegar pelas etapas do modal
            while True:
                # Rola o modal para garantir que todos os elementos estejam visíveis
                self.detailed_log("Rolando o modal para baixo...")
                self.driver.execute_script("document.querySelector(\".artdeco-modal-overlay\").scrollTop = document.querySelector(\".artdeco-modal-overlay\").scrollHeight;")
                time.sleep(random.uniform(1, 2))

                # Tenta encontrar o botão \'Avançar\' ou \'Revisar\' ou \'Enviar candidatura\'
                next_button_selectors = [
                    "button[aria-label=\'Avançar\']",
                    "button[aria-label=\'Revisar\']",
                    "button[aria-label=\'Enviar candidatura\']",
                    "button[data-control-name=\'submit_application\']",
                    "button[data-test-id=\'submit-button\']",
                    "button[data-test-id=\'next-button\']"
                ]
                
                next_button = None
                for selector in next_button_selectors:
                    try:
                        next_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                        if next_button.is_displayed() and next_button.is_enabled():
                            self.detailed_log(f"✅ Botão \'{next_button.text}\' encontrado.")
                            break
                        else:
                            next_button = None
                    except TimeoutException:
                        continue
                
                if not next_button:
                    self.detailed_log("❌ Nenhum botão de navegação no modal encontrado. Tentando fechar modal.", "ERROR")
                    self.take_debug_screenshot(f"no_modal_button_{job_id}")
                    self.close_modal()
                    return False # Falha ao processar o modal

                button_text = next_button.text.lower()

                # Lida com perguntas
                self.handle_modal_questions()

                # Clica no botão
                self.detailed_log(f"Clicando em \'{next_button.text}\'...")
                next_button.click()
                self.take_debug_screenshot(f"modal_button_clicked_{button_text.replace(' ', '_')}_{job_id}")
                time.sleep(random.uniform(2, 4))

                if "enviar candidatura" in button_text or "submit application" in button_text:
                    self.detailed_log("✅ Candidatura enviada! Aguardando confirmação...")
                    # Espera a mensagem de confirmação ou o modal fechar
                    try:
                        self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, modal_selector)))
                        self.detailed_log("✅ Modal de candidatura fechado. Candidatura provavelmente enviada.", "SUCCESS")
                        return True
                    except TimeoutException:
                        self.detailed_log("❌ Modal não fechou após enviar candidatura. Pode haver erro ou confirmação na tela.", "ERROR")
                        self.take_debug_screenshot(f"modal_not_closed_after_submit_{job_id}")
                        self.close_modal()
                        return False
                elif "concluído" in button_text or "done" in button_text:
                    self.detailed_log("✅ Botão \'Concluído\' clicado. Candidatura finalizada.", "SUCCESS")
                    self.close_modal()
                    return True
                else:
                    self.detailed_log(f"Avançando para a próxima etapa do modal: {button_text}")
                    # Continua o loop para a próxima etapa do modal

        except Exception as e:
            self.detailed_log(f"❌ Erro ao processar modal de candidatura: {str(e)}", "ERROR")
            self.take_debug_screenshot(f"modal_process_error_{job_id}")
            self.close_modal()
            return False

    def handle_modal_questions(self):
        """Lida com perguntas dentro do modal de candidatura"""
        self.detailed_log("Verificando perguntas no modal...")
        # Perguntas e respostas padrão
        questions_and_answers = {
            "Você aceita um modelo de contratação PJ (Pessoa Jurídica)?": "Sim",
            "Qual é a sua pretensão de remuneração mensal?": "1900.00", # Baseado no padrão do usuário
            "Qual o seu nível de conhecimento com Excel? Dê uma nota de 0 a 10, por favor)": "8",
            "Qual o seu nível de conhecimento com ferramentas de ERP? Dê uma nota de 0 a 10, por favor)": "9"
        }

        # Tenta encontrar campos de texto ou radio buttons para perguntas
        question_elements = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-easy-apply-form-section__grouping")
        for q_element in question_elements:
            try:
                question_text_element = q_element.find_element(By.CSS_SELECTOR, ".jobs-easy-apply-form-section__question-title")
                question_text = question_text_element.text.strip()
                self.detailed_log(f"Pergunta detectada: {question_text}")

                if question_text in questions_and_answers:
                    answer = questions_and_answers[question_text]
                    self.detailed_log(f"Respondendo \'{question_text}\' com \'{answer}\'")

                    # Tenta preencher campo de texto
                    try:
                        input_field = q_element.find_element(By.CSS_SELECTOR, "input[type=\'text\'], textarea")
                        input_field.clear()
                        input_field.send_keys(answer)
                        self.detailed_log("✅ Campo de texto preenchido.")
                        continue
                    except NoSuchElementException:
                        pass # Não é campo de texto

                    # Tenta selecionar radio button ou checkbox
                    try:
                        # Procura por labels que contenham a resposta
                        radio_or_checkbox_labels = q_element.find_elements(By.CSS_SELECTOR, "label")
                        for label in radio_or_checkbox_labels:
                            if answer.lower() in label.text.lower():
                                # Clica no input associado à label
                                self.detailed_log(f"Clicando em opção: {label.text}")
                                label.click()
                                self.detailed_log("✅ Opção selecionada.")
                                break
                        continue
                    except NoSuchElementException:
                        pass # Não é radio/checkbox

                else:
                    self.detailed_log(f"❓ Pergunta não mapeada: {question_text}. Tentando pular.", "WARNING")

            except NoSuchElementException:
                continue # Não é um elemento de pergunta
            except Exception as e:
                self.detailed_log(f"❌ Erro ao lidar com pergunta: {str(e)}", "ERROR")

    def close_modal(self):
        """Tenta fechar qualquer modal aberto"""
        self.detailed_log("Tentando fechar modal...")
        try:
            close_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".artdeco-modal__dismiss")))
            close_button.click()
            self.detailed_log("✅ Modal fechado com sucesso.")
            self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".artdeco-modal-overlay")))
        except TimeoutException:
            self.detailed_log("❌ Botão de fechar modal não encontrado ou modal não fechou.", "WARNING")
        except Exception as e:
            self.detailed_log(f"❌ Erro ao fechar modal: {str(e)}", "ERROR")

    def close(self):
        """Fecha o navegador"""
        if self.driver:
            self.driver.quit()
            self.detailed_log("Navegador fechado.")

    def start_full_automation(self, username, password, job_types, max_applications, session_id):
        """Executa o fluxo completo de automação"""
        self.detailed_log("=== INICIANDO AUTOMAÇÃO COMPLETA DO LINKEDIN ===", "SUCCESS")
        self.session_id = session_id


        if not self.setup_driver():
            return {"success": False, "error": "Falha ao configurar o driver do navegador.", "session_id": self.session_id}

        # Tenta login se não estiver logado
        if not self.is_logged_in():
            if not self.step_2_login(username, password):
                self.close()
                return {"success": False, "error": "Falha no login do LinkedIn.", "session_id": self.session_id}
        else:
            self.detailed_log("Já logado no LinkedIn, pulando etapa de login.")

        # Navega para vagas filtradas
        if not self.step_3_navigate_to_filtered_jobs(job_types):
            self.close()
            return {"success": False, "error": "Falha ao navegar para vagas filtradas.", "session_id": self.session_id}

        # Processa as vagas
        applications_sent = self.step_4_process_jobs(job_types, max_applications)


        self.close()

        return {
            "success": True,
            "applications_sent": applications_sent,
            "applied_jobs": self.applied_jobs,
            "failed_applications": self.failed_applications,
            "session_id": self.session_id
        }


if __name__ == '__main__':
    # Exemplo de uso
    bot = LinkedInFullFlow(headless=False) # Mude para True para não ver o navegador
    result = bot.run_full_automation(
        username="rena.recalchi@gmail.com",
        password="Yumi1703$",
        job_types=["analista financeiro", "contas a pagar"],
        max_applications=5,
    )
    
    print(json.dumps(result, indent=2))

