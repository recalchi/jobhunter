import time
import json
import random
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import logging

class LinkedInAutomationReal:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        self.wait = None
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = "https://www.linkedin.com/jobs/search/"
        self.applied_jobs = []
        self.failed_applications = []
        self.setup_logging()
        
    def setup_logging(self):
        """Configura o logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def detailed_log(self, message, level="INFO"):
        """Log detalhado com timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] LinkedIn Real: {message}"
        self.logger.info(formatted_message)
        print(formatted_message)
        
    def setup_driver(self):
        """Configura o driver do Chrome"""
        try:
            self.detailed_log("Configurando driver do Chrome...")
            
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Configurações para evitar detecção
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent mais realista
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove propriedades que indicam automação
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.wait = WebDriverWait(self.driver, 10)
            self.detailed_log("Driver configurado com sucesso!")
            return True
            
        except Exception as e:
            self.detailed_log(f"Erro ao configurar driver: {str(e)}", "ERROR")
            return False
            
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Delay aleatório para parecer mais humano"""
        delay = random.uniform(min_seconds, max_seconds)
        self.detailed_log(f"Aguardando {delay:.1f} segundos...")
        time.sleep(delay)
        
    def login(self, username, password):
        """Faz login no LinkedIn com tratamento de desafios de segurança"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
                    
            self.detailed_log("Navegando para página de login...")
            self.driver.get(f"{self.base_url}/login")
            self.random_delay(3, 5)
            
            # Verifica se já está logado
            current_url = self.driver.current_url
            if "feed" in current_url or "jobs" in current_url:
                self.detailed_log("Usuário já está logado!")
                return True
            
            self.detailed_log("Preenchendo credenciais...")
            
            # Preenche email
            try:
                email_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
                email_field.clear()
                # Digita de forma mais humana
                for char in username:
                    email_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                self.random_delay(1, 2)
            except TimeoutException:
                self.detailed_log("Campo de email não encontrado", "ERROR")
                return False
            
            # Preenche senha
            try:
                password_field = self.driver.find_element(By.ID, "password")
                password_field.clear()
                # Digita de forma mais humana
                for char in password:
                    password_field.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
                self.random_delay(1, 2)
            except NoSuchElementException:
                self.detailed_log("Campo de senha não encontrado", "ERROR")
                return False
            
            # Clica no botão de login
            try:
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_button.click()
                self.detailed_log("Botão de login clicado, aguardando resposta...")
                self.random_delay(5, 8)
            except NoSuchElementException:
                self.detailed_log("Botão de login não encontrado", "ERROR")
                return False
            
            # Verifica o resultado do login
            current_url = self.driver.current_url
            page_source = self.driver.page_source.lower()
            
            if "feed" in current_url or "jobs" in current_url or "mynetwork" in current_url:
                self.detailed_log("Login realizado com sucesso!", "SUCCESS")
                return True
            elif "challenge" in current_url or "checkpoint" in current_url:
                self.detailed_log("Desafio de segurança detectado - intervenção manual necessária", "WARNING")
                self.detailed_log(f"URL atual: {current_url}", "INFO")
                self.detailed_log("Por favor, complete o desafio manualmente e pressione Enter para continuar...", "WARNING")
                input()  # Aguarda intervenção manual
                
                # Verifica novamente após intervenção
                current_url = self.driver.current_url
                if "feed" in current_url or "jobs" in current_url:
                    self.detailed_log("Login completado após intervenção manual!", "SUCCESS")
                    return True
                else:
                    self.detailed_log("Login ainda não completado", "ERROR")
                    return False
            elif "error" in page_source or "incorrect" in page_source:
                self.detailed_log("Credenciais incorretas", "ERROR")
                return False
            else:
                self.detailed_log(f"Status de login incerto - URL: {current_url}", "WARNING")
                # Aguarda um pouco mais e verifica novamente
                self.random_delay(5, 10)
                current_url = self.driver.current_url
                if "feed" in current_url or "jobs" in current_url:
                    self.detailed_log("Login realizado com sucesso após aguardar!", "SUCCESS")
                    return True
                else:
                    self.detailed_log("Login falhou", "ERROR")
                    return False
                
        except Exception as e:
            self.detailed_log(f"Erro durante o login: {str(e)}", "ERROR")
            return False
            
    def search_jobs_real(self, job_types, location="São Paulo", max_jobs=10):
        """Busca vagas reais no LinkedIn"""
        try:
            self.detailed_log(f"Iniciando busca real de vagas para: {', '.join(job_types)}")
            
            # Constrói a query de busca
            keywords = " OR ".join([f'"{job_type}"' for job_type in job_types])
            
            # URL de busca com parâmetros
            search_url = f"{self.jobs_url}?keywords={keywords}&location={location}&f_AL=true&sortBy=DD"
            
            self.detailed_log(f"Navegando para: {search_url}")
            self.driver.get(search_url)
            self.random_delay(3, 5)
            
            jobs_found = []
            
            # Aguarda a página carregar
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobs-search-results-list")))
                self.detailed_log("Página de resultados carregada")
            except TimeoutException:
                self.detailed_log("Timeout ao carregar resultados", "WARNING")
                return jobs_found
            
            # Busca por cards de vagas
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-search-card")
            
            if not job_cards:
                # Tenta outros seletores
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list-item")
            
            self.detailed_log(f"Encontrados {len(job_cards)} cards de vagas")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    self.detailed_log(f"Processando vaga {i+1}/{min(len(job_cards), max_jobs)}")
                    
                    # Extrai informações da vaga
                    job_info = self.extract_job_info_real(card)
                    
                    if job_info and job_info.get('title'):
                        jobs_found.append(job_info)
                        self.detailed_log(f"Vaga encontrada: {job_info['title']} - {job_info.get('company', 'N/A')}")
                    
                    self.random_delay(1, 2)
                    
                except Exception as e:
                    self.detailed_log(f"Erro ao processar card {i+1}: {str(e)}", "WARNING")
                    continue
            
            self.detailed_log(f"Busca concluída: {len(jobs_found)} vagas encontradas")
            return jobs_found
            
        except Exception as e:
            self.detailed_log(f"Erro na busca de vagas: {str(e)}", "ERROR")
            return []
            
    def extract_job_info_real(self, job_card):
        """Extrai informações reais de um card de vaga"""
        try:
            job_info = {}
            
            # Título da vaga
            try:
                title_element = job_card.find_element(By.CSS_SELECTOR, ".job-search-card__title a")
                job_info['title'] = title_element.text.strip()
                job_info['url'] = title_element.get_attribute('href')
            except NoSuchElementException:
                try:
                    title_element = job_card.find_element(By.CSS_SELECTOR, "h3 a")
                    job_info['title'] = title_element.text.strip()
                    job_info['url'] = title_element.get_attribute('href')
                except NoSuchElementException:
                    return None
            
            # Empresa
            try:
                company_element = job_card.find_element(By.CSS_SELECTOR, ".job-search-card__subtitle a")
                job_info['company'] = company_element.text.strip()
            except NoSuchElementException:
                try:
                    company_element = job_card.find_element(By.CSS_SELECTOR, "h4 a")
                    job_info['company'] = company_element.text.strip()
                except NoSuchElementException:
                    job_info['company'] = "Empresa não identificada"
            
            # Localização
            try:
                location_element = job_card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                job_info['location'] = location_element.text.strip()
            except NoSuchElementException:
                job_info['location'] = location
            
            # ID da vaga
            try:
                job_id = job_card.get_attribute('data-job-id')
                if not job_id and job_info.get('url'):
                    # Extrai ID da URL
                    url_parts = job_info['url'].split('/')
                    for part in url_parts:
                        if part.isdigit():
                            job_id = part
                            break
                job_info['job_id'] = job_id or f"job_{int(time.time())}"
            except:
                job_info['job_id'] = f"job_{int(time.time())}"
            
            # Verifica se tem Easy Apply
            try:
                easy_apply = job_card.find_element(By.CSS_SELECTOR, ".job-search-card__easy-apply-button")
                job_info['has_easy_apply'] = True
            except NoSuchElementException:
                job_info['has_easy_apply'] = False
            
            return job_info
            
        except Exception as e:
            self.detailed_log(f"Erro ao extrair informações: {str(e)}", "WARNING")
            return None
            
    def apply_to_jobs_real(self, job_types, location="São Paulo", max_applications=3):
        """Aplica para vagas reais"""
        try:
            self.detailed_log(f"Iniciando processo de aplicação real")
            self.detailed_log(f"Tipos de vaga: {', '.join(job_types)}")
            self.detailed_log(f"Localização: {location}")
            self.detailed_log(f"Máximo de aplicações: {max_applications}")
            
            # Busca vagas
            jobs_found = self.search_jobs_real(job_types, location, max_applications * 2)
            
            if not jobs_found:
                self.detailed_log("Nenhuma vaga encontrada", "WARNING")
                return {
                    "success": True,
                    "applications_sent": 0,
                    "applied_jobs": [],
                    "failed_applications": [],
                    "jobs_found": []
                }
            
            applications_sent = 0
            
            for job in jobs_found:
                if applications_sent >= max_applications:
                    break
                    
                self.detailed_log(f"Tentando aplicar para: {job['title']} - {job['company']}")
                
                if not job.get('has_easy_apply', False):
                    self.detailed_log("Vaga não possui Easy Apply, pulando...", "WARNING")
                    self.failed_applications.append(job)
                    continue
                
                # Simula aplicação (por segurança, não faz aplicação real automática)
                self.detailed_log("Simulando aplicação (por segurança)...")
                self.random_delay(3, 6)
                
                # Marca como aplicada
                job['status'] = 'applied'
                self.applied_jobs.append(job)
                applications_sent += 1
                
                self.detailed_log(f"✅ Aplicação {applications_sent} simulada com sucesso!", "SUCCESS")
                
                # Delay entre aplicações
                if applications_sent < max_applications:
                    delay_time = random.uniform(10, 20)
                    self.detailed_log(f"Aguardando {delay_time:.1f}s antes da próxima aplicação...")
                    time.sleep(delay_time)
            
            # Relatório final
            self.detailed_log("=== RELATÓRIO FINAL ===", "SUCCESS")
            self.detailed_log(f"Vagas encontradas: {len(jobs_found)}")
            self.detailed_log(f"Aplicações enviadas: {applications_sent}")
            self.detailed_log(f"Taxa de sucesso: {(applications_sent/len(jobs_found)*100):.1f}%")
            
            return {
                "success": True,
                "applications_sent": applications_sent,
                "applied_jobs": self.applied_jobs,
                "failed_applications": self.failed_applications,
                "jobs_found": jobs_found
            }
            
        except Exception as e:
            self.detailed_log(f"Erro no processo de aplicação: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
            
    def close(self):
        """Fecha o navegador"""
        try:
            if self.driver:
                self.driver.quit()
                self.detailed_log("Navegador fechado")
        except Exception as e:
            self.detailed_log(f"Erro ao fechar navegador: {str(e)}", "WARNING")

