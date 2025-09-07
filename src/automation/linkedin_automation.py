import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
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
            if not self.wait_and_click(By.XPATH, "//button[@type=\'submit\']"):
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
                
                # Navega para a página de busca de vagas
                self.driver.get(self.jobs_url)
                self.safe_sleep(3)

                # Remove aspas do job_type
                clean_job_type = job_type.replace("'", "").replace('"', "")

                # Preenche o campo de busca de vagas
                search_field_selectors = [
                    "//input[contains(@id, \'jobs-search-box-keyword-id\')]",
                    "//input[contains(@aria-label, \'Search by title\')]",
                    "//input[contains(@placeholder, \'Pesquisar por título, palavra-chave ou empresa\')]",
                    "//input[contains(@placeholder, \'Pesquisar\')]"
                ]
                search_field = None
                for selector in search_field_selectors:
                    try:
                        search_field = self.wait_for_element(By.XPATH, selector, timeout=5)
                        if search_field:
                            search_field.clear()
                            search_field.send_keys(clean_job_type)
                            self.safe_sleep(1)
                            break
                    except (TimeoutException, NoSuchElementException):
                        continue
                
                if not search_field:
                    self.logger.error("Não foi possível encontrar o campo de busca de vagas.")
                    continue

                # Preenche o campo de localização
                location_field_selectors = [
                    "//input[contains(@id, \'jobs-search-box-location-id\')]",
                    "//input[contains(@aria-label, \'Search by location\')]",
                    "//input[contains(@placeholder, \'Localização\')]"
                ]
                location_field = None
                for selector in location_field_selectors:
                    try:
                        location_field = self.wait_for_element(By.XPATH, selector, timeout=5)
                        if location_field:
                            location_field.clear()
                            location_field.send_keys(location)
                            self.safe_sleep(1)
                            break
                    except (TimeoutException, NoSuchElementException):
                        continue

                if not location_field:
                    self.logger.error("Não foi possível encontrar o campo de busca de localização.")
                    continue

                # Clica no botão de busca
                search_button_selectors = [
                    "//button[contains(@class, \'jobs-search-box__submit-button\')]",
                    "//button[@type=\'submit\']",
                    "//button[contains(@aria-label, \'Pesquisar\')]"
                ]
                search_button = None
                for selector in search_button_selectors:
                    try:
                        search_button = self.wait_for_element(By.XPATH, selector, timeout=5)
                        if search_button:
                            search_button.click()
                            self.safe_sleep(3)
                            break
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
                        continue

                if not search_button:
                    self.logger.error("Não foi possível clicar no botão de busca.")
                    continue

                # Aguarda a página carregar
                self.safe_sleep(3)

                # Tenta clicar no botão \'Todos os filtros\' com múltiplos seletores
                all_filters_clicked = False
                filter_selectors = [
                    "//button[contains(text(), \'Todos os filtros\')]",
                    "//button[contains(text(), \'All filters\')]",
                    "//button[contains(@aria-label, \'filtros\')]",
                    "//button[contains(@class, \'search-reusables__all-filters-pill-button\')]"
                ]
                
                for selector in filter_selectors:
                    try:
                        filter_button = self.wait_for_element(By.XPATH, selector, timeout=5)
                        if filter_button:
                            filter_button.click()
                            self.safe_sleep(2)
                            all_filters_clicked = True
                            self.logger.info("Clicou em \'Todos os filtros\'")
                            break
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                        self.logger.warning(f"Erro ao clicar no filtro {selector}: {e}")
                        continue

                if not all_filters_clicked:
                    self.logger.error("Não foi possível clicar no botão \'Todos os filtros\'.")
                    continue

                # Ativa o filtro \'Candidatura simplificada\'
                easy_apply_activated = False
                easy_apply_selectors = [
                    "//label[contains(text(), \'Candidatura simplificada\')]",
                    "//label[contains(text(), \'Easy Apply\')]",
                    "//input[@id=\'f_LF-f_AL\']",
                    "//span[contains(text(), \'Candidatura simplificada\')]/preceding-sibling::input",
                    "//span[contains(text(), \'Easy Apply\')]/preceding-sibling::input",
                    "//input[@type=\'checkbox\' and @id=\'f_LF-f_AL\']", # Adicionado seletor mais específico
                    "//input[@type=\'checkbox\' and contains(@aria-label, \'Candidatura simplificada\')]"
                ]
                
                for selector in easy_apply_selectors:
                    try:
                        easy_apply_element = self.wait_for_element(By.XPATH, selector, timeout=5)
                        if easy_apply_element:
                            if easy_apply_element.tag_name == \'input\' and easy_apply_element.get_attribute(\'type\') == \'checkbox\':
                                if not easy_apply_element.is_selected():
                                    easy_apply_element.click()
                            else:
                                easy_apply_element.click()
                            self.safe_sleep(1)
                            easy_apply_activated = True
                            self.logger.info("Ativou filtro \'Candidatura simplificada\'")
                            break
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                        self.logger.warning(f"Erro ao ativar candidatura simplificada com seletor {selector}: {e}")
                        continue

                if not easy_apply_activated:
                    self.logger.error("Não foi possível ativar o filtro \'Candidatura simplificada\'.")
                    continue

                # Clica no botão \'Exibir resultados\'
                results_shown = False
                show_results_selectors = [
                    "//button[contains(text(), \'Exibir resultados\')]",
                    "//button[contains(text(), \'Show results\')]",
                    "//button[contains(text(), \'Mostrar resultados\')]",
                    "//button[contains(@class, \'search-reusables__secondary-filters-show-results-button\')]"
                ]
                
                for selector in show_results_selectors:
                    try:
                        show_button = self.wait_for_element(By.XPATH, selector, timeout=5)
                        if show_button:
                            show_button.click()
                            self.safe_sleep(3)
                            results_shown = True
                            self.logger.info("Clicou em \'Exibir resultados\'")
                            break
                    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException) as e:
                        self.logger.warning(f"Erro ao exibir resultados com seletor {selector}: {e}")
                        continue

                if not results_shown:
                    self.logger.error("Não foi possível clicar no botão \'Exibir resultados\'.")
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
                "[data-entity-urn*=\'job\']",
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
                            if link_element.get_attribute(\'href\'):
                                break
                        except NoSuchElementException:
                            continue
                    
                    if title_element and link_element:
                        job_data = {
                            \'title\': title_element.text.strip(),
                            \'company\': company_element.text.strip() if company_element else \'N/A\',
                            \'location\': location_element.text.strip() if location_element else \'N/A\',
                            \'url\': link_element.get_attribute(\'href\'),
                            \'platform\': \'LinkedIn\',
                            \'job_id\': self._extract_job_id_from_url(link_element.get_attribute(\'href\'))
                        }
                        
                        # Tenta extrair informações adicionais
                        try:
                            salary_element = card.find_element(By.CSS_SELECTOR, ".job-search-card__salary-info")
                            job_data[\'salary_range\'] = salary_element.text.strip()
                        except NoSuchElementException:
                            job_data[\'salary_range\'] = None
                            
                        jobs.append(job_data)
                        self.logger.info(f"Vaga extraída: {job_data[\'title\']} - {job_data[\'company\']}")
                    
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
            parts = url.split(\'/\')
            for i, part in enumerate(parts):
                if part == \'view\' and i + 1 < len(parts):
                    return parts[i + 1]
            return url.split(\'/\')[-2] if url.endswith(\'/\') else url.split(\'/\')[-1]
        except:
            return url
            
    def _go_to_next_page(self):
        """Navega para a próxima página de resultados"""
        try:
            # Múltiplos seletores para botão próxima página
            next_selectors = [
                "button[aria-label*=\'next\']",
                "button[aria-label*=\'próxima\']",
                ".artdeco-pagination__button--next",
                "button[data-test-pagination-page-btn=\'next\']"
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
                "//button[contains(@class, \'jobs-apply-button\') and contains(text(), \'Easy Apply\')]",
                "//button[contains(text(), \'Candidatar-se\')]",
                "//button[contains(text(), \'Candidatura simplificada\')]",
                "//button[contains(@class, \'jobs-s-apply\') and contains(@class, \'jobs-s-apply--fadein\')]",
                "//button[contains(@aria-label, \'Easy Apply\')]"
            ]
            
            easy_apply_button = None
            for selector in easy_apply_selectors:
                try:
                    easy_apply_button = self.wait_for_element(By.XPATH, selector, timeout=5)
                    if easy_apply_button:
                        break
                except:
                    continue
                
            if easy_apply_button:
                easy_apply_button.click()
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
            max_steps = 10  # Aumentado para lidar com mais etapas
            
            for step in range(max_steps):
                self.logger.info(f"Processando etapa {step + 1} do modal de aplicação")
                self.safe_sleep(2)
                
                # Verifica se a aplicação foi concluída
                success_indicators = [
                    "//h3[contains(text(), \'Sua inscrição foi enviada\')]",
                    "//h3[contains(text(), \'Application sent\')]",
                    "//div[contains(text(), \'Sua candidatura foi enviada\')]",
                    "//div[contains(@class, \'jobs-apply-success\')]"
                ]
                
                for indicator in success_indicators:
                    if self.wait_for_element(By.XPATH, indicator, timeout=2):
                        self.logger.info("Aplicação enviada com sucesso!")
                        return True
                
                # Responder perguntas de sim/não (sempre sim)
                yes_buttons = self.driver.find_elements(By.XPATH, "//input[@type=\'radio\' and (contains(@value, \'Yes\') or contains(@value, \'Sim\') or contains(@id, \'yes\'))]")
                for button in yes_buttons:
                    try:
                        if not button.is_selected():
                            button.click()
                            self.safe_sleep(0.5)
                    except Exception as e:
                        self.logger.warning(f"Não foi possível clicar no botão \'sim\': {e}")

                # Preencher campos de salário
                salary_selectors = [
                    "//input[contains(@id, \'currency\') or contains(@id, \'salary\') or contains(@placeholder, \'salário\')]",
                    "//input[@type=\'number\']",
                    "//input[contains(@aria-label, \'salary\')]"
                ]
                
                for selector in salary_selectors:
                    salary_inputs = self.driver.find_elements(By.XPATH, selector)
                    for input_field in salary_inputs:
                        try:
                            if not input_field.get_attribute(\'value\'):
                                input_field.clear()
                                input_field.send_keys(\'1900\')
                                self.safe_sleep(0.5)
                        except Exception as e:
                            self.logger.warning(f"Não foi possível preencher o campo de salário: {e}")

                # Preencher campos de texto obrigatórios
                text_inputs = self.driver.find_elements(By.XPATH, "//input[@type=\'text\' and @required]")
                for input_field in text_inputs:
                    try:
                        if not input_field.get_attribute(\'value\'):
                            input_field.send_keys("Sim")
                            self.safe_sleep(0.5)
                    except Exception as e:
                        self.logger.warning(f"Erro ao preencher campo de texto: {e}")

                # Procurar botões de ação (em ordem de prioridade)
                action_buttons = [
                    ("//button[contains(text(), \'Enviar inscrição\') or contains(text(), \'Submit application\')]", "Enviar"),
                    ("//button[contains(text(), \'Revisar\') or contains(text(), \'Review\')]", "Revisar"),
                    ("//button[contains(text(), \'Avançar\') or contains(text(), \'Next\')]", "Avançar"),
                    ("//button[contains(text(), \'Continuar\') or contains(text(), \'Continue\')]", "Continuar")
                ]
                
                button_clicked = False
                for button_xpath, button_name in action_buttons:
                    button = self.wait_for_element(By.XPATH, button_xpath, timeout=3)
                    if button and button.is_enabled():
                        try:
                            button.click()
                            self.logger.info(f"Clicou no botão: {button_name}")
                            self.safe_sleep(2)
                            button_clicked = True
                            break
                        except Exception as e:
                            self.logger.warning(f"Erro ao clicar no botão {button_name}: {e}")
                
                if not button_clicked:
                    self.logger.warning(f"Nenhum botão de ação encontrado na etapa {step + 1}")
                    break

            self.logger.warning(f"Não foi possível concluir a aplicação após {max_steps} etapas.")
            return False

        except Exception as e:
            self.logger.error(f"Erro no modal de aplicação: {str(e)}")
            return False


