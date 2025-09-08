'''
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys # Importar Keys
from src.automation.base_automation import BaseAutomation
import urllib.parse
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
                
                # Remove aspas do job_type
                clean_job_type = job_type.replace("'", "").replace(""", "")

                # Constrói a URL de busca diretamente
                encoded_job_type = urllib.parse.quote_plus(clean_job_type)
                encoded_location = urllib.parse.quote_plus(location)
                search_url = f"{self.jobs_url}?keywords={encoded_job_type}&location={encoded_location}"
                
                self.logger.info(f"Navegando diretamente para a URL de busca: {search_url}")
                self.driver.get(search_url)
                self.safe_sleep(5) # Aumenta o tempo de espera para o carregamento da página
                self.logger.info("Página de busca carregada.")

                # Tenta clicar no botão 'Todos os filtros'
                all_filters_clicked = False
                filter_selectors = [
                    (By.XPATH, "//button[contains(text(), 'Todos os filtros')]", "Botão 'Todos os filtros' por texto (PT)"),
                    (By.XPATH, "//button[contains(text(), 'All filters')]", "Botão 'All filters' por texto (EN)"),
                    (By.XPATH, "//button[contains(@aria-label, 'filtros')]", "Botão de filtros por aria-label"),
                    (By.CSS_SELECTOR, "button.search-reusables__all-filters-pill-button", "Botão de filtros por classe"),
                    (By.CSS_SELECTOR, "button[data-test-all-filters-button]", "Botão de filtros por data-test")
                ]
                
                for by_type, selector, description in filter_selectors:
                    try:
                        self.logger.info(f"Tentando clicar em 'Todos os filtros': {description} ({selector})")
                        filter_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((by_type, selector))
                        )
                        if filter_button:
                            filter_button.click()
                            self.safe_sleep(2)
                            all_filters_clicked = True
                            self.logger.info(f"Clicou em 'Todos os filtros' usando: {description}")
                            break
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                        self.logger.warning(f"Erro ao clicar no filtro {description}: {e}")
                        continue

                if not all_filters_clicked:
                    self.logger.error("Não foi possível clicar no botão 'Todos os filtros' após todas as tentativas.")
                    continue

                # Ativa o filtro 'Candidatura simplificada'
                easy_apply_activated = False
                easy_apply_selectors = [
                    (By.XPATH, "//label[contains(text(), 'Candidatura simplificada')]", "Label 'Candidatura simplificada' (PT)"),
                    (By.XPATH, "//label[contains(text(), 'Easy Apply')]", "Label 'Easy Apply' (EN)"),
                    (By.ID, "f_LF-f_AL", "Checkbox 'Candidatura simplificada' por ID"),
                    (By.XPATH, "//span[contains(text(), 'Candidatura simplificada')]/preceding-sibling::input", "Checkbox 'Candidatura simplificada' por span (PT)"),
                    (By.XPATH, "//span[contains(text(), 'Easy Apply')]/preceding-sibling::input", "Checkbox 'Easy Apply' por span (EN)"),
                    (By.XPATH, "//input[@type='checkbox' and @id='f_LF-f_AL']", "Checkbox 'Candidatura simplificada' por tipo e ID"),
                    (By.XPATH, "//input[@type='checkbox' and contains(@aria-label, 'Candidatura simplificada')]", "Checkbox 'Candidatura simplificada' por tipo e aria-label")
                ]
                
                for by_type, selector, description in easy_apply_selectors:
                    try:
                        self.logger.info(f"Tentando ativar filtro 'Candidatura simplificada': {description} ({selector})")
                        easy_apply_element = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((by_type, selector))
                        )
                        if easy_apply_element:
                            if easy_apply_element.tag_name == 'input' and easy_apply_element.get_attribute('type') == 'checkbox':
                                if not easy_apply_element.is_selected():
                                    easy_apply_element.click()
                            else:
                                easy_apply_element.click()
                            self.safe_sleep(1)
                            easy_apply_activated = True
                            self.logger.info(f"Ativou filtro 'Candidatura simplificada' usando: {description}")
                            break
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                        self.logger.warning(f"Erro ao ativar candidatura simplificada com {description}: {e}")
                        continue

                if not easy_apply_activated:
                    self.logger.error("Não foi possível ativar o filtro 'Candidatura simplificada' após todas as tentativas.")
                    continue

                # Clica no botão 'Exibir resultados'
                results_shown = False
                show_results_selectors = [
                    (By.XPATH, "//button[contains(text(), 'Exibir resultados')]", "Botão 'Exibir resultados' por texto (PT)"),
                    (By.XPATH, "//button[contains(text(), 'Show results')]", "Botão 'Show results' por texto (EN)"),
                    (By.XPATH, "//button[contains(text(), 'Mostrar resultados')]", "Botão 'Mostrar resultados' por texto (PT)"),
                    (By.CSS_SELECTOR, "button.search-reusables__secondary-filters-show-results-button", "Botão 'Exibir resultados' por classe"),
                    (By.CSS_SELECTOR, "button[data-test-show-results-button]", "Botão 'Exibir resultados' por data-test")
                ]
                
                for by_type, selector, description in show_results_selectors:
                    try:
                        self.logger.info(f"Tentando clicar em 'Exibir resultados': {description} ({selector})")
                        show_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((by_type, selector))
                        )
                        if show_button:
                            show_button.click()
                            self.safe_sleep(3)
                            results_shown = True
                            self.logger.info(f"Clicou em 'Exibir resultados' usando: {description}")
                            break
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                        self.logger.warning(f"Erro ao exibir resultados com {description}: {e}")
                        continue

                if not results_shown:
                    self.logger.error("Não foi possível clicar no botão 'Exibir resultados' após todas as tentativas.")
                    continue

                # Aguarda os resultados carregarem
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
            self.safe_sleep(2)
            
            # Múltiplos seletores para cards de vaga
            job_card_selectors = [
                ".job-search-card",
                ".jobs-search-results__list-item",
                "[data-entity-urn*='job']",
                ".scaffold-layout__list-item"
            ]
            
            job_cards = []
            for selector in job_card_selectors:
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if job_cards:
                    self.logger.info(f"Encontrou {len(job_cards)} vagas usando seletor: {selector}")
                    break
            
            if not job_cards:
                self.logger.warning("Nenhum card de vaga encontrado")
                return jobs
            
            for card in job_cards:
                try:
                    # Múltiplos seletores para título
                    title_selectors = [
                        ".base-search-card__title",
                        ".job-card-list__title",
                        "h3 a",
                        ".job-card-container__link"
                    ]
                    
                    title_element = None
                    for selector in title_selectors:
                        try:
                            title_element = card.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                            continue
                    
                    if not title_element:
                        continue
                    
                    # Múltiplos seletores para empresa
                    company_selectors = [
                        ".base-search-card__subtitle",
                        ".job-card-container__company-name",
                        ".job-card-list__company-name",
                        "h4 a"
                    ]
                    
                    company_element = None
                    for selector in company_selectors:
                        try:
                            company_element = card.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                            continue
                    
                    # Múltiplos seletores para localização
                    location_selectors = [
                        ".job-search-card__location",
                        ".job-card-container__metadata-item",
                        ".job-card-list__location"
                    ]
                    
                    location_element = None
                    for selector in location_selectors:
                        try:
                            location_element = card.find_element(By.CSS_SELECTOR, selector)
                            break
                        except NoSuchElementException:
                            continue
                    
                    # Múltiplos seletores para link
                    link_selectors = [
                        "a",
                        ".job-card-container__link",
                        ".base-card__full-link"
                    ]
                    
                    link_element = None
                    for selector in link_selectors:
                        try:
                            link_element = card.find_element(By.CSS_SELECTOR, selector)
                            if link_element.get_attribute('href'):
                                break
                        except NoSuchElementException:
                            continue
                    
                    if title_element and link_element:
                        job_data = {
                            'title': title_element.text.strip(),
                            'company': company_element.text.strip() if company_element else 'N/A',
                            'location': location_element.text.strip() if location_element else 'N/A',
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
                        self.logger.info(f"Vaga extraída: {job_data['title']} - {job_data['company']}
")
                    
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
            # Múltiplos seletores para botão próxima página
            next_selectors = [
                "button[aria-label*='next']",
                "button[aria-label*='próxima']",
                ".artdeco-pagination__button--next",
                "button[data-test-pagination-page-btn='next']"
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        next_button.click()
                        return True
                except NoSuchElementException:
                    continue
            return False
        except Exception as e:
            self.logger.error(f"Erro ao navegar para próxima página: {e}")
            return False
            
    def apply_to_job(self, job_url, resume_path=None):
        """Aplica para uma vaga específica"""
        try:
            self.logger.info(f"Aplicando para vaga: {job_url}")
            self.driver.get(job_url)
            self.safe_sleep(3)
            
            # Múltiplos seletores para botão Easy Apply
            easy_apply_selectors = [
                (By.XPATH, "//button[contains(@class, 'jobs-apply-button') and contains(text(), 'Easy Apply')]", "Botão 'Easy Apply' por texto (EN)"),
                (By.XPATH, "//button[contains(text(), 'Candidatar-se')]", "Botão 'Candidatar-se' por texto (PT)"),
                (By.XPATH, "//button[contains(text(), 'Candidatura simplificada')]", "Botão 'Candidatura simplificada' por texto (PT)"),
                (By.CSS_SELECTOR, "button.jobs-s-apply.jobs-s-apply--fadein", "Botão 'Candidatura simplificada' por classe"),
                (By.XPATH, "//button[contains(@aria-label, 'Easy Apply')]", "Botão 'Easy Apply' por aria-label")
            ]
            
            easy_apply_button = None
            for by_type, selector, description in easy_apply_selectors:
                try:
                    self.logger.info(f"Tentando encontrar botão Easy Apply: {description} ({selector})")
                    easy_apply_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((by_type, selector))
                    )
                    if easy_apply_button:
                        self.logger.info(f"Botão Easy Apply encontrado usando: {description}")
                        break
                except (TimeoutException, NoSuchElementException) as e:
                    self.logger.warning(f"Não foi possível encontrar o botão Easy Apply ({description}): {e}")
                    continue
                
            if easy_apply_button:
                easy_apply_button.click()
                self.safe_sleep(2)
                
                # Verifica se apareceu um modal de aplicação
                return self._handle_application_modal(resume_path)
            else:
                self.logger.warning("Botão Easy Apply não encontrado após todas as tentativas.")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao aplicar para vaga: {str(e)}")
            return False
            
    def _handle_application_modal(self, resume_path=None):
        """Lida com o modal de aplicação de múltiplas etapas."""
        try:
            max_steps = 10  # Aumentado para lidar com mais etapas
            
            for step in range(max_steps):
                self.logger.info(f"Processando etapa {step + 1} do modal de aplicação")
                self.safe_sleep(2)
                
                # Verifica se a aplicação foi concluída
                success_indicators = [
                    (By.XPATH, "//h3[contains(text(), 'Sua inscrição foi enviada')]", "Indicador de sucesso por h3 (PT)"),
                    (By.XPATH, "//h3[contains(text(), 'Application sent')]", "Indicador de sucesso por h3 (EN)"),
                    (By.XPATH, "//div[contains(text(), 'Sua candidatura foi enviada')]", "Indicador de sucesso por div (PT)"),
                    (By.CSS_SELECTOR, "div.jobs-apply-success", "Indicador de sucesso por classe")
                ]
                
                for by_type, selector, description in success_indicators:
                    try:
                        if WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((by_type, selector))):
                            self.logger.info(f"Aplicação enviada com sucesso! ({description})")
                            return True
                    except TimeoutException:
                        continue
                
                # Responder perguntas de sim/não (sempre sim)
                yes_buttons = self.driver.find_elements(By.XPATH, "//input[@type='radio' and (contains(@value, 'Yes') or contains(@value, 'Sim') or contains(@id, 'yes'))]")
                for button in yes_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled() and not button.is_selected():
                            button.click()
                            self.safe_sleep(0.5)
                    except Exception as e:
                        self.logger.warning(f"Não foi possível clicar no botão 'sim': {e}")

                # Preencher campos de salário
                salary_selectors = [
                    (By.XPATH, "//input[contains(@id, 'currency') or contains(@id, 'salary') or contains(@placeholder, 'salário')]", "Campo de salário por ID/placeholder (PT)"),
                    (By.XPATH, "//input[@type='number']", "Campo de salário por tipo number"),
                    (By.XPATH, "//input[contains(@aria-label, 'salary')]", "Campo de salário por aria-label")
                ]
                
                for by_type, selector, description in salary_selectors:
                    salary_inputs = self.driver.find_elements(by_type, selector)
                    for input_field in salary_inputs:
                        try:
                            if input_field.is_displayed() and input_field.is_enabled() and not input_field.get_attribute('value'):
                                input_field.clear()
                                input_field.send_keys('1900')
                                self.safe_sleep(0.5)
                        except Exception as e:
                            self.logger.warning(f"Não foi possível preencher o campo de salário ({description}): {e}")

                # Preencher campos de texto obrigatórios
                text_inputs = self.driver.find_elements(By.XPATH, "//input[@type='text' and @required]")
                for input_field in text_inputs:
                    try:
                        if input_field.is_displayed() and input_field.is_enabled() and not input_field.get_attribute('value'):
                            input_field.send_keys("Sim")
                            self.safe_sleep(0.5)
                    except Exception as e:
                        self.logger.warning(f"Erro ao preencher campo de texto: {e}")

                # Procurar botões de ação (em ordem de prioridade)
                action_buttons = [
                    (By.XPATH, "//button[contains(text(), 'Enviar inscrição') or contains(text(), 'Submit application')]", "Botão 'Enviar inscrição' (PT/EN)"),
                    (By.XPATH, "//button[contains(text(), 'Revisar') or contains(text(), 'Review')]", "Botão 'Revisar' (PT/EN)"),
                    (By.XPATH, "//button[contains(text(), 'Avançar') or contains(text(), 'Next')]", "Botão 'Avançar' (PT/EN)"),
                    (By.XPATH, "//button[contains(text(), 'Continuar') or contains(text(), 'Continue')]", "Botão 'Continuar' (PT/EN)")
                ]
                
                button_clicked = False
                for by_type, selector, description in action_buttons:
                    try:
                        button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((by_type, selector))
                        )
                        if button:
                            button.click()
                            self.logger.info(f"Clicou no botão: {description}")
                            self.safe_sleep(2)
                            button_clicked = True
                            break
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                        self.logger.warning(f"Erro ao clicar no botão {description}: {e}")
                
                if not button_clicked:
                    self.logger.warning(f"Nenhum botão de ação encontrado na etapa {step + 1} após todas as tentativas.")
                    break

            self.logger.warning(f"Não foi possível concluir a aplicação após {max_steps} etapas.")
            return False

        except Exception as e:
            self.logger.error(f"Erro no modal de aplicação: {str(e)}")
            return False
'''

