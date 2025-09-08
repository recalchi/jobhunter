import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
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

            if not self.wait_and_send_keys(By.ID, "username", username):
                return False

            if not self.wait_and_send_keys(By.ID, "password", password):
                return False

            if not self.wait_and_click(By.XPATH, "//button[@type='submit']"):
                return False

            self.safe_sleep(3)

            if "feed" in self.driver.current_url or "jobs" in self.driver.current_url:
                self.logger.info("✅ Login realizado com sucesso!")
                return True
            else:
                self.logger.error("❌ Falha no login - verificar credenciais")
                return False

        except Exception as e:
            self.logger.error(f"Erro durante o login: {str(e)}")
            return False

    def search_jobs(self, job_types, location="São Paulo", salary_min=1900, max_apply=3):
        """Busca vagas no LinkedIn e tenta aplicar automaticamente"""
        jobs_found = []

        try:
            for job_type in job_types:
                self.logger.info(f"🔎 Buscando vagas para: {job_type}")

                search_params = {
                    'keywords': job_type,
                    'location': location,
                    'f_SB2': str(salary_min),  # Salário mínimo
                    'f_TPR': 'r86400',  # Últimas 24 horas
                    'f_E': '2'  # Nível de experiência
                }

                params_str = '&'.join([f"{k}={v}" for k, v in search_params.items()])
                search_url = f"{self.jobs_url}?{params_str}"

                self.driver.get(search_url)

                try:
                    self.logger.info("⏳ Aguardando carregamento da página de vagas...")
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".job-search-card"))
                    )
                except TimeoutException:
                    self.logger.warning("⚠️ Timeout ao carregar vagas, tentando novamente...")
                    self.driver.get(search_url)
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".job-search-card"))
                    )

                self.safe_sleep(3)

                # Filtros de localidade e candidatura simplificada
                try:
                    self.logger.info("🎯 Aplicando filtros...")

                    location_input = self.wait_for_element(By.XPATH, "//input[contains(@aria-label, 'Localidade')]", timeout=10)
                    if location_input:
                        location_input.clear()
                        location_input.send_keys(location)
                        self.safe_sleep(2)
                        location_input.send_keys(u'\ue007')  # ENTER
                        self.logger.info(f"📍 Localidade aplicada: {location}")

                    try:
                        self.wait_and_click(By.XPATH, "//button[contains(text(), 'Todos os filtros')]", timeout=10)
                        self.safe_sleep(2)

                        easy_apply_toggle = self.wait_for_element(By.XPATH, "//span[text()='Candidatura simplificada']/ancestor::li//button", timeout=10)
                        if easy_apply_toggle and easy_apply_toggle.get_attribute("aria-checked") == "false":
                            easy_apply_toggle.click()
                            self.logger.info("✅ Filtro 'Candidatura simplificada' ativado.")

                        self.wait_and_click(By.XPATH, "//button[contains(text(), 'Exibir resultados')]", timeout=10)
                        self.safe_sleep(5)
                    except TimeoutException:
                        self.logger.warning("⚠️ Botão 'Todos os filtros' não encontrado. Usando URL direta com f_AL=true")
                        search_url += "&f_AL=true"
                        self.driver.get(search_url)
                        self.safe_sleep(3)

                except Exception as ex:
                    self.logger.error(f"Erro ao aplicar filtros: {str(ex)}")

                # Extração de vagas
                page_jobs = self._extract_jobs_from_page()
                jobs_found.extend(page_jobs)

                for page in range(2, 4):
                    if self._go_to_next_page():
                        self.safe_sleep(3)
                        page_jobs = self._extract_jobs_from_page()
                        jobs_found.extend(page_jobs)
                    else:
                        break

                # Aplicação automática em N vagas
                self.logger.info(f"🤖 Iniciando auto-aplicação em até {max_apply} vagas...")
                for job in jobs_found[:max_apply]:
                    try:
                        self.logger.info(f"👉 Tentando aplicar em: {job['title']} - {job['company']}")
                        sucesso = self.apply_to_job(job['url'])
                        if sucesso:
                            self.logger.info(f"✅ Aplicação concluída para {job['title']} ({job['company']})")
                        else:
                            self.logger.warning(f"❌ Falhou aplicação em {job['title']} ({job['company']})")
                    except Exception as e:
                        self.logger.error(f"Erro ao aplicar para {job['url']}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Erro durante a busca de vagas: {str(e)}")

        return jobs_found

    def _extract_jobs_from_page(self):
        """Extrai informações das vagas da página atual"""
        jobs = []
        try:
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-search-card")

            for card in job_cards:
                try:
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
        try:
            parts = url.split('/')
            for i, part in enumerate(parts):
                if part == 'view' and i + 1 < len(parts):
                    return parts[i + 1]
            return url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
        except:
            return url

    def _go_to_next_page(self):
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, "button[aria-label*='next']")
            if next_button.is_enabled():
                next_button.click()
                return True
            return False
        except NoSuchElementException:
            return False

    def apply_to_job(self, job_url, resume_path=None):
        try:
            self.logger.info(f"Aplicando para vaga: {job_url}")
            self.driver.get(job_url)
            self.safe_sleep(3)

            easy_apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'jobs-apply-button') and contains(text(), 'Easy Apply')]")
            if not easy_apply_buttons:
                easy_apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Candidatar-se')]")

            if easy_apply_buttons:
                easy_apply_buttons[0].click()
                self.safe_sleep(2)
                return self._handle_application_modal(resume_path)
            else:
                self.logger.warning("Botão Easy Apply não encontrado")
                return False

        except Exception as e:
            self.logger.error(f"Erro ao aplicar para vaga: {str(e)}")
            return False

    def _handle_application_modal(self, resume_path=None):
        try:
            self.safe_sleep(2)

            if not self.wait_and_click(By.XPATH, "//button[contains(text(), 'Avançar')]"):
                self.logger.warning("Botão 'Avançar' não encontrado, seguindo...")

            while True:
                selects = self.driver.find_elements(By.CSS_SELECTOR, "select")
                for select in selects:
                    try:
                        select.click()
                        self.safe_sleep(1)
                        option_to_select = select.find_element(By.XPATH, ".//option[contains(text(), 'Sim') or contains(text(), 'Yes')]")
                        option_to_select.click()
                        self.safe_sleep(1)
                    except NoSuchElementException:
                        continue

                text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                for text_input in text_inputs:
                    try:
                        text_input.send_keys("1900")
                        self.safe_sleep(1)
                    except Exception as e:
                        self.logger.warning(f"Não foi possível preencher campo: {e}")
                        continue

                if self.wait_and_click(By.XPATH, "//button[contains(text(), 'Revisar')]"):
                    self.logger.info("Indo para a tela de revisão.")
                    self.safe_sleep(2)
                    break
                else:
                    break

            if self.wait_and_click(By.XPATH, "//button[contains(text(), 'Enviar candidatura')]"):
                self.logger.info("✅ Candidatura enviada com sucesso!")
                self.safe_sleep(3)
                self.wait_and_click(By.XPATH, "//button[contains(text(), 'Concluído')]")
                return True
            else:
                self.logger.error("❌ Não foi possível enviar a candidatura.")
                return False

        except Exception as e:
            self.logger.error(f"Erro no modal de aplicação: {str(e)}")
            return False
