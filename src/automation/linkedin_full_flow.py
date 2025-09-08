# src/automation/linkedin_full_flow.py
import os
import time
import json
import logging
from typing import List, Dict, Any, Optional
import random
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    ElementClickInterceptedException, ElementNotInteractableException,
    StaleElementReferenceException
)
import re

from src.automation.base_automation import BaseAutomation



# Log de import para sabermos QUAL arquivo está em uso em tempo de execução
_logger = logging.getLogger("LinkedInFullFlow")
if not _logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(name)s: %(message)s')
_logger.info(f"✅ Módulo LinkedInFullFlow carregado de: {__file__}")

class LinkedInFullFlow(BaseAutomation):
    """
    Fluxo completo de automação para LinkedIn:
      - login
      - navegar para Jobs
      - aplicar filtros/termos de busca
      - coletar vagas listadas
      - aplicar via 'Candidatura simplificada' quando existir

    Esta classe é compatível com as chamadas dos arquivos de rotas/automation.py:
      - start_full_automation(username, password, job_types, max_applications=..., session_id=...)
    Também oferece um alias:
      - run_full_automation(..., apply_limit=..., max_pages=...)  -> para retrocompatibilidade
    """

    BASE_URL = "https://www.linkedin.com"
    JOBS_SEARCH_URL = "https://www.linkedin.com/jobs/search/"

    def __init__(


        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        job_types: Optional[List[str]] = None,
        location: str = "São Paulo, SP",
        salary_min: int = 1900,
        max_applications: int = 3,
        headless: bool = False,
        timeout: int = 40
    ):
        super().__init__(headless=headless)   # ✅ inicializa driver + logger
        # garante que BaseAutomation.save_cookies/_load_cookies tenham caminho válido
        if not hasattr(self, "cookies_file") or not self.cookies_file:
            import os
            self.cookies_file = os.path.join(os.getcwd(), "linkedin_cookies.json")

        self.username = username
        self.password = password
        self.job_types = job_types or []
        self.location = location
        self.salary_min = salary_min
        self.max_applications = max_applications
        self.timeout = timeout

        # ✅ cria diretórios para screenshots e HTMLs de debug
        self._ensure_dirs()

        self.logger.info(f"🧭 LinkedInFullFlow inicializado | headless={headless} | timeout={timeout}s")

    def _human_type(self, element, text):
        """Digita texto caractere por caractere para simular humano"""
        import random, time
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # tempo aleatório por caractere
    # -------------------------- Helpers de infra --------------------------

    def _ensure_dirs(self):
        self.screens_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screens_dir, exist_ok=True)
        self.debug_dir = os.path.join(os.getcwd(), "debug_html")
        os.makedirs(self.debug_dir, exist_ok=True)

    def _snap(self, label: str) -> str:
        """Salva screenshot com prefixo padronizado e retorna o caminho relativo."""
        fname = f"linkedin_step_{int(time.time())}_{label}.png"
        fpath = os.path.join(self.screens_dir, fname)
        try:
            self.driver.save_screenshot(fpath)
            self.logger.info(f"📸 Screenshot salvo: {fname}")
        except Exception as e:
            self.logger.warning(f"Não foi possível salvar screenshot ({label}): {e}")
        return fpath

    def _dump_html(self, label: str) -> str:
        """Salva o HTML atual para debug detalhado."""
        fname = f"dump_{int(time.time())}_{label}.html"
        fpath = os.path.join(self.debug_dir, fname)
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            self.logger.info(f"🧾 HTML de debug salvo: {fname}")
        except Exception as e:
            self.logger.warning(f"Não foi possível salvar HTML ({label}): {e}")
        return fpath

    def _wait(self, by, value, timeout: Optional[int] = None):
        return WebDriverWait(self.driver, timeout or self.timeout).until(EC.presence_of_element_located((by, value)))

    # -------------------------- Passos principais --------------------------

    def login(self, username: str, password: str) -> bool:
        """Faz login no LinkedIn de forma humanizada (ou detecta se já está logado)."""
        try:
            self.logger.info("🔐 Iniciando login no LinkedIn...")

            # Se já está no feed ou em jobs, não precisa logar
            current_url = self.driver.current_url
            if "linkedin.com/feed" in current_url or "linkedin.com/jobs" in current_url:
                self.logger.info("✅ Já está logado no LinkedIn.")
                return True

            self.driver.get(f"{self.BASE_URL}/login")
            self._snap("01_login_page")

            # Campo senha
            password_el = self.wait_for_element(By.ID, "password", timeout=self.timeout)
            if password_el:
                self._human_type(password_el, password)
            else:
                self._dump_html("login_password_fail")
                return False

            # Pausa aleatória antes do submit
            self.safe_sleep(random.uniform(1.5, 3.0))

            # Botão de login
            if not self.wait_and_click(By.XPATH, "//button[@type='submit']"):
                self._dump_html("login_submit_fail")
                return False

            self.safe_sleep(random.uniform(2.0, 4.0))
            self._snap("02_after_login_submit")

            # Verificação de sucesso
            current = self.driver.current_url
            if "feed" in current or "jobs" in current:
                self.logger.info("✅ Login realizado com sucesso!")
                return True

            self.logger.warning(f"⚠️ Login não confirmou redirecionamento esperado. URL atual: {current}")
            self._dump_html("login_unknown_state")
            return False

        except Exception as e:
            self.logger.error(f"❌ Erro durante o login: {e}")
            self._snap("login_exception")
            self._dump_html("login_exception_html")
            return False

    def _check_for_security_challenge(self):
        """Detecta se caiu em reCAPTCHA ou tela de checkpoint."""
        current_url = self.driver.current_url
        page_source = self.driver.page_source.lower()

        if "checkpoint/challenge" in current_url:
            self.logger.warning("⚠️ LinkedIn pediu verificação de segurança/checkpoint.")
            return True

        if "recaptcha" in page_source or "i'm not a robot" in page_source:
            self.logger.warning("⚠️ reCAPTCHA detectado na página.")
            return True

        return False
    
    def _go_to_jobs_search_directly(self):
        """Vai direto para a página de busca de vagas."""
        try:
            self.logger.info("🧭 Indo direto para a página de busca de vagas...")
            self.driver.get(self.JOBS_SEARCH_URL)
            self._wait(By.CSS_SELECTOR, "input[aria-label*='Pesquisar cargos' i]")
            self.logger.info("✅ Página de busca de vagas carregada.")
            self._snap("08_direct_jobs_search_page")
        except TimeoutException:
            self.logger.error("⏳ Timeout ao carregar a página de busca de vagas.")
            self._snap("08A_jobs_search_timeout")
            self._dump_html("jobs_search_page_timeout")
            raise
    
    def go_to_jobs_page(self) -> bool:
        """Acessa diretamente a página de vagas recomendadas."""
        try:
            # Primeiro passo: /jobs
            jobs_url = f"{self.BASE_URL}/jobs/"
            self.logger.info(f"➡️ Acessando: {jobs_url}")
            self.driver.get(jobs_url)
            self.safe_sleep(2)
            self._snap("jobs_landing_page")

            # Segundo passo: /jobs/collections/recommended
            recommended_url = f"{self.BASE_URL}/jobs/collections/recommended/"
            self.logger.info(f"➡️ Redirecionando para: {recommended_url}")
            self.driver.get(recommended_url)
            self.safe_sleep(3)
            self._snap("jobs_recommended_page")

            current_url = self.driver.current_url
            if "linkedin.com/jobs/collections/recommended" in current_url:
                self.logger.info("✅ Página de vagas recomendadas acessada com sucesso.")
                return True
            else:
                self.logger.error(f"❌ Não conseguimos chegar na página de recomendadas. URL atual: {current_url}")
                return False

        except Exception as e:
            self.logger.error(f"❌ Erro ao acessar a página de vagas: {e}")
            return False

    def _apply_search_and_filters(
        self,
        keywords: str,
        location: Optional[str] = None,
        distance: int = 25,
        remote_only: bool = True,
        sort_by: str = "R"
    ) -> bool:
        """
        Aplica filtros de pesquisa de vagas no LinkedIn construindo a URL diretamente.
        Usa go_to_filtered_jobs para evitar falhas em seletores dinâmicos.
        """
        try:
            self.logger.info(f"🎛️ Aplicando busca e filtros | termo={keywords}, local={location or self.location}")

            # fallback se não foi passado `location`
            loc = location or self.location

            ok = self.go_to_filtered_jobs(
                keywords=keywords,
                location=loc,
                remote_only=remote_only,
                distance=distance,
                sort_by=sort_by
            )
            if not ok:
                self.logger.error("❌ Falha ao acessar vagas com filtros.")
                return False

            self.logger.info("✅ Filtros aplicados com sucesso.")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao aplicar filtros: {e}")
            self._dump_html("apply_filters_exception")
            return False
    
    def apply_job_search_filters(
        self,
        job_term: str,
        location: str = "São Paulo, SP",
        easy_apply_only: bool = True,
        posted_last_days: int = 1,
        experience_level: str | None = None,
    ) -> bool:
        # apenas encaminha para o método real já implementado
        return self._apply_search_and_filters(
            job_term, location, easy_apply_only, posted_last_days, experience_level
        )

    def process_job_listings(self, max_apply: int = 10):
        """
        Coleta até 30 vagas visíveis, filtra apenas Easy Apply que não foram aplicadas,
        e tenta aplicar até `max_apply`.
        """
        applied = 0
        try:
            # coleta limitada (aprox. 30)
            jobs = self._collect_jobs_from_list(limit=30)

            # filtrar somente Easy Apply e que não têm already_applied
            candidates = [j for j in jobs if j.get("easy_apply") and not j.get("already_applied")]
            len_jobs = len(jobs)
            self.logger.info(f"🔎 Após filtro: {len(candidates)} vagas 'Easy Apply' não inscritas (de {len_jobs} coletadas).")

            # iterar e aplicar (respeitando limite)
            for idx, job in enumerate(candidates, start=1):
                if applied >= max_apply:
                    self.logger.info("🎯 Limite de candidaturas atingido.")
                    break
                try:
                    self.logger.info(f"🧭 [{idx}/{len(candidates)}] Tentando aplicar: {job.get('title')} | {job.get('company')} | {job.get('url')}")
                    ok = self.open_and_process_job_card(job.get("el") or job.get("url"), idx)
                    if ok:
                        applied += 1
                        self.logger.info(f"✅ Aplicado: {job.get('url')}")
                    else:
                        self.logger.info(f"⏭️ Não aplicado: {job.get('url')}")
                    # pausa humana variável
                    self.safe_sleep(random.uniform(1.0, 2.0))
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao processar vaga #{idx}: {e}")
                    self._dump_html(f"process_job_error_{idx}")
            self.logger.info(f"✅ Processamento finalizado | Total candidaturas efetuadas: {applied}")
            return applied

        except Exception as e:
            self.logger.error(f"💥 Erro ao percorrer vagas: {e}")
            self._dump_html("listings_iteration_error")
            return applied

    def robust_click(self, element):
        """
        Tenta clicar de forma robusta: espera clickable -> scrollIntoView -> click -> JS click fallback.
        Retorna True se clicou sem lançar exceção.
        """
        try:
            WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.XPATH, ".//*")))
        except Exception:
            pass
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            time.sleep(0.3)
            try:
                element.click()
                return True
            except (ElementClickInterceptedException, ElementNotInteractableException):
                # JS click fallback
                try:
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception:
                    return False
        except Exception:
            return False


    def open_and_process_job_card(self, anchor_el_or_url, idx: int) -> bool:
        try:
            # helper para fechar overlays que bloqueiam cliques
            def _close_overlays():
                for xp in [
                    "//button[@aria-label='Fechar']",
                    "//button[contains(normalize-space(.),'Fechar')]",
                    "//button[contains(normalize-space(.),'Close')]",
                    "//button[contains(normalize-space(.),'Cancelar')]"
                ]:
                    for b in self.driver.find_elements(By.XPATH, xp):
                        try:
                            if b.is_displayed():
                                self.driver.execute_script("arguments[0].click();", b)
                                self.safe_sleep(0.2)
                        except Exception:
                            continue

            _close_overlays()

            # Se passou URL, navegar diretamente (fallback)
            if isinstance(anchor_el_or_url, str):
                url = anchor_el_or_url
                self.logger.info(f"🔗 Navegando para URL (fallback): {url}")
                self.driver.get(url)
                self.safe_sleep(1.2)
            else:
                # elemento do card
                li = anchor_el_or_url
                # tentar achar link do card
                a = None
                try:
                    a = li.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/'], a.base-card__full-link, a.job-card-list__title, a.job-card-container__link")
                except Exception:
                    try:
                        a = li.find_element(By.TAG_NAME, "a")
                    except Exception:
                        a = None

                # 1) tentar detectar botão/link 'Candidatura simplificada' dentro do próprio card
                try:
                    # texto "Candidatura simplificada" ou "Easy Apply" dentro do card
                    if li.find_elements(By.XPATH, ".//*[contains(normalize-space(.),'Candidatura simplificada') or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'easy apply')]"):
                        self.logger.info("🖱️ Easy Apply detectado dentro do card (por texto). Clicando no card para abrir painel e depois no botão.")
                        # abrir painel clicando no link/título
                        if a:
                            self.robust_click(a)
                            self.safe_sleep(0.8)
                    else:
                        # também procurar botões/anchors no card
                        btns = li.find_elements(By.XPATH,
                            ".//button[contains(@class,'jobs-apply-button') or contains(@data-control-name,'apply') or contains(. ,'Easy Apply') or contains(. ,'Candidatura')] | .//a[contains(. ,'Easy Apply') or contains(. ,'Candidatura')]"
                        )
                        if btns:
                            self.logger.info("🖱️ Botão Easy Apply encontrado dentro do card; clicando (JS fallback).")
                            try:
                                self.driver.execute_script("arguments[0].click();", btns[0])
                                self.safe_sleep(1.0)
                                return self.handle_application_modal()
                            except Exception:
                                try:
                                    btns[0].click()
                                    self.safe_sleep(1.0)
                                    return self.handle_application_modal()
                                except Exception:
                                    pass

                    # 2) abrir painel direito (clicar no link/título) e procurar o botão lá
                    if a:
                        self.logger.info("➡️ Abrindo painel direito do card (click no link).")
                        try:
                            self.robust_click(a)
                        except Exception:
                            try:
                                self.driver.execute_script("arguments[0].click();", a)
                            except Exception:
                                pass
                        # esperar painel carregar
                        WebDriverWait(self.driver, self.timeout).until(
                            lambda d: d.find_elements(By.XPATH, "//div[contains(@id,'job-details') or contains(@class,'jobs-details__main-content') or contains(@class,'jobs-search__job-details')]")
                        )
                        self.safe_sleep(0.8)

                except Exception:
                    pass

            # Agora estamos no contexto do painel direito ou da página da vaga
            _close_overlays()

            # Rejeitar vagas já aplicadas
            try:
                applied_badge = self.driver.find_elements(By.XPATH,
                    "//*[contains(normalize-space(.),'Candidatura enviada') or contains(normalize-space(.),'Candidatou-se') or contains(normalize-space(.),'Applied')]"
                )
                if applied_badge:
                    self.logger.info("⏩ Já candidatado (detectado no painel/página). Pulando.")
                    return False
            except Exception:
                pass

            # Procurar botão Easy Apply por várias heurísticas no painel/página
            candidate_xpaths = [
                "//button[contains(normalize-space(.),'Candidatura simplificada')]",
                "//button[contains(normalize-space(.),'Easy Apply')]",
                "//button[contains(@data-control-name,'apply') or contains(@data-control-name,'inapply')]",
                "//button[contains(@class,'jobs-apply-button') or contains(@class,'apply') or contains(@class,'in-apply')]",
                "//a[contains(normalize-space(.),'Candidatura simplificada') or contains(normalize-space(.),'Easy Apply') or contains(normalize-space(.),'Apply')]"
            ]
            easy_btn = None
            for xp in candidate_xpaths:
                try:
                    els = self.driver.find_elements(By.XPATH, xp)
                    for e in els:
                        try:
                            if e.is_displayed():
                                easy_btn = e
                                break
                        except Exception:
                            easy_btn = e
                            break
                    if easy_btn:
                        break
                except Exception:
                    continue

            if not easy_btn:
                # debug: salvar screenshot/HTML para análise posterior
                self.logger.info("🔎 Botão de candidatura não encontrado no card/painel. Salvando debug e pulando.")
                self._snap(f"no_easy_apply_{idx}")
                self._dump_html(f"no_easy_apply_{idx}")
                return False

            # tentar clicar no botão Easy Apply
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", easy_btn)
                self.safe_sleep(0.3)
                try:
                    easy_btn.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", easy_btn)
                self.safe_sleep(1.2)
            except Exception as e:
                self.logger.warning(f"❗ Erro ao clicar no Easy Apply: {e}")
                return False

            # delegar ao modal handler
            return bool(self.handle_application_modal())

        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao abrir/processar vaga #{idx}: {e}")
            self._dump_html(f"open_proc_error_{idx}")
            return False

    def go_to_filtered_jobs(
        self,
        keywords: str = "analista financeiro",
        location: str = "Brasil",
        easy_apply_only: bool = True,
        distance: int = 25,
        sort_by: str = "R"  # R = Relevância, DD = Data de publicação
    ):
        """Monta a URL de busca de vagas no LinkedIn já com filtros aplicados."""
        try:
            # GeoIdes usados comumente (ajuste/expanda conforme necessário)
            geo_map = {
                "Brasil": "1047466682",      # (corrigido para geoId comum do Brasil)
                "São Paulo": "106057199",
                "São Paulo, SP": "104176396",  # keep as fallback - adapte se necessário
            }
            # tenta achar melhor match para location (maior correspondência)
            geo_id = None
            for k, v in geo_map.items():
                if k.lower() in location.lower():
                    geo_id = v
                    break
            if not geo_id:
                geo_id = geo_map.get("Brasil", "1047466682")

            base_url = f"{self.BASE_URL}/jobs/search/"
            params = {
                "keywords": keywords,
                "geoId": geo_id,
                "distance": distance,
                # f_AL é o parâmetro que em algumas UIs indica 'Easy Apply' / Aplicações Internas
                "f_AL": "true" if easy_apply_only else "false",
                "origin": "JOB_SEARCH_PAGE_JOB_FILTER",
                "refresh": "true",
                "sortBy": sort_by,
            }

            from urllib.parse import urlencode
            query = urlencode(params)
            final_url = f"{base_url}?{query}"

            self.logger.info(f"➡️ Acessando vagas filtradas: {final_url}")
            self.driver.get(final_url)
            # aguardar elementos da lista aparecerem (cards)
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]") or d.find_elements(By.CSS_SELECTOR, "a.base-card__full-link")
                )
            except TimeoutException:
                self.logger.warning("⏳ Timeout aguardando lista de vagas após acessar URL filtrada.")
            # dar um pequeno tempo extra para JS carregar cards
            self.safe_sleep(2.0)
            self._snap("jobs_search_filtered")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao acessar vagas filtradas: {e}")
            return False

    def _collect_jobs_from_list(self, limit: int = 30) -> List[Dict[str, Any]]:
        jobs = []
        try:
            # Seletores de containers comuns
            cards = self.driver.find_elements(By.CSS_SELECTOR,
                "li[data-occludable-job-id], ul.scaffold-layout__list-container li, ul.jobs-search__results-list li"
            )
            seen = set()
            for card in cards[:limit]:
                try:
                    a = None
                    try:
                        a = card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/'], a.base-card__full-link, a.job-card-list__title, a.job-card-container__link")
                    except Exception:
                        try:
                            a = card.find_element(By.TAG_NAME, "a")
                        except Exception:
                            a = None

                    url = a.get_attribute("href") if a else None
                    if not url or "/jobs/view/" not in url:
                        # pular itens irrelevantes
                        continue
                    base = url.split('?')[0]
                    if base in seen:
                        continue
                    seen.add(base)

                    # detectar 'easy apply' por várias heurísticas (texto dentro do card, link, classes)
                    easy_apply = False
                    try:
                        # procura texto visível no card (pt/en)
                        txts = card.find_elements(By.XPATH,
                            ".//*[contains(normalize-space(.),'Candidatura simplificada') or contains(normalize-space(.),'Candidatura Simplificada') or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'easy apply')]"
                        )
                        if txts:
                            easy_apply = True
                        else:
                            # procura botão/anchor com classes/atributos típicos
                            elems = card.find_elements(By.XPATH,
                                ".//button[contains(@class,'jobs-apply-button') or contains(@data-control-name,'apply') or contains(@aria-label,'Apply') or contains(@aria-label,'Candidatura')] | .//a[contains(@href,'apply') or contains(.,'Easy Apply') or contains(.,'Candidatura') ]"
                            )
                            for e in elems:
                                try:
                                    if e.is_displayed():
                                        easy_apply = True
                                        break
                                except Exception:
                                    easy_apply = True
                                    break
                    except Exception:
                        easy_apply = False

                    # detectar já aplicado (badge/linha)
                    already_applied = False
                    try:
                        badges = card.find_elements(By.XPATH,
                            ".//*[contains(normalize-space(.),'Candidatura enviada') or contains(normalize-space(.),'Candidatou-se') or contains(normalize-space(.),'Applied') or contains(normalize-space(.),'You already applied')]"
                        )
                        if badges:
                            already_applied = True
                    except Exception:
                        already_applied = False

                    # extrair tít./empresa/local (fallbacks)
                    title = ""
                    company = ""
                    location = ""
                    try:
                        el = card.find_element(By.CSS_SELECTOR, ".job-card-list__title, .base-search-card__title, .job-card-container__title")
                        title = el.text.strip()
                    except Exception:
                        pass
                    try:
                        el = card.find_element(By.CSS_SELECTOR, ".job-card-container__company-name, .base-search-card__subtitle, .job-card-list__company")
                        company = el.text.strip()
                    except Exception:
                        pass
                    try:
                        el = card.find_element(By.CSS_SELECTOR, ".job-card-list__location, .job-search-card__location, .job-card-container__metadata-item")
                        location = el.text.strip()
                    except Exception:
                        pass

                    jobs.append({
                        "el": card,
                        "url": base,
                        "job_id": self._extract_job_id_from_url(base),
                        "title": title,
                        "company": company,
                        "location": location,
                        "easy_apply": bool(easy_apply),
                        "already_applied": bool(already_applied),
                        "platform": "LinkedIn"
                    })
                except Exception:
                    continue

            count = len(jobs)
            self.logger.info(f"📝 {count} vagas coletadas da lista (limit={limit}).")
            return jobs

        except Exception as e:
            self.logger.error(f"❌ Erro ao coletar vagas: {e}")
            self._dump_html("collect_jobs_error")
            return jobs

    def handle_application_modal(self) -> bool:
        try:
            # aguardar dialog/modal aparecer
            WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.find_elements(By.XPATH,
                    "//div[@role='dialog'] | //form[contains(@class,'jobs-easy-apply-form')] | //div[contains(@class,'jobs-apply-modal')]"
                )
            )
            self.safe_sleep(0.6)

            default_text_answers = [
                "Tenho experiência sólida na área, com foco em resultados e atenção a detalhes.",
                "Tenho disponibilidade e interesse na vaga anunciada.",
                "Estou à disposição para conversar sobre o cargo."
            ]

            # máximo de iterações (páginas do modal)
            for step in range(12):
                progressed = False

                # selects nativos
                try:
                    selects = self.driver.find_elements(By.TAG_NAME, "select")
                    for sel in selects:
                        try:
                            if not sel.get_attribute("value"):
                                options = sel.find_elements(By.TAG_NAME, "option")
                                chosen = None
                                for o in options:
                                    txt = (o.text or "").strip().lower()
                                    if "sim" in txt or "yes" in txt:
                                        chosen = o
                                        break
                                if not chosen and len(options) > 1:
                                    chosen = options[1]
                                if chosen:
                                    self.driver.execute_script("arguments[0].scrollIntoView(true);", sel)
                                    chosen.click()
                                    progressed = True
                                    self.safe_sleep(0.3)
                        except Exception:
                            continue
                except Exception:
                    pass

                # dropdowns estilizados / listboxes (role='listbox')
                try:
                    boxes = self.driver.find_elements(By.XPATH, "//div[@role='listbox' or contains(@class,'select') or contains(@class,'dropdown')]")
                    for b in boxes:
                        try:
                            if b.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView(true);", b)
                                b.click()
                                self.safe_sleep(0.4)
                                # opções
                                opts = self.driver.find_elements(By.XPATH, "//div[contains(@role,'option')] | //li//span")
                                for o in opts:
                                    txt = (o.text or "").strip().lower()
                                    if "sim" in txt or "yes" in txt:
                                        try:
                                            o.click()
                                            progressed = True
                                            break
                                        except Exception:
                                            continue
                                if not progressed and opts:
                                    try:
                                        opts[0].click()
                                        progressed = True
                                    except Exception:
                                        pass
                                self.safe_sleep(0.3)
                        except Exception:
                            continue
                except Exception:
                    pass

                # radios
                try:
                    radios = self.driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    if radios:
                        for r in radios:
                            try:
                                if r.is_displayed() and not r.is_selected():
                                    lab = (r.get_attribute("value") or "").lower()
                                    if "yes" in lab or "sim" in lab:
                                        r.click()
                                        progressed = True
                                        break
                            except Exception:
                                continue
                        if not progressed:
                            for r in radios:
                                try:
                                    if r.is_displayed() and not r.is_selected():
                                        r.click()
                                        progressed = True
                                        break
                                except Exception:
                                    continue
                except Exception:
                    pass

                # checkboxes
                try:
                    checks = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                    for c in checks:
                        try:
                            if c.is_displayed() and not c.is_selected():
                                c.click()
                                progressed = True
                        except Exception:
                            continue
                except Exception:
                    pass

                # textareas
                try:
                    tars = self.driver.find_elements(By.TAG_NAME, "textarea")
                    for t in tars:
                        try:
                            if t.is_displayed():
                                val = t.get_attribute("value") or ""
                                if not val.strip():
                                    t.clear()
                                    t.send_keys(default_text_answers[step % len(default_text_answers)])
                                    progressed = True
                                    self.safe_sleep(0.2)
                        except Exception:
                            continue
                except Exception:
                    pass

                # inputs texto/numero (evitar sobrescrever email/telefone)
                try:
                    inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number'], input[type='tel']")
                    for inp in inputs:
                        try:
                            if not inp.is_displayed():
                                continue
                            name = (inp.get_attribute("name") or "").lower()
                            idv = (inp.get_attribute("id") or "").lower()
                            if "email" in name or "email" in idv or "phone" in name or "phone" in idv or "tel" in name:
                                continue
                            val = inp.get_attribute("value") or ""
                            if not val.strip():
                                if "pretensão" in name or "salary" in name:
                                    inp.send_keys(str(self.salary_min or 1900))
                                else:
                                    inp.send_keys("1900")
                                progressed = True
                        except Exception:
                            continue
                except Exception:
                    pass

                # tentar avançar / revisar / enviar
                # Avançar / Next / Próximo
                if self.wait_and_click(By.XPATH, "//button[contains(normalize-space(.),'Avançar') or contains(normalize-space(.),'Next') or contains(normalize-space(.),'Próxima') or contains(normalize-space(.),'Próximo')]"):
                    progressed = True
                    self.safe_sleep(0.8)
                    continue

                # Revisar / Review
                if self.wait_and_click(By.XPATH, "//button[contains(normalize-space(.),'Revisar') or contains(normalize-space(.),'Review')]"):
                    progressed = True
                    self.safe_sleep(0.8)
                    continue

                # Botão Enviar final
                if self.wait_and_click(By.XPATH, "//button[contains(normalize-space(.),'Enviar candidatura') or contains(normalize-space(.),'Enviar') or contains(normalize-space(.),'Submit application') or contains(normalize-space(.),'Submit')]"):
                    # aguardar confirmação
                    self.safe_sleep(1.5)
                    self._snap("application_submitted")
                    # fechar modal (Concluído / Done)
                    try:
                        self.wait_and_click(By.XPATH, "//button[contains(normalize-space(.),'Concluído') or contains(normalize-space(.),'Done') or @aria-label='Fechar']")
                    except Exception:
                        pass
                    # verificar mensagem de sucesso
                    ok_msgs = self.driver.find_elements(By.XPATH, "//*[contains(normalize-space(.),'Candidatura enviada') or contains(normalize-space(.),'Application submitted') or contains(normalize-space(.),'Sua candidatura foi enviada')]")
                    if ok_msgs:
                        return True
                    return True

                # nada mudou -> sair
                if not progressed:
                    break

            # se não conseguiu, salvar debug
            self.logger.info("⚠️ Não foi possível completar candidatura simplificada para esta vaga.")
            self._dump_html("apply_incomplete")
            # tentar fechar modal
            try:
                self.wait_and_click(By.XPATH, "//button[@aria-label='Fechar'] | //button[contains(normalize-space(.),'Cancelar') or contains(normalize-space(.),'Cancel')]")
            except Exception:
                pass
            return False

        except Exception as e:
            self.logger.error(f"❌ Erro ao aplicar na vaga: {e}")
            self._dump_html("apply_exception")
            try:
                self.wait_and_click(By.XPATH, "//button[@aria-label='Fechar']")
            except Exception:
                pass
            return False

    def answer_question(self, label: str, input_el):
        """
        Responde perguntas do formulário de candidatura de forma automática e inteligente.
        """
        respostas_predefinidas = {
            "salary": "R$ 1.900",
            "salário": "R$ 1.900",
            "pretensão": "R$ 2.300",
            "remuneração": "R$ 2.300",
            "english": "Básico",
            "ingles": "Básico",
            "inglês": "Básico",
            "spanish": "Básico",
            "experiência": "Tenho mais de 3 anos de experiência relevante.",
            "motivo": "Busco novos desafios e acredito que minha experiência agrega muito à posição.",
            "benefício": "Sim",
            "curso": "Sim, concluído.",
            "certificação": "Sim, possuo certificações relevantes.",
            "manager": "Sim",
            "liderança": "Sim, já liderei equipes em projetos anteriores.",
            "sim": "Sim",
            "não": "Não",
            "yes": "Yes",
            "no": "No",
        }

        resposta = None
        for chave, valor in respostas_predefinidas.items():
            if chave.lower() in label.lower():
                resposta = valor
                break

        if not resposta:
            resposta = "Sim"  # fallback padrão

        try:
            tag = input_el.tag_name.lower()
            if tag == "input":
                tipo = input_el.get_attribute("type") or ""
                if tipo in ["text", "email", "tel", "number"]:
                    input_el.clear()
                    input_el.send_keys(resposta)
                elif tipo in ["radio", "checkbox"]:
                    self.driver.execute_script("arguments[0].click();", input_el)

            elif tag == "textarea":
                input_el.clear()
                input_el.send_keys(resposta)

            elif tag == "select":
                Select(input_el).select_by_index(1)

            self.logger.info(f"📝 Respondida pergunta '{label}' com: {resposta}")
        except Exception as e:
            self.logger.warning(f"⚠️ Não consegui responder '{label}': {e}")

    def _extract_job_id_from_url(self, url: str) -> str:
        try:
            parts = url.split("/")
            for i, part in enumerate(parts):
                if part == "view" and i + 1 < len(parts):
                    return parts[i + 1]
            return parts[-2] if url.endswith("/") else parts[-1]
        except Exception:
            return url

    def _apply_to_single_job(self, job_url: str) -> bool:
        """Abre a vaga e tenta aplicar via 'Easy Apply' / 'Candidatura simplificada'."""
        try:
            self.driver.get(job_url)
            self.safe_sleep(2)
            self._snap("10_open_job")

            # Scroll pra garantir carregamento do botão
            self.driver.execute_script("window.scrollTo(0, 0);")

            btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@class, 'jobs-apply-button') or contains(., 'Candidatar-se') or contains(., 'Easy Apply')]"
            )
            if not btns:
                self.logger.info("🔎 Vaga sem botão de 'Candidatura simplificada'. Pulando.")
                return False

            try:
                btns[0].click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", btns[0])
            self.safe_sleep(2)
            self._snap("11_easy_apply_clicked")

            # Modal de perguntas
            # Tenta avançar respondendo selects/textos simples
            for _ in range(8):  # no máx. 8 telas de perguntas
                progressed = False

                # selects
                selects = self.driver.find_elements(By.CSS_SELECTOR, "select")
                for sel in selects:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", sel)
                        sel.click()
                        time.sleep(0.5)
                        # tenta marcar "Sim/Yes" se existir, senão pega a 1ª opção válida
                        opts = sel.find_elements(By.TAG_NAME, "option")
                        chosen = None
                        for o in opts:
                            txt = (o.text or "").strip().lower()
                            if "sim" in txt or "yes" in txt:
                                chosen = o
                                break
                        if not chosen and opts:
                            chosen = opts[1] if len(opts) > 1 else opts[0]
                        if chosen:
                            chosen.click()
                            progressed = True
                    except Exception:
                        pass

                # inputs texto com números esperados
                inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='number']")
                for inp in inputs:
                    try:
                        if not inp.get_attribute("value"):
                            inp.send_keys("1900")
                            progressed = True
                    except Exception:
                        pass

                # tenta avançar / revisar / enviar
                if self.wait_and_click(By.XPATH, "//button[contains(., 'Avançar') or contains(., 'Next')]"):
                    progressed = True
                    self.safe_sleep(1)
                    continue

                if self.wait_and_click(By.XPATH, "//button[contains(., 'Revisar') or contains(., 'Review')]"):
                    progressed = True
                    self.safe_sleep(1)

                # enviar candidatura
                if self.wait_and_click(By.XPATH, "//button[contains(., 'Enviar candidatura') or contains(., 'Submit application')]"):
                    self.safe_sleep(2)
                    self._snap("12_application_submitted")
                    # fecha modal
                    self.wait_and_click(By.XPATH, "//button[contains(., 'Concluído') or contains(., 'Done') or @aria-label='Fechar']")
                    return True

                if not progressed:
                    break

            self.logger.info("⚠️ Não foi possível completar candidatura simplificada para esta vaga.")
            self._dump_html("apply_incomplete")
            return False

        except Exception as e:
            self.logger.error(f"❌ Erro ao aplicar na vaga: {e}")
            self._dump_html("apply_exception")
            return False

    # -------------------------- Orquestração --------------------------

    def start_full_automation(self, username, password, job_types, max_applications=10, session_id=None):
        try:
            self.logger.info("🚀 Iniciando automação completa do LinkedIn")

            # 1) Login
            if not self.login(username, password):
                return {"status": "error", "message": "Falha no login"}

            # 2) Tentar acessar diretamente a página de vagas filtradas (mais rápido/robusto)
            term = (job_types or ["analista financeiro"])[0]
            # tenta acessar URL filtrada já no início (favorecer Easy Apply)
            if not self.go_to_filtered_jobs(
                keywords=term,
                location=self.location,
                easy_apply_only=True,
                distance=25,
                sort_by="R"
            ):
                self.logger.warning("⚠️ Falha ao abrir vagas filtradas diretamente; tentando abrir a página de vagas padrão.")
                if not self.go_to_jobs_page():
                    return {"status": "error", "message": "Falha ao abrir página de vagas"}

            # 3) Pequena espera para garantir lista renderizada
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, "li[data-occludable-job-id]") or d.find_elements(By.CSS_SELECTOR, "a.base-card__full-link")
                )
            except TimeoutException:
                self.safe_sleep(2.0)

            # 4) Iterar lista e aplicar em “Candidatura simplificada” (limite e filtro interno)
            applied_count = self.process_job_listings(max_apply=max_applications)
            return {"status": "success", "results": f"Candidaturas efetuadas: {applied_count}"}

        except Exception as e:
            self.logger.error(f"💥 Erro crítico na automação: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            self.close_driver()

    # se em algum ponto chamam flow.close(), ofereça esse alias:
    def close(self):
        try:
            self.close_driver()
        except Exception as e:
            self.logger.warning(f"close() falhou: {e}")
                
        # Alias de compatibilidade (algumas versões chamavam run_full_automation)
    def run_full_automation(
        self,
        job_types: Optional[List[str]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        apply_limit: int = 10,
        max_pages: int = 3,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Mantido por compatibilidade. Encaminha para start_full_automation.
        Ignora max_pages (o LinkedIn carrega infinitamente e a UI muda; usamos coleta limitada).
        Aceita **kwargs para não quebrar chamadas antigas com nomes diferentes.
        """
        # aceita também 'max_applications' no kwargs para não estourar erro de assinatura
        if "max_applications" in kwargs and isinstance(kwargs["max_applications"], int):
            apply_limit = kwargs["max_applications"]

        return self.start_full_automation(
            username=username or "",
            password=password or "",
            job_types=job_types or [],
            max_applications=apply_limit,
            session_id=session_id
        )


# Uso manual (debug local):
if __name__ == "__main__":
    # Permite rodar diretamente este arquivo para um teste rápido
    import getpass
    email = os.environ.get("LI_EMAIL") or input("E-mail LinkedIn: ")
    pwd = os.environ.get("LI_PASSWORD") or getpass.getpass("Senha LinkedIn: ")
    terms = ["analista financeiro"]
    bot = LinkedInFullFlow(headless=False, timeout=40)
    res = bot.start_full_automation(email, pwd, terms, max_applications=1)
    print(json.dumps(res, ensure_ascii=False, indent=2))
