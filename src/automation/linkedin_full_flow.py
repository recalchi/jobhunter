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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select

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

    def process_job_listings(self, max_apply: int = 10, limit_cards: int = 30):
        """
        Coleta vagas da lista (até `limit_cards`), filtra Easy Apply não inscritas
        e tenta aplicar até atingir max_apply.
        Retorna o número de candidaturas efetuadas.
        """
        from urllib.parse import quote_plus
        applied = 0
        try:
            self.safe_sleep(0.6)

            # garantir que estamos na página de pesquisa (se não, tenta open fallback)
            try:
                current = self.driver.current_url
            except Exception:
                current = ""
            if "linkedin.com/jobs/search" not in (current or ""):
                try:
                    keywords = getattr(self, "search_keywords", getattr(self, "job_term", "analista financeiro"))
                    loc = getattr(self, "location", None) or "Brasil"
                    if hasattr(self, "go_to_filtered_jobs"):
                        self.logger.info("➡️ Tentando abrir página de vagas via go_to_filtered_jobs()")
                        try:
                            self.go_to_filtered_jobs(keywords=keywords, location=loc, sort_by="R")
                        except Exception:
                            base = "https://www.linkedin.com/jobs/search/"
                            params = f"?keywords={quote_plus(keywords)}&f_AL=true&sortBy=R"
                            final = base + params
                            self.logger.info(f"➡️ Acessando fallback: {final}")
                            self.driver.get(final)
                            self.safe_sleep(3)
                    else:
                        base = "https://www.linkedin.com/jobs/search/"
                        params = f"?keywords={quote_plus(keywords)}&f_AL=true&sortBy=R"
                        final = base + params
                        self.logger.info(f"➡️ Acessando (fallback): {final}")
                        self.driver.get(final)
                        self.safe_sleep(3)
                except Exception:
                    self.logger.warning("⚠️ Não consegui garantir página de pesquisa - seguindo mesmo assim.")

            self.safe_sleep(0.8)

            # coletar vagas (preferindo coleta estruturada)
            jobs = []
            try:
                if hasattr(self, "_collect_jobs_from_list"):
                    jobs = self._collect_jobs_from_list(limit=limit_cards)
                else:
                    anchors = self.driver.find_elements(By.XPATH, "//a[contains(@href,'/jobs/view/')]")
                    seen = set()
                    for a in anchors:
                        href = a.get_attribute("href") or ""
                        if not href or "/jobs/view/" not in href:
                            continue
                        base = href.split("?")[0]
                        if base in seen:
                            continue
                        seen.add(base)
                        jobs.append({"url": base})
                        if len(jobs) >= limit_cards:
                            break
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao coletar lista de vagas: {e}")
                self._dump_html("collect_jobs_error")

            if not jobs:
                self.logger.info("🔎 Nenhuma vaga encontrada na lista.")
                return applied

            # Filtrar: aceitar somente vagas easy_apply = True (quando disponivel) e que não estejam already_applied
            filtered = []
            for j in jobs:
                # se _collect_jobs_from_list já retornou estrutura rica
                if isinstance(j, dict) and ("easy_apply" in j or "already_applied" in j):
                    if j.get("already_applied"):
                        continue
                    # se easy_apply é falso/None — ainda assim vamos tentar abrir (pode haver botão no painel)
                    filtered.append(j)
                else:
                    filtered.append(j)

            self.logger.info(f"📝 {len(filtered)} vagas coletadas da lista (limit={limit_cards}).")
            # iterar e aplicar
            for idx, job in enumerate(filtered, start=1):
                if applied >= max_apply:
                    self.logger.info("🎯 Limite de candidaturas atingido.")
                    break

                try:
                    job_url = job.get("url") if isinstance(job, dict) and job.get("url") else (job if isinstance(job, str) else None)
                    self.logger.info(f"🧭 [{idx}/{len(filtered)}] Tentando aplicar:  |  | {job_url or '(card element)'}")

                    ok = False
                    # se tiver elemento 'el' (WebElement) tente abrir via elemento (mais rápido)
                    if isinstance(job, dict) and job.get("el"):
                        # cuidado com stale element: re-localizar pela job_id/href antes de passar
                        try:
                            job_el = job.get("el")
                            job_id = job.get("job_id")
                            if job_id:
                                # re-encontrar elemento na lista para reduzir stale
                                try:
                                    re_el = self.driver.find_element(By.CSS_SELECTOR, f"li[data-occludable-job-id='{job_id}']")
                                    job_el = re_el
                                except Exception:
                                    # fallback: procurar pelo href
                                    try:
                                        re_a = self.driver.find_element(By.XPATH, f"//a[contains(@href,'/jobs/view/{job_id}')]")
                                        parent = re_a.find_element(By.XPATH, "./ancestor::li[1]")
                                        job_el = parent or job_el
                                    except Exception:
                                        pass
                            ok = self.open_and_process_job_card(job_el, idx)
                        except StaleElementReferenceException:
                            self.logger.warning("⚠️ StaleElementReference ao usar elemento; tentando por URL.")
                            if job_url:
                                ok = self.open_and_process_job_card(job_url, idx)
                            else:
                                ok = False
                    else:
                        # usar URL (string)
                        if isinstance(job, dict) and job.get("url"):
                            ok = self.open_and_process_job_card(job.get("url"), idx)
                        elif isinstance(job, str):
                            ok = self.open_and_process_job_card(job, idx)
                        else:
                            ok = False

                    if ok:
                        applied += 1
                        self.logger.info(f"✅ Aplicado ({applied}/{max_apply})")
                    else:
                        self.logger.info("⏭️ Não aplicado (pulando).")

                    self.safe_sleep(random.uniform(1.0, 2.0))
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao processar vaga {job.get('url') if isinstance(job, dict) else job}: {e}")
                    self._dump_html(f"process_job_error_{idx}")
                    self.safe_sleep(0.5)
                    continue

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

    def find_job_cards(self):
        """
        Procura por cards/links de vagas com vários seletors e retorna lista de WebElements (ou dicts).
        Preferência por elementos visíveis no painel esquerdo; fallback para links.
        """
        from selenium.webdriver.common.by import By
        job_cards = []
        selectors = [
            "li[data-occludable-job-id]",           # muito comum
            ".jobs-search-results__list-item",      # lista nova
            ".job-card-container",                  # antigo
            ".job-search-card",                     # fallback
            "a.base-card__full-link",               # links completos
            "a[href*='/jobs/view/']"                # fallback definitivo
        ]
        try:
            for sel in selectors:
                try:
                    els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    visible = [e for e in els if e.is_displayed()]
                    if visible:
                        self.logger.info(f"✅ Encontrados {len(visible)} cards com seletor '{sel}'")
                        job_cards = visible
                        break
                except Exception:
                    continue

            # fallback extra: procurar anchors no painel esquerdo (por vezes os cards estão como links)
            if not job_cards:
                try:
                    anchors = self.driver.find_elements(By.XPATH, "//div[contains(@class,'jobs-search-results')]//a[contains(@href,'/jobs/view/')]")
                    visible = [a for a in anchors if a.is_displayed()]
                    if visible:
                        self.logger.info(f"✅ Fallback: encontrados {len(visible)} anchors de job")
                        job_cards = visible
                except Exception:
                    pass
        except Exception as e:
            self.logger.warning(f"⚠️ Erro em find_job_cards: {e}")
        return job_cards

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
            # dentro de go_to_filtered_jobs
            geo_map = {
                "brasil": ["1047466682", "104746682", "104746682"],    # variações comuns
                "são paulo, sp": ["106057199", "104176396"],
                "sao paulo": ["106057199", "104176396"],
                "são paulo": ["106057199", "104176396"],
                "sao paulo, sp": ["106057199", "104176396"],
            }
            # selecionar melhor match
            geo_id = None
            for k, vals in geo_map.items():
                if k in location.lower():
                    geo_id = vals[0]
                    break
            if not geo_id:
                # tentar extrair geoId direto da url de location (se o usuário passou um geoId)
                if isinstance(location, str) and location.isdigit():
                    geo_id = location
                else:
                    # fallback para Brasil
                    geo_id = geo_map["brasil"][0]

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

    def open_and_process_job_card(self, anchor_el_or_url, idx: int) -> bool:
        """
        Abre card/URL, localiza botão 'Easy Apply' / 'Candidatura simplificada' em múltiplos lugares,
        clica e delega para handle_application_modal(). Retorna True apenas se detectar confirmação.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time, random

        def _close_overlays():
            for xp in [
                "//button[@aria-label='Fechar']", "//button[contains(normalize-space(.),'Fechar')]",
                "//button[contains(normalize-space(.),'Close')]","//button[contains(normalize-space(.),'Cancelar')]"
            ]:
                try:
                    for b in self.driver.find_elements(By.XPATH, xp):
                        if b.is_displayed():
                            try:
                                self.driver.execute_script("arguments[0].click();", b)
                                self.safe_sleep(0.15)
                            except Exception:
                                pass
                except Exception:
                    pass

        try:
            _close_overlays()
            # abrir via url ou clicando no card
            if isinstance(anchor_el_or_url, str):
                self.logger.info(f"🔗 ({idx}) Abrindo URL: {anchor_el_or_url}")
                self.driver.get(anchor_el_or_url)
                self.safe_sleep(1.2)
            else:
                card = anchor_el_or_url
                try:
                    # clicar no card para abrir painel direito (se aplicável)
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                    self.safe_sleep(0.2)
                    try:
                        card.click()
                    except Exception:
                        try:
                            self.driver.execute_script("arguments[0].click();", card)
                        except Exception:
                            pass
                    self.safe_sleep(0.7)
                except Exception:
                    pass

            # buscar botão 'Easy Apply' / 'Candidatura simplificada' em várias localizações:
            apply_selectors = [
                "#jobs-apply-button-id", # ID específico do botão de candidatura simplificada
                "//button[contains(@class, 'jobs-apply-button') and contains(@aria-label, 'Candidatura simplificada')]",
                "//button[contains(@class, 'jobs-apply-button') and contains(@aria-label, 'Easy Apply')]",
                "//button[contains(normalize-space(.),'Candidatura simplificada') or contains(normalize-space(.),'Easy Apply') or contains(normalize-space(.),'Candidatar-se')]",
                "button.jobs-apply-button",                      # classe comum
                "//button[contains(@aria-label,'Apply') or contains(@aria-label,'Candidatura') or contains(@aria-label,'Apply on LinkedIn')]",
                "//a[contains(@href,'apply') and contains(normalize-space(.),'Easy Apply')]",
                "//div[contains(@class,'jobs-apply-button-top-card')]//button"
            ]

            apply_btn = None
            for sel in apply_selectors:
                try:
                    if sel.strip().startswith("//"):
                        els = self.driver.find_elements(By.XPATH, sel)
                    else:
                        els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                    for e in els:
                        try:
                            if e.is_displayed():
                                apply_btn = e
                                break
                        except Exception:
                            apply_btn = e
                            break
                    if apply_btn:
                        break
                except Exception:
                    continue

            # se não encontrou botão direto, procurar no painel direito (panel content)
            if not apply_btn:
                try:
                    right_panel = self.driver.find_element(By.CSS_SELECTOR, "div.jobs-details__main-content, div.jobs-unified-top-card")
                    for sel in ["button", "a"]:
                        candidates = right_panel.find_elements(By.CSS_SELECTOR, sel)
                        for c in candidates:
                            txt = (c.text or "").strip()
                            if ("Candidatura" in txt) or ("Easy Apply" in txt) or ("Candidatar" in txt) or ("Apply" in txt):
                                apply_btn = c
                                break
                        if apply_btn:
                            break
                except Exception:
                    pass

            if not apply_btn:
                self.logger.info(f"⏭️ ({idx}) Botão de candidatura não encontrado — pulando.")
                # snapshot para debug
                self._snap(f"no_apply_button_{idx}")
                return False

            # clicar no botão com fallback JS
            try:
                if apply_btn.is_displayed():
                    try:
                        apply_btn.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", apply_btn)
                else:
                    self.driver.execute_script("arguments[0].click();", apply_btn)
                self.safe_sleep(0.8 + random.random() * 0.6)
            except Exception as e:
                self.logger.warning(f"⚠️ Falha ao clicar apply_btn ({e})")
                self._snap(f"apply_click_error_{idx}")
                return False

            # delegar para handler do modal
            sent = False
            try:
                sent = self.handle_application_modal()
            except Exception as e:
                self.logger.warning(f"⚠️ Erro no handle_application_modal: {e}")
                self._dump_html(f"handle_modal_error_{idx}")
                sent = False

            if sent:
                self._snap(f"confirmation_{idx}")
                self.logger.info(f"✅ Candidatura enviada [{idx}]")
                return True
            else:
                self.logger.info(f"⏭️ Candidatura não confirmada [{idx}]")
                return False

        except Exception as e:
            self.logger.error(f"❌ open_and_process_job_card erro: {e}")
            self._dump_html(f"open_card_error_{idx}")
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

    def handle_application_modal(self, max_steps: int = 20) -> bool:
        """
        Handler robusto do Easy Apply modal.
        - Classifica campos (salary/years/integer/decimal/select/textarea/text)
        - Preenche selects nativos e custom dropdowns (role=listbox / role=option / ul/li)
        - Preenche inputs/textarea com heurísticas (salário -> número, anos -> número, texto longo -> cover_letter)
        - Trata radio/checks (prefere 'Sim' ou primeira opção)
        - Trata popup 'Salvar esta candidatura?' (Descartar por padrão)
        - Retorna True apenas se detectar confirmação final (texto 'Candidatura enviada' / 'Application submitted')
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.webdriver.support import expected_conditions as EC
        import re, time

        # config/heurísticas
        expected_salary = str(getattr(self, "expected_salary", getattr(self, "salary_min", 1900)))
        min_years = str(getattr(self, "min_experience_years", 1))
        answer_bank = getattr(self, "answer_bank", {}) or {}
        default_text = answer_bank.get("default_text", "Tenho interesse nesta oportunidade e acredito que minha experiência é compatível.")
        cover_letter = answer_bank.get("cover_letter", default_text)
        save_on_discard = getattr(self, "save_on_discard", False)

        def _safe_click(el):
            try:
                if not el:
                    return False
                if el.is_displayed():
                    try:
                        el.click()
                        return True
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", el)
                        return True
            except Exception:
                return False
            return False

        def _find_modal_container():
            """Tenta encontrar o modal de candidatura usando vários seletores."""
            for sel in [
                By.XPATH, "//div[@role=\'dialog\']",
                By.XPATH, "//form[contains(@class,\'jobs-easy-apply-form\')]",
                By.CSS_SELECTOR, "div.artdeco-modal-overlay",
                By.CSS_SELECTOR, "div.jobs-easy-apply-modal"
            ]:
                try:
                    if sel[0] == By.XPATH:
                        el = self.driver.find_element(sel[0], sel[1])
                    else:
                        el = self.driver.find_element(sel[0], sel[1])
                    if el.is_displayed():
                        return el
                except (NoSuchElementException, ElementNotInteractableException):
                    continue
            return None

        def _set_input_value(inp, value):
            """Escreve valor lentamente para disparar eventos e dispara event('input') no elemento."""
            try:
                try:
                    inp.clear()
                except Exception:
                    pass
                s = str(value)
                for ch in s:
                    try:
                        inp.send_keys(ch)
                        time.sleep(0.01)
                    except Exception:
                        pass
                try:
                    # disparar event input/change para frameworks que escutam
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));arguments[0].dispatchEvent(new Event('change',{bubbles:true}));", inp)
                except Exception:
                    pass
                return True
            except Exception:
                return False

        def _find_modal_container():
            """Tenta localizar o dialog/modal do Easy Apply com heurísticas."""
            try:
                # seletores comuns
                sels = [
                    "//div[@role='dialog' and .//form[contains(@class,'jobs-apply-form') or .//label]]",
                    "//form[contains(@class,'jobs-easy-apply-form')]",
                    "//div[contains(@class,'jobs-easy-apply-modal')]",
                    "//div[contains(@class,'artdeco-modal__content') and .//form]"
                ]
                for s in sels:
                    els = self.driver.find_elements(By.XPATH, s)
                    for e in els:
                        if e.is_displayed():
                            return e
            except Exception:
                pass
            # fallback: primeiro dialog visível
            try:
                dialogs = self.driver.find_elements(By.XPATH, "//div[@role='dialog']")
                for d in dialogs:
                    if d.is_displayed():
                        return d
            except Exception:
                pass
            return None

        def _get_field_label_text(el):
            """Tenta extrair um rótulo/descrição do elemento (label text / preceding label / placeholder / aria)."""
            try:
                # 1) label[for=id]
                idv = el.get_attribute("id") or ""
                if idv:
                    labs = self.driver.find_elements(By.XPATH, f".//label[@for='{idv}']")
                    if labs:
                        txt = (labs[0].text or "").strip()
                        if txt:
                            return txt
                # 2) label/caption imediato anterior
                try:
                    p = el.find_element(By.XPATH, "./preceding::label[1]")
                    txt = (p.text or "").strip()
                    if txt:
                        return txt
                except Exception:
                    pass
                # 3) aria / placeholder / name / title
                parts = [
                    el.get_attribute("aria-label") or "",
                    el.get_attribute("placeholder") or "",
                    el.get_attribute("aria-describedby") or "",
                    el.get_attribute("name") or "",
                    el.get_attribute("title") or ""
                ]
                aria = " ".join([p for p in parts if p]).strip()
                if aria:
                    return aria
                # 4) pequeno fallback parent text
                try:
                    parent = el.find_element(By.XPATH, "ancestor::div[1]")
                    txt = (parent.text or "").strip()
                    if txt:
                        # reduzir muito longo
                        return (txt.split("\n")[0])[:200]
                except Exception:
                    pass
            except Exception:
                pass
            return ""

        def classify_label(text):
            """Classifica rótulo/descrição em tipos: salary, years, integer, decimal, select, textarea, text"""
            t = (text or "").lower()
            if not t:
                return "text"
            # salário / pretensão
            if re.search(r"sal[aá]rio|pretens[aã]o|expectativa\s*salar|expected\s*salary|remuner|pretens", t):
                return "salary"
            # anos / experiência
            if re.search(r"\b(anos|ano|years|year|experience|quanto tempo|quanto tempo você|quantos anos)\b", t):
                return "years"
            # inteiro / whole number / between
            if re.search(r"\b(whole number|n[uú]mero inteiro|inteiro|entre \d+ e \d+|between \d+ and \d+)\b", t):
                return "integer"
            # decimal / valor monetário
            if re.search(r"\b(decimal|valor|r\$|\$|€|[,\.]\d{1,2}|valor aproximado)\b", t):
                return "decimal"
            # opção sim/não / disponibilidade / presencial / remoto
            if re.search(r"\b(sim|n[aã]o|yes|no|dispon[ií]vel|presencial|remoto|remote|h[ií]brido|aceita|aceito)\b", t):
                return "select"
            # area para texto longo / motivo / descreva / explain
            if len(t) > 90 or re.search(r"(descreva|explique|por que|why|motivo|justifiqu|explain|describe|give details)", t):
                return "textarea"
            return "text"

        def fill_real_select(sel):
            """Preenche <select> nativo (Select helper)."""
            try:
                opts = sel.find_elements(By.TAG_NAME, "option")
                candidate = None
                for o in opts:
                    txt = (o.text or "").strip().lower()
                    if not txt:
                        continue
                    # preferir opção afirmativa
                    if re.match(r"^(sim|yes|true|1|aceito|aceita|dispon[ií]vel)\b", txt):
                        candidate = o
                        break
                if not candidate:
                    # escolher primeiro não-vazio diferente do placeholder
                    for o in opts:
                        txt = (o.text or "").strip().lower()
                        if txt and not re.search(r"selecionar|select|choose|escolha", txt.lower()):
                            candidate = o
                            break
                if candidate:
                    try:
                        # Usar Select do Selenium para selects nativos
                        Select(sel).select_by_visible_text(candidate.text)
                        # Disparar evento de mudança para garantir que o LinkedIn (React) reconheça a seleção
                        self.driver.execute_script("var event = new Event(\'change\', { bubbles: true }); arguments[0].dispatchEvent(event);", sel)
                        self.safe_sleep(0.5) # Pequena pausa para o JS do LinkedIn processar a mudança
                        return True
                    except Exception as e:
                        self.logger.warning(f"⚠️ Falha ao selecionar opção no select nativo com Select: {e}")
                        # Fallback para click direto se Select falhar
                        try:
                            candidate.click()
                            # Disparar evento de mudança para garantir que o LinkedIn (React) reconheça a seleção
                            self.driver.execute_script("var event = new Event(\'change\', { bubbles: true }); arguments[0].dispatchEvent(event);", sel)
                            self.safe_sleep(0.5) # Pequena pausa para o JS do LinkedIn processar a mudança
                            return True
                        except Exception:
                            self.logger.warning(f"⚠️ Falha ao clicar na opção do select nativo: {e}")
                            return False
            except Exception:
                pass
            return False

        def fill_custom_dropdown(toggle_el):
            """
            Tenta abrir custom dropdown / combobox e escolher uma opção.
            heurísticas:
            - abre o toggle
            - busca por role=option, li, button dentro do menu
            - prefere 'Sim'/'Yes' ou opção numérica '1'
            """
            try:
                # abrir
                if not _safe_click(toggle_el):
                    return False
                time.sleep(0.18)
                # procurar menu (após abrir)
                menu_candidates = []
                # role=option/listbox
                menu_candidates += self.driver.find_elements(By.XPATH, "//div[@role='listbox' or @role='menu' or @role='presentation']")
                menu_candidates += self.driver.find_elements(By.XPATH, "//ul[contains(@class,'options') or contains(@class,'menu')]|//div[contains(@class,'options') or contains(@class,'menu')]")
                # filtrar visíveis e próximos ao toggle (prefer)
                menu = None
                for m in menu_candidates:
                    try:
                        if not m.is_displayed():
                            continue
                        # proximidade heurística: contém option
                        opts = m.find_elements(By.XPATH, ".//li|.//button|.//div[@role='option']|.//span")
                        if opts:
                            menu = m
                            break
                    except Exception:
                        continue
                if not menu:
                    # fallback: buscar qualquer option visível
                    opts = self.driver.find_elements(By.XPATH, "//div[@role='option' or @role='menuitem' or contains(@class,'option') or contains(@class,'dropdown__option')]")
                else:
                    opts = menu.find_elements(By.XPATH, ".//div[@role='option'] | .//li | .//button | .//span[normalize-space(.)!='']")
                # escolher opção
                candidate = None
                for o in opts:
                    try:
                        txt = (o.text or "").strip().lower()
                        if not txt:
                            continue
                        if re.match(r"^(sim|yes|true|1|aceito|aceita|dispon[ií]vel)\b", txt):
                            candidate = o
                            break
                    except Exception:
                        continue
                if not candidate:
                    # escolher primeiro não-vazio
                    for o in opts:
                        try:
                            txt = (o.text or "").strip()
                            if txt and not re.search(r"select|selecionar|choose", txt.lower()):
                                candidate = o
                                break
                        except Exception:
                            continue
                if candidate:
                    try:
                        _safe_click(candidate)
                        time.sleep(0.12)
                        # dispatch events if needed
                        try:
                            self.driver.execute_script("arguments[0].dispatchEvent(new Event('click',{bubbles:true}));", candidate)
                        except Exception:
                            pass
                        return True
                    except Exception:
                        return False
            except Exception:
                pass
            return False

        def handle_save_popup_if_present():
            """Detecta popup 'Salvar esta candidatura?' e clica 'Descartar' (ou 'Salvar' se save_on_discard True)."""
            try:
                # procurar por modals/dialogs com esse texto
                els = self.driver.find_elements(By.XPATH, "//div[contains(.,'Salvar esta candidatura') or contains(.,'Save this application') or contains(.,'Salvar sua candidatura')]")
                for d in els:
                    if not d.is_displayed():
                        continue
                    # procurar botões
                    btns = d.find_elements(By.XPATH, ".//button")
                    btn_discard = None
                    btn_save = None
                    for b in btns:
                        t = (b.text or "").strip().lower()
                        if "descartar" in t or "discard" in t:
                            btn_discard = b
                        if "salvar" in t or "save" in t:
                            btn_save = b
                    if btn_discard and not save_on_discard:
                        _safe_click(btn_discard)
                        time.sleep(0.4)
                        self.logger.info("ℹ️ Popup 'Salvar esta candidatura' -> descartei.")
                        return "discarded"
                    if btn_save and save_on_discard:
                        _safe_click(btn_save)
                        time.sleep(0.6)
                        self.logger.info("ℹ️ Popup 'Salvar esta candidatura' -> salvei.")
                        return "saved"
                    # fallback: fechar
                    close = None
                    try:
                        close = d.find_element(By.XPATH, ".//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'fechar') or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'close')]")
                    except Exception:
                        close = None
                    if close:
                        _safe_click(close)
                        time.sleep(0.3)
                        return "closed"
            except Exception:
                pass
            return None

        # ----------------- MAIN -----------------
        try:
            # aguardar modal abrir (breve)
            dialog = None
            try:
                dialog = WebDriverWait(self.driver, min(8, max(3, int(getattr(self, "timeout", 10))))).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role=\'dialog\'] | //form[contains(@class,\'jobs-easy-apply-form\')] | //div[contains(@class,\'artdeco-modal-overlay\')] "))
                )
            except TimeoutException:
                self.logger.warning("⚠️ Timeout ao aguardar modal de candidatura.")
                self._dump_html("modal_timeout")
                return False
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao encontrar modal de candidatura: {e}")
                self._dump_html("modal_find_error")
                return False

            if not dialog:
                self.logger.warning("⚠️ Modal de candidatura não encontrado após espera.")
                return False

            steps = 0
            last_progress = time.time()
            while steps < max_steps:
                steps += 1
                time.sleep(0.25)  # respira um pouco

                # dialog = _find_modal_container() or dialog  # atualizar referência - já atualizado pelo wait
                progressed = False

                # 1) preencher selects nativos
                try:
                    selects = dialog.find_elements(By.XPATH, ".//select")
                    for s in selects:
                        try:
                            lbl = _get_field_label_text(s)
                            # Não pular selects que já têm valor, pois pode ser o placeholder ("Selecionar opção")
                            if fill_real_select(s):
                                progressed = True
                                last_progress = time.time()
                                self.logger.debug(f"📝 select preenchido (nativo) label='{lbl[:60]}'")
                                # Disparar evento de mudança para garantir que o LinkedIn (React) reconheça a seleção
                                self.driver.execute_script("var event = new Event('change', { bubbles: true }); arguments[0].dispatchEvent(event);", s)
                                self.safe_sleep(0.5)  # Pequena pausa para o JS do LinkedIn processar
                        except Exception as e_select:
                            self.logger.warning(f"⚠️ Erro menor ao processar um select: {e_select}")
                            continue
                except Exception as e_group:
                    self.logger.error(f"❌ Erro ao buscar selects no modal: {e_group}")
                    pass

                # 2) preencher custom dropdowns / combobox toggles
                try:
                    toggles = dialog.find_elements(By.XPATH, ".//div[@role='listbox'] | .//button[contains(@class,'select') or contains(@class,'dropdown') or contains(@aria-haspopup,'listbox')] | .//div[contains(@class,'select__control') or contains(@class,'fb-dash-form-element__select')]")
                    for t in toggles:
                        try:
                            # pular se já tiver valor visível
                            txt = (t.text or "").strip()
                            if txt and not re.search(r"selecionar|select|choose|escolha", txt.lower()):
                                continue
                            if fill_custom_dropdown(t):
                                progressed = True
                                last_progress = time.time()
                                self.logger.debug("📝 custom dropdown preenchido")
                        except Exception:
                            continue
                except Exception:
                    pass

                # 3) preencher inputs e textareas
                try:
                    inputs = dialog.find_elements(By.XPATH, ".//input[not(@type='hidden')] | .//textarea")
                    for inp in inputs:
                        try:
                            if not inp.is_displayed():
                                continue
                            # pular se já preenchido
                            current = (inp.get_attribute("value") or "").strip()
                            if current:
                                continue
                            label = _get_field_label_text(inp)
                            qtype = classify_label(label)
                            tag = inp.tag_name.lower()
                            input_type = (inp.get_attribute("type") or "").lower()

                            if qtype == "salary":
                                # colocar só números (remove formatações)
                                val = re.sub(r"[^\d\.]", "", expected_salary)
                                if not val:
                                    val = expected_salary
                                _set_input_value(inp, val)
                                progressed = True
                                last_progress = time.time()
                                self.logger.info(f"📝 Preenchido salário: {val} ({label[:60]})")
                                continue
                            if qtype == "years":
                                _set_input_value(inp, min_years or "1")
                                progressed = True
                                last_progress = time.time()
                                self.logger.info(f"📝 Preenchido anos: {min_years} ({label[:60]})")
                                continue
                            if qtype == "integer":
                                _set_input_value(inp, "1")
                                progressed = True
                                last_progress = time.time()
                                continue
                            if qtype == "decimal":
                                # enviar com .0 se necessário
                                v = expected_salary
                                if isinstance(v, (int, float)):
                                    v = f"{float(v):.1f}"
                                _set_input_value(inp, str(v))
                                progressed = True
                                last_progress = time.time()
                                continue
                            if tag == "textarea" or qtype == "textarea":
                                _set_input_value(inp, cover_letter)
                                progressed = True
                                last_progress = time.time()
                                self.logger.info(f"📝 Preenchido textarea (cover_letter) ({label[:60]})")
                                continue

                            # fallback texto - evitar usar default_text quando a label sugere número
                            if re.search(r"pretens|expectativ|sal[aá]rio|valor|quantos|anos", (label or "").lower()):
                                # tentar colocar número se detectar tokens
                                if re.search(r"sal[aá]rio|pretens|valor", (label or "").lower()):
                                    _set_input_value(inp, re.sub(r"[^\d\.]", "", expected_salary))
                                elif re.search(r"ano|anos|year|years|quantos", (label or "").lower()):
                                    _set_input_value(inp, min_years or "1")
                                else:
                                    _set_input_value(inp, default_text)
                            else:
                                _set_input_value(inp, default_text)
                            progressed = True
                            last_progress = time.time()
                            self.logger.debug(f"📝 input preenchido fallback ({label[:50]})")
                        except Exception:
                            continue
                except Exception:
                    pass

                # 4) radios / checkboxes (prefere 'Sim' / first)
                try:
                    groups = dialog.find_elements(By.XPATH, ".//fieldset | .//div[contains(@class,'choice-list') or contains(@class,'radio-list') or contains(@role,'radiogroup')]")
                    for g in groups:
                        try:
                            options = g.find_elements(By.XPATH, ".//input[@type='radio'] | .//input[@type='checkbox']")
                            if not options:
                                continue
                            if any([o.is_selected() for o in options]):
                                continue
                            chosen = None
                            for o in options:
                                # procurar label próximo com texto Sim/Yes
                                try:
                                    lab = None
                                    # label próximo
                                    labs = o.find_elements(By.XPATH, "./following::label[1] | ./ancestor::label[1]")
                                    if labs:
                                        lab = labs[0]
                                    txt = (lab.text or "").strip().lower() if lab else ""
                                    if re.match(r"^(sim|yes|true|1|aceito|aceita)\b", txt):
                                        chosen = o
                                        break
                                except Exception:
                                    pass
                            if not chosen:
                                chosen = options[0]
                            try:
                                _safe_click(chosen)
                                progressed = True
                                last_progress = time.time()
                                self.logger.debug("📝 radio/checkbox selecionado")
                            except Exception:
                                pass
                        except Exception:
                            continue
                except Exception:
                    pass

                # 5) lidar com popup 'Salvar esta candidatura'
                popup = handle_save_popup_if_present()
                if popup == "discarded":
                    # pop-up descartado -> continuar loop (modal ainda aberto)
                    time.sleep(0.4)
                    continue
                if popup == "saved":
                    # salvou em vez de enviar -> aborta vaga
                    return False

                # 6) clicar botões 'Next'/'Revisar'/'Avançar'/'Submit' se presentes
                clicked_next = False
                try:
                    # procurar no dialog primeiro
                    btn_text_candidates = ["revisar", "avançar", "avancar", "next", "continuar", "enviar candidatura", "enviar", "submit", "review", "done"]
                    buttons = dialog.find_elements(By.XPATH, ".//button[not(@type='hidden') and normalize-space(.)!='']")
                    for b in buttons:
                        try:
                            txt = (b.text or "").strip().lower()
                            if not txt:
                                continue
                            for cand in btn_text_candidates:
                                if cand in txt:
                                    if _safe_click(b):
                                        clicked_next = True
                                        time.sleep(0.6)
                                        last_progress = time.time()
                                        self.logger.debug(f"🖱️ Cliquei botão '{txt[:40]}' no modal")
                                        break
                            if clicked_next:
                                break
                        except Exception:
                            continue
                    # se não clicou e não há candidatos no dialog, tentar buscar no driver (fallback)
                    if not clicked_next:
                        for cand in btn_text_candidates:
                            try:
                                b = self.driver.find_element(By.XPATH, f"//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{cand}')]")
                                if b and b.is_displayed():
                                    if _safe_click(b):
                                        clicked_next = True
                                        time.sleep(0.6)
                                        last_progress = time.time()
                                        break
                            except Exception:
                                continue
                except Exception:
                    pass

                # 7) detectar confirmação final (texto na página / modal de confirmação)
                try:
                    body_text = (self.driver.find_element(By.TAG_NAME, "body").text or "").lower()
                    if ("candidatura enviada" in body_text) or ("application submitted" in body_text) or ("sua candidatura" in body_text and "enviada" in body_text) or ("thank you for applying" in body_text):
                        self.logger.info("✅ Confirmação detectada no body.")
                        return True
                    # também checar por modal de confirmação visível com botão Concluído / Done
                    try:
                        conf = self.driver.find_elements(By.XPATH, "//div[contains(.,'Candidatura enviada') or contains(.,'Application submitted') or .//button[contains(.,'Concluído') or contains(.,'Done')]]")
                        for c in conf:
                            if c.is_displayed():
                                return True
                    except Exception:
                        pass
                except Exception:
                    pass

                # 8) se não clicou em next e modal não mudou, tentar clicar botões primários 'Enviar' / 'Submit'
                if not clicked_next:
                    try:
                        prim = dialog.find_elements(By.XPATH, ".//button[contains(@class,'artdeco-button') and (contains(normalize-space(.),'Enviar') or contains(normalize-space(.),'Submit') or contains(normalize-space(.),'Done') or contains(normalize-space(.),'Concluído'))]")
                        for b in prim:
                            try:
                                txt = (b.text or "").strip().lower()
                                if any(k in txt for k in ["enviar", "submit", "done", "concluído", "concluido"]):
                                    if _safe_click(b):
                                        time.sleep(0.8)
                                        last_progress = time.time()
                                        progressed = True
                                        break
                            except Exception:
                                continue
                    except Exception:
                        pass

                # 9) se não houve progresso por muito tempo -> salvar debug e abortar
                if not progressed and (time.time() - last_progress) > 14:
                    self.logger.info("⚠️ Sem progresso no modal por >14s — salvando debug e abortando esta candidatura.")
                    try:
                        self._snap("modal_stuck")
                    except Exception:
                        pass
                    try:
                        self._dump_html("modal_stuck")
                    except Exception:
                        pass
                    return False

                # pequena pausa antes de próxima iteração
                time.sleep(0.4)

            # max_steps esgotado sem confirmação
            self.logger.info("⚠️ Max steps atingidos no modal; envio não detectado. Salvando debug.")
            try:
                self._snap("modal_incomplete")
            except Exception:
                pass
            try:
                self._dump_html("modal_incomplete")
            except Exception:
                pass
            return False

        except Exception as e:
            self.logger.exception(f"❌ Erro em handle_application_modal: {e}")
            try:
                self._dump_html("handle_modal_exception")
            except Exception:
                pass
            return False

    def _find_and_click_easy_apply(self, job_card, open_panel_if_needed=True):
        selectors = [
            "button.jobs-apply-button--top-card",
            "button.jobs-apply-button",
            "button[id^='jobs-apply-button']",
            "button[aria-label*='Candidatura simplificada']",
            "button[aria-label*='Easy Apply']",
            "div.jobs-apply-button-top-card button"
        ]
        for sel in selectors:
            try:
                btns = job_card.find_elements(By.CSS_SELECTOR, sel)
                for btn in btns:
                    try:
                        if btn.is_displayed():
                            try:
                                WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, ".")))
                            except Exception:
                                pass
                            try:
                                btn.click()
                            except Exception:
                                self.driver.execute_script("arguments[0].click();", btn)
                            return True
                    except Exception:
                        continue
            except Exception:
                continue

        # abrir painel direito (clicando no título) e procurar botão lá
        try:
            link = None
            try:
                link = job_card.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/'], a.job-card-list__title")
            except Exception:
                try:
                    link = job_card.find_element(By.TAG_NAME, "a")
                except Exception:
                    link = None
            if link:
                try:
                    self.robust_click(link)
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].click();", link)
                    except Exception:
                        pass
                self.safe_sleep(0.8)
                # procurar no painel direito
                panel_btns = self.driver.find_elements(By.XPATH,
                    "//button[contains(normalize-space(.),'Candidatura simplificada') or contains(normalize-space(.),'Easy Apply') or contains(normalize-space(.),'Candidatar-se') or contains(@data-control-name,'apply')]"
                )
                for b in panel_btns:
                    if b.is_displayed():
                        try:
                            b.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", b)
                        return True
        except Exception:
            pass

        # busca global (último recurso)
        try:
            global_btns = self.driver.find_elements(By.XPATH, "//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'candidatura simplificada') or contains(.,'Easy Apply') or contains(@aria-label,'Apply')]")
            for b in global_btns:
                if b.is_displayed():
                    try:
                        b.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", b)
                    return True
        except Exception:
            pass

        return False


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

    def parse_validation_and_retry(self, dialog_scope=None):
        """
        Procura mensagens de erro/validação no modal (texto em vermelho / role=alert)
        Se encontrar padrões como 'Enter a whole number' / 'Enter a decimal number' -> tenta ajustar
        Retorna True se tentou corrigir algo (e o caller deve re-iterar), False caso contrário.
        """
        try:
            scope = dialog_scope if dialog_scope is not None else self.driver
            # mensagens de erro comuns: role alert, elementos com atributo data-test...-error, text in red
            msgs = scope.find_elements(By.XPATH, "//*[contains(@class,'error') or contains(@class,'fb-dash-form-element__error') or @role='alert' or contains(@aria-live,'assertive')]")
            if not msgs:
                # procurar spans com texto vermelho (heurístico)
                msgs = scope.find_elements(By.XPATH, "//span[contains(.,'Enter a whole') or contains(.,'decimal number') or contains(.,'larger than') or contains(.,'Digite') or contains(.,'Obrigat') ]")
            for m in msgs:
                text = (m.text or "").lower()
                if not text:
                    continue
                self.logger.info(f"🔍 Validation message found: {text[:80]}")
                if "enter a whole" in text or "whole number" in text or "entre 0 e 99" in text or re.search(r"\bentre\b.*\b0\b.*\b99\b", text):
                    # procurar campo anterior marcado como inválido (procurar input near this message)
                    try:
                        bad_input = m.find_element(By.XPATH, "preceding::input[1] | preceding::textarea[1] | preceding::select[1]")
                    except Exception:
                        bad_input = None
                    if bad_input:
                        # preencher inteiro '2'
                        if _field_has_validation_error(self, bad_input, explicit_value="2"):
                            self.logger.info("🔧 Re-filled numeric after validation hint (2).")
                            return True
                if "decimal number larger" in text or "larger than 0.0" in text:
                    try:
                        bad_input = m.find_element(By.XPATH, "preceding::input[1] | preceding::textarea[1]")
                    except Exception:
                        bad_input = None
                    if bad_input:
                        if _field_has_validation_error(self, bad_input, explicit_value="1"):
                            self.logger.info("🔧 Re-filled decimal after validation hint (1).")
                            return True
                # caso geral: se mensagem contém 'Obrigatório' tentar preencher default text
                if "obrigat" in text or "required" in text:
                    try:
                        bad_input = m.find_element(By.XPATH, "preceding::input[1] | preceding::textarea[1] | preceding::select[1]")
                    except Exception:
                        bad_input = None
                    if bad_input:
                        if _field_has_validation_error(self, bad_input, explicit_value=self.answer_bank.get("default_text", "Tenho interesse nesta oportunidade.")):
                            self.logger.info("🔧 Preenchimento de campo obrigatório via fallback.")
                            return True
        except Exception as e:
            self.logger.debug(f"parse_validation_and_retry error: {e}")
        return False

