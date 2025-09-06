import time
import json
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from src.automation.base_automation import BaseAutomation

class LinkedInAutomationImproved(BaseAutomation):
    def __init__(self, headless=False):  # Mudando para não headless por padrão para debug
        super().__init__(headless)
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = "https://www.linkedin.com/jobs/search/"
        self.applied_jobs = []
        self.failed_applications = []
        
    def detailed_log(self, message, level="INFO"):
        """Log detalhado com timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] LinkedIn: {message}"
        self.logger.info(formatted_message)
        print(formatted_message)  # Para aparecer no terminal
        
    def random_delay(self, min_seconds=2, max_seconds=5):
        """Delay aleatório para parecer mais humano"""
        delay = random.uniform(min_seconds, max_seconds)
        self.detailed_log(f"Aguardando {delay:.1f} segundos...")
        time.sleep(delay)
        
    def login(self, username, password):
        """Faz login no LinkedIn com logs detalhados"""
        try:
            self.detailed_log("Iniciando processo de login no LinkedIn...")
            self.driver.get(f"{self.base_url}/login")
            self.random_delay(3, 5)
            
            # Verifica se já está logado
            if "feed" in self.driver.current_url or "jobs" in self.driver.current_url:
                self.detailed_log("Usuário já está logado!")
                return True
            
            self.detailed_log("Preenchendo campo de email...")
            email_field = self.wait_for_element(By.ID, "username", timeout=10)
            if not email_field:
                self.detailed_log("Campo de email não encontrado", "ERROR")
                return False
                
            email_field.clear()
            email_field.send_keys(username)
            self.random_delay(1, 2)
            
            self.detailed_log("Preenchendo campo de senha...")
            password_field = self.wait_for_element(By.ID, "password", timeout=10)
            if not password_field:
                self.detailed_log("Campo de senha não encontrado", "ERROR")
                return False
                
            password_field.clear()
            password_field.send_keys(password)
            self.random_delay(1, 2)
            
            self.detailed_log("Clicando no botão de login...")
            login_button = self.wait_for_element(By.XPATH, "//button[@type='submit']", timeout=10)
            if not login_button:
                self.detailed_log("Botão de login não encontrado", "ERROR")
                return False
                
            login_button.click()
            self.random_delay(5, 8)
            
            # Verifica se o login foi bem-sucedido
            current_url = self.driver.current_url
            if "feed" in current_url or "jobs" in current_url or "mynetwork" in current_url:
                self.detailed_log("Login realizado com sucesso!", "SUCCESS")
                return True
            elif "challenge" in current_url:
                self.detailed_log("Desafio de segurança detectado - intervenção manual necessária", "WARNING")
                return False
            else:
                self.detailed_log(f"Login falhou - URL atual: {current_url}", "ERROR")
                return False
                
        except Exception as e:
            self.detailed_log(f"Erro durante o login: {str(e)}", "ERROR")
            return False
            
    def navigate_to_jobs_search(self, job_types, location="São Paulo"):
        """Navega para a página de busca de vagas"""
        try:
            self.detailed_log("Navegando para a página de vagas...")
            
            # Constrói a URL de busca com parâmetros específicos
            keywords = " OR ".join([f'"{job_type}"' for job_type in job_types])
            search_params = {
                'keywords': keywords,
                'location': location,
                'f_AL': 'true',  # Easy Apply
                'f_TPR': 'r86400',  # Últimas 24 horas
                'sortBy': 'DD'  # Mais recentes
            }
            
            # Constrói a URL
            params_str = '&'.join([f"{k}={v}" for k, v in search_params.items()])
            search_url = f"{self.jobs_url}?{params_str}"
            
            self.detailed_log(f"URL de busca: {search_url}")
            self.driver.get(search_url)
            self.random_delay(3, 5)
            
            # Verifica se a página carregou corretamente
            if "jobs/search" in self.driver.current_url:
                self.detailed_log("Página de busca carregada com sucesso!")
                return True
            else:
                self.detailed_log("Falha ao carregar página de busca", "ERROR")
                return False
                
        except Exception as e:
            self.detailed_log(f"Erro ao navegar para busca: {str(e)}", "ERROR")
            return False
            
    def get_job_cards(self):
        """Obtém os cards de vagas da página atual"""
        try:
            self.detailed_log("Buscando cards de vagas na página...")
            
            # Aguarda os cards carregarem
            self.random_delay(2, 4)
            
            # Múltiplos seletores para diferentes layouts do LinkedIn
            selectors = [
                ".job-search-card",
                ".jobs-search-results__list-item",
                "[data-job-id]",
                ".job-card-container"
            ]
            
            job_cards = []
            for selector in selectors:
                try:
                    cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if cards:
                        job_cards = cards
                        self.detailed_log(f"Encontrados {len(job_cards)} cards usando seletor: {selector}")
                        break
                except:
                    continue
                    
            if not job_cards:
                self.detailed_log("Nenhum card de vaga encontrado", "WARNING")
                
            return job_cards
            
        except Exception as e:
            self.detailed_log(f"Erro ao buscar cards: {str(e)}", "ERROR")
            return []
            
    def extract_job_info(self, job_card):
        """Extrai informações de um card de vaga"""
        try:
            job_info = {}
            
            # Título da vaga
            title_selectors = [
                ".job-card-list__title",
                ".job-search-card__title",
                "[data-job-title]",
                "h3 a",
                ".job-title"
            ]
            
            for selector in title_selectors:
                try:
                    title_element = job_card.find_element(By.CSS_SELECTOR, selector)
                    job_info['title'] = title_element.text.strip()
                    job_info['url'] = title_element.get_attribute('href')
                    break
                except:
                    continue
                    
            # Empresa
            company_selectors = [
                ".job-card-container__company-name",
                ".job-search-card__subtitle",
                "[data-job-company]",
                "h4 a",
                ".job-company"
            ]
            
            for selector in company_selectors:
                try:
                    company_element = job_card.find_element(By.CSS_SELECTOR, selector)
                    job_info['company'] = company_element.text.strip()
                    break
                except:
                    continue
                    
            # Localização
            location_selectors = [
                ".job-card-container__metadata-item",
                ".job-search-card__location",
                "[data-job-location]",
                ".job-location"
            ]
            
            for selector in location_selectors:
                try:
                    location_element = job_card.find_element(By.CSS_SELECTOR, selector)
                    job_info['location'] = location_element.text.strip()
                    break
                except:
                    continue
                    
            # ID da vaga (do atributo data-job-id ou da URL)
            try:
                job_id = job_card.get_attribute('data-job-id')
                if not job_id and 'url' in job_info:
                    # Extrai ID da URL
                    url_parts = job_info['url'].split('/')
                    for part in url_parts:
                        if part.isdigit():
                            job_id = part
                            break
                job_info['job_id'] = job_id or 'unknown'
            except:
                job_info['job_id'] = 'unknown'
                
            return job_info
            
        except Exception as e:
            self.detailed_log(f"Erro ao extrair informações da vaga: {str(e)}", "ERROR")
            return {}
            
    def click_job_card(self, job_card):
        """Clica em um card de vaga para abrir os detalhes"""
        try:
            self.detailed_log("Clicando no card da vaga...")
            
            # Scroll até o elemento
            self.driver.execute_script("arguments[0].scrollIntoView(true);", job_card)
            self.random_delay(1, 2)
            
            # Tenta clicar no card
            try:
                job_card.click()
            except ElementClickInterceptedException:
                # Se não conseguir clicar diretamente, tenta clicar no link
                link = job_card.find_element(By.CSS_SELECTOR, "a")
                link.click()
                
            self.random_delay(2, 4)
            return True
            
        except Exception as e:
            self.detailed_log(f"Erro ao clicar no card: {str(e)}", "ERROR")
            return False
            
    def find_easy_apply_button(self):
        """Encontra o botão Easy Apply"""
        try:
            self.detailed_log("Procurando botão Easy Apply...")
            
            # Múltiplos seletores para o botão Easy Apply
            selectors = [
                "button[aria-label*='Easy Apply']",
                "button[data-control-name='jobdetails_topcard_inapply']",
                ".jobs-apply-button",
                "button:contains('Easy Apply')",
                "button:contains('Candidatar-se')",
                "[data-job-id] button[aria-label*='Apply']"
            ]
            
            for selector in selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            text = button.text.lower()
                            aria_label = button.get_attribute('aria-label').lower() if button.get_attribute('aria-label') else ""
                            
                            if any(keyword in text or keyword in aria_label for keyword in ['easy apply', 'candidatar', 'apply']):
                                self.detailed_log(f"Botão Easy Apply encontrado: {button.text}")
                                return button
                except:
                    continue
                    
            self.detailed_log("Botão Easy Apply não encontrado", "WARNING")
            return None
            
        except Exception as e:
            self.detailed_log(f"Erro ao procurar botão Easy Apply: {str(e)}", "ERROR")
            return None
            
    def handle_easy_apply_process(self):
        """Lida com o processo completo de Easy Apply"""
        try:
            self.detailed_log("Iniciando processo Easy Apply...")
            
            # Aguarda o modal aparecer
            self.random_delay(2, 4)
            
            max_steps = 5
            current_step = 1
            
            while current_step <= max_steps:
                self.detailed_log(f"Processando etapa {current_step} do Easy Apply...")
                
                # Verifica se há campos obrigatórios para preencher
                self.fill_required_fields()
                
                # Procura botões de ação
                next_button = self.find_next_button()
                submit_button = self.find_submit_button()
                
                if submit_button:
                    self.detailed_log("Botão de envio encontrado - finalizando aplicação...")
                    submit_button.click()
                    self.random_delay(3, 5)
                    
                    # Verifica se a aplicação foi enviada
                    if self.check_application_success():
                        self.detailed_log("Aplicação enviada com sucesso!", "SUCCESS")
                        return True
                    else:
                        self.detailed_log("Falha ao enviar aplicação", "ERROR")
                        return False
                        
                elif next_button:
                    self.detailed_log("Avançando para próxima etapa...")
                    next_button.click()
                    self.random_delay(2, 4)
                    current_step += 1
                    
                else:
                    self.detailed_log("Nenhum botão de ação encontrado", "WARNING")
                    break
                    
            self.detailed_log("Processo Easy Apply não completado", "WARNING")
            return False
            
        except Exception as e:
            self.detailed_log(f"Erro no processo Easy Apply: {str(e)}", "ERROR")
            return False
            
    def fill_required_fields(self):
        """Preenche campos obrigatórios básicos"""
        try:
            # Procura por campos de texto obrigatórios
            required_fields = self.driver.find_elements(By.CSS_SELECTOR, "input[required], textarea[required]")
            
            for field in required_fields:
                if field.is_displayed() and not field.get_attribute('value'):
                    field_type = field.get_attribute('type')
                    placeholder = field.get_attribute('placeholder')
                    
                    self.detailed_log(f"Preenchendo campo obrigatório: {placeholder or field_type}")
                    
                    if 'phone' in placeholder.lower() or field_type == 'tel':
                        field.send_keys("(11) 99999-9999")
                    elif 'email' in placeholder.lower() or field_type == 'email':
                        field.send_keys("contato@exemplo.com")
                    else:
                        field.send_keys("Informação não disponível")
                        
                    self.random_delay(0.5, 1)
                    
        except Exception as e:
            self.detailed_log(f"Erro ao preencher campos: {str(e)}", "WARNING")
            
    def find_next_button(self):
        """Encontra botão Next/Próximo"""
        selectors = [
            "button[aria-label*='Next']",
            "button[aria-label*='Próximo']",
            "button:contains('Next')",
            "button:contains('Próximo')",
            ".artdeco-button--primary:contains('Next')"
        ]
        
        for selector in selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button
            except:
                continue
        return None
        
    def find_submit_button(self):
        """Encontra botão Submit/Enviar"""
        selectors = [
            "button[aria-label*='Submit']",
            "button[aria-label*='Enviar']",
            "button:contains('Submit')",
            "button:contains('Enviar')",
            "button:contains('Send')",
            ".artdeco-button--primary:contains('Submit')"
        ]
        
        for selector in selectors:
            try:
                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        return button
            except:
                continue
        return None
        
    def check_application_success(self):
        """Verifica se a aplicação foi enviada com sucesso"""
        try:
            # Procura por mensagens de sucesso
            success_indicators = [
                "Application sent",
                "Candidatura enviada",
                "Your application was sent",
                "Sua candidatura foi enviada"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in success_indicators:
                if indicator.lower() in page_text:
                    return True
                    
            # Verifica se voltou para a página de vagas
            if "jobs/search" in self.driver.current_url:
                return True
                
            return False
            
        except:
            return False
            
    def apply_to_jobs(self, job_types, location="São Paulo", max_applications=5):
        """Aplica para vagas com processo completo e detalhado"""
        try:
            self.detailed_log(f"Iniciando busca e aplicação para: {', '.join(job_types)}")
            self.detailed_log(f"Localização: {location}")
            self.detailed_log(f"Máximo de aplicações: {max_applications}")
            
            # Navega para a busca
            if not self.navigate_to_jobs_search(job_types, location):
                return {"success": False, "error": "Falha ao navegar para busca"}
                
            applications_sent = 0
            page_number = 1
            
            while applications_sent < max_applications and page_number <= 3:
                self.detailed_log(f"Processando página {page_number}...")
                
                # Obtém cards da página atual
                job_cards = self.get_job_cards()
                
                if not job_cards:
                    self.detailed_log("Nenhuma vaga encontrada nesta página")
                    break
                    
                for i, job_card in enumerate(job_cards):
                    if applications_sent >= max_applications:
                        break
                        
                    self.detailed_log(f"Processando vaga {i+1}/{len(job_cards)} da página {page_number}")
                    
                    # Extrai informações da vaga
                    job_info = self.extract_job_info(job_card)
                    
                    if not job_info.get('title'):
                        self.detailed_log("Informações da vaga incompletas, pulando...", "WARNING")
                        continue
                        
                    self.detailed_log(f"Vaga: {job_info.get('title', 'N/A')}")
                    self.detailed_log(f"Empresa: {job_info.get('company', 'N/A')}")
                    self.detailed_log(f"Localização: {job_info.get('location', 'N/A')}")
                    
                    # Clica no card para abrir detalhes
                    if not self.click_job_card(job_card):
                        self.detailed_log("Falha ao abrir detalhes da vaga", "WARNING")
                        continue
                        
                    # Procura botão Easy Apply
                    easy_apply_button = self.find_easy_apply_button()
                    
                    if not easy_apply_button:
                        self.detailed_log("Vaga não possui Easy Apply, pulando...", "WARNING")
                        continue
                        
                    # Clica no Easy Apply
                    self.detailed_log("Clicando em Easy Apply...")
                    easy_apply_button.click()
                    self.random_delay(2, 4)
                    
                    # Processa o Easy Apply
                    if self.handle_easy_apply_process():
                        applications_sent += 1
                        self.applied_jobs.append(job_info)
                        self.detailed_log(f"✅ Aplicação {applications_sent} enviada com sucesso!", "SUCCESS")
                        
                        # Delay entre aplicações
                        delay_time = random.uniform(10, 20)
                        self.detailed_log(f"Aguardando {delay_time:.1f}s antes da próxima aplicação...")
                        time.sleep(delay_time)
                    else:
                        self.failed_applications.append(job_info)
                        self.detailed_log("❌ Falha ao enviar aplicação", "ERROR")
                        
                    # Volta para a lista de vagas
                    self.driver.back()
                    self.random_delay(2, 4)
                    
                # Tenta ir para próxima página
                if applications_sent < max_applications:
                    if self.go_to_next_page():
                        page_number += 1
                        self.random_delay(3, 5)
                    else:
                        self.detailed_log("Não há mais páginas disponíveis")
                        break
                        
            # Relatório final
            self.detailed_log("=== RELATÓRIO FINAL ===", "SUCCESS")
            self.detailed_log(f"Total de aplicações enviadas: {applications_sent}")
            self.detailed_log(f"Total de falhas: {len(self.failed_applications)}")
            
            for i, job in enumerate(self.applied_jobs, 1):
                self.detailed_log(f"{i}. ✅ {job.get('title', 'N/A')} - {job.get('company', 'N/A')}")
                
            return {
                "success": True,
                "applications_sent": applications_sent,
                "applied_jobs": self.applied_jobs,
                "failed_applications": self.failed_applications
            }
            
        except Exception as e:
            self.detailed_log(f"Erro geral na aplicação: {str(e)}", "ERROR")
            return {"success": False, "error": str(e)}
            
    def go_to_next_page(self):
        """Vai para a próxima página de resultados"""
        try:
            next_selectors = [
                "button[aria-label*='Next']",
                ".artdeco-pagination__button--next",
                "button:contains('Next')",
                ".jobs-search-pagination__button--next"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        next_button.click()
                        return True
                except:
                    continue
                    
            return False
            
        except:
            return False

