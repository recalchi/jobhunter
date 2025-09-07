import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.automation.base_automation import BaseAutomation

class LinkedInAutomation(BaseAutomation):
    def __init__(self, headless=True):
        super().__init__(headless)
        self.base_url = "https://www.linkedin.com"
        self.jobs_url = "https://www.linkedin.com/jobs/search/"
        
    def login(self, username, password):
        """Faz login no LinkedIn"""
        try:
            self.logger.info("Iniciando login no LinkedIn...")
            self.driver.get(f"{self.base_url}/login")
            
            # Preenche email
            if not self.wait_and_send_keys(By.ID, "username", username):
                return False
                
            # Preenche senha
            if not self.wait_and_send_keys(By.ID, "password", password):
                return False
                
            # Clica no botão de login
            if not self.wait_and_click(By.XPATH, "//button[@type='submit']"):
                return False
                
            self.safe_sleep(3)
            
            # Verifica se o login foi bem-sucedido
            if "feed" in self.driver.current_url or "jobs" in self.driver.current_url:
                self.logger.info("Login realizado com sucesso!")
                return True
            else:
                self.logger.error("Falha no login - verificar credenciais")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro durante o login: {str(e)}")
            return False
            
    def search_jobs(self, job_types, location="São Paulo", salary_min=1900):
        """Busca vagas no LinkedIn"""
        jobs_found = []
        
        try:
            for job_type in job_types:
                self.logger.info(f"Buscando vagas para: {job_type}")
                
                # Monta a URL de busca
                search_params = {
                    'keywords': job_type,
                    'location': location,
                    'f_SB2': str(salary_min),
                    'f_TPR': 'r86400',
                    'f_E': '2',
                    'f_LF': 'f_AL'
                }
                self.driver.get(self.jobs_url)
                self.safe_sleep(3)

                # Preenche o campo de busca de vagas
                if not self.wait_and_send_keys(By.XPATH, "//input[contains(@id, 'jobs-search-box-keyword-id') or contains(@aria-label, 'Search by title') ]", job_type.replace("'", "")):
                    self.logger.error("Não foi possível encontrar o campo de busca de vagas.")
                    continue

                # Preenche o campo de localização
                if not self.wait_and_send_keys(By.XPATH, "//input[contains(@id, 'jobs-search-box-location-id') or contains(@aria-label, 'Search by location') ]", location):
                    self.logger.error("Não foi possível encontrar o campo de busca de localização.")
                    continue

                # Clica no botão de busca
                if not self.wait_and_click(By.XPATH, "//button[contains(@class, 'jobs-search-box__submit-button') or @type='submit']"):
                    self.logger.error("Não foi possível clicar no botão de busca.")
                    continue

                self.safe_sleep(3)

                # Clica no botão 'Todos os filtros'
                if not self.wait_and_click(By.XPATH, "//button[contains(text(), 'Todos os filtros')]"):
                    self.logger.error("Não foi possível clicar no botão 'Todos os filtros'.")
                    continue

                self.safe_sleep(2)

                # Ativa o filtro 'Candidatura simplificada'
                if not self.wait_and_click(By.XPATH, "//label[contains(text(), 'Candidatura simplificada')]"):
                    self.logger.error("Não foi possível ativar o filtro 'Candidatura simplificada'.")
                    continue

                self.safe_sleep(2)

                # Clica no botão 'Exibir resultados'
                if not self.wait_and_click(By.XPATH, "//button[contains(text(), 'Exibir resultados')]"):
                    self.logger.error("Não foi possível clicar no botão 'Exibir resultados'.")
                    continue

                self.safe_sleep(3)

                
                # Busca as vagas na página
                page_jobs = self._extract_jobs_from_page()
                jobs_found.extend(page_jobs)
                
                # Navega pelas próximas páginas (máximo 3 páginas)
                for page in range(2, 4):
                    if self._go_to_next_page():
                        self.safe_sleep(3)
                        page_jobs = self._extract_jobs_from_page()
                        jobs_found.extend(page_jobs)
                    else:
                        break
                        
        except Exception as e:
            self.logger.error(f"Erro durante a busca de vagas: {str(e)}")
            
        return jobs_found
        
    def _extract_jobs_from_page(self):
        """Extrai informações das vagas da página atual"""
        jobs = []
        
        try:
            # Aguarda os elementos de vaga carregarem
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-search-card")
            
            for card in job_cards:
                try:
                    # Extrai informações básicas
                    title_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__title")
                    company_element = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle")
                    location_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                    link_element = card.find_element(By.CSS_SELECTOR, "a")
                    
                    job_data = {
                        'title': title_element.text.strip(),
                        'company': company_element.text.strip(),
                        'location': location_element.text.strip(),
                        'url': link_element.get_attribute('href'),
                        'platform': 'LinkedIn',
                        'job_id': self._extract_job_id_from_url(link_element.get_attribute('href'))
                    }
                    
                    # Tenta extrair informações adicionais
                    try:
                        salary_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__salary-info")
                        job_data['salary_range'] = salary_element.text.strip()
                    except NoSuchElementException:
                        job_data['salary_range'] = None
                        
                    jobs.append(job_data)
                    
                except Exception as e:
                    self.logger.warning(f"Erro ao extrair dados de uma vaga: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Erro ao extrair vagas da página: {str(e)}")
            
        return jobs
        
    def _extract_job_id_from_url(self, url):
        """Extrai o ID da vaga da URL"""
        try:
            # LinkedIn job URLs geralmente têm o formato: .../jobs/view/123456789/
            parts = url.split('/')
            for i, part in enumerate(parts):
                if part == 'view' and i + 1 < len(parts):
                    return parts[i + 1]
            return url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        except:
            return url
            
    def _go_to_next_page(self):
        """Navega para a próxima página de resultados"""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='next']")
            if next_button.is_enabled():
                next_button.click()
                return True
            return False
        except NoSuchElementException:
            return False
            
    def apply_to_job(self, job_url, resume_path=None):
        """Aplica para uma vaga específica"""
        try:
            self.logger.info(f"Aplicando para vaga: {job_url}")
            self.driver.get(job_url)
            self.safe_sleep(3)
            
            # Procura pelo botão "Easy Apply"
            easy_apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'jobs-apply-button') and contains(text(), 'Easy Apply')]")
            
            if not easy_apply_buttons:
                # Tenta outros seletores para o botão de aplicação
                easy_apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Candidatar-se')]")
                
            if easy_apply_buttons:
                easy_apply_buttons[0].click()
                self.safe_sleep(2)
                
                # Verifica se apareceu um modal de aplicação
                return self._handle_application_modal(resume_path)
            else:
                self.logger.warning("Botão Easy Apply não encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao aplicar para vaga: {str(e)}")
            return False
            
    def _handle_application_modal(self, resume_path=None):
        """Lida com o modal de aplicação de múltiplas etapas."""
        try:
            # Loop para lidar com as etapas do modal
            for _ in range(5): # Limite de 5 etapas para evitar loops infinitos
                # Pular seleção de currículo
                next_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Avançar') or contains(text(), 'Next')]")
                if next_button:
                    next_button.click()
                    self.safe_sleep(2)

                # Responder perguntas de sim/não
                yes_buttons = self.driver.find_elements(By.XPATH, "//input[@type='radio' and contains(@id, 'yes')]")
                for button in yes_buttons:
                    try:
                        button.click()
                    except Exception as e:
                        self.logger.warning(f"Não foi possível clicar no botão 'sim': {e}")

                # Responder perguntas descritivas (ex: salário)
                salary_inputs = self.driver.find_elements(By.XPATH, "//input[contains(@id, 'currency')]")
                for input_field in salary_inputs:
                    try:
                        input_field.send_keys('1900') # Valor padrão
                    except Exception as e:
                        self.logger.warning(f"Não foi possível preencher o campo de salário: {e}")

                # Clicar em 'Revisar' ou 'Enviar'
                review_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Revisar') or contains(text(), 'Review')]")
                if review_button:
                    review_button.click()
                    self.safe_sleep(2)

                submit_button = self.wait_for_element(By.XPATH, "//button[contains(text(), 'Enviar inscrição') or contains(text(), 'Submit application')]")
                if submit_button:
                    submit_button.click()
                    self.safe_sleep(3)
                    self.logger.info("Aplicação enviada com sucesso!")
                    return True

            self.logger.warning("Não foi possível concluir a aplicação após 5 etapas.")
            return False

        except Exception as e:
            self.logger.error(f"Erro no modal de aplicação: {str(e)}")
            return False