# centralizar: chamar after submit click
    def handle_save_discard_modal(self, save_on_discard=True, last_click_time=0.0):
        try:
            # procurar modal por texto ou atributos
            discard_modals = self.driver.find_elements(By.XPATH,
                "//div[contains(normalize-space(.),'Salvar esta candidatura') or contains(normalize-space(.),'Save this application') or contains(@data-test-modal-id,'easy-apply-discard') or contains(@data-test-easy-apply-discard,'true')]"
            )
            if not discard_modals:
                return None
            modal = discard_modals[0]
            self.logger.info("ℹ️ Popup 'Salvar esta candidatura?' detectado (handler central).")
            # localizar botões
            try:
                btns = modal.find_elements(By.XPATH, ".//button")
            except Exception:
                btns = []
            btn_save = None
            btn_discard = None
            for b in btns:
                txt = (b.text or "").strip().lower()
                if 'salvar' in txt or txt == 'save':
                    btn_save = b
                if 'descartar' in txt or 'discard' in txt:
                    btn_discard = b
            # se apareceu logo após submit -> preferir salvar
            if last_click_time and (time.time() - last_click_time) < 4.5:
                if btn_save:
                    _safe_click(btn_save)
                    self.logger.info("🔔 Modal pós-submit: cliquei 'Salvar' (preservar aplicação).")
                    return "saved"
            # se configuração pede salvar
            if save_on_discard and btn_save:
                _safe_click(btn_save)
                self.logger.info("ℹ️ Popup 'Salvar esta candidatura' -> cliquei 'Salvar' (config).")
                return "saved"
            # senão descartar (ou fechar)
            if btn_discard:
                _safe_click(btn_discard)
                self.logger.info("ℹ️ Popup 'Salvar esta candidatura' -> cliquei 'Descartar'.")
                return "discarded"
            # fallback: clicar fechar (X)
            try:
                close_btn = modal.find_element(By.XPATH, ".//button[@aria-label='Fechar' or contains(normalize-space(.),'Fechar') or contains(normalize-space(.),'Close')]")
                _safe_click(close_btn)
                return "closed"
            except Exception:
                return None
        except Exception as e:
            self.logger.debug(f"handle_save_discard_modal error: {e}")
            return None


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
