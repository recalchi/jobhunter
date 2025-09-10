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

    def process_job_listings(self, max_apply: int = 30) -> int:
        """
        Itera a lista de vagas e tenta aplicar via Easy Apply.
        Retorna número de candidaturas efetivamente enviadas.
        Quando nenhum candidato é encontrado, grava dumps detalhados por card.
        """
        applied = 0
        try:
            try:
                jobs = self._collect_jobs_from_list(limit=max_apply * 3)
            except Exception:
                jobs = []

            # filtrar candidatos (easy + não aplicado)
            candidates = [j for j in jobs if j.get("easy_apply") and not j.get("already_applied")]
            self.logger.info(f"📝 {len(candidates)} vagas candidatas encontradas (limite solicit.)")

            # Se não encontrou candidatos, gerar debug granular:
            if len(candidates) == 0:
                self.logger.warning("⚠️ Nenhuma vaga marcada como 'easy apply' encontrada — gerando dumps por card para inspeção.")
                # screenshot da página inteira
                try:
                    self._snap("no_candidates_page")
                except Exception:
                    pass
                # dump completo da página
                try:
                    self._dump_html("no_candidates_page")
                except Exception:
                    pass
                # salvar outerHTML de cada card para análise
                for idx, j in enumerate(jobs, start=1):
                    try:
                        label = f"card_{idx}_{j.get('job_id') or 'noid'}"
                        # salvar arquivo com outerHTML
                        fname = os.path.join(self.debug_dir, f"card_out_{int(time.time())}_{label}.html")
                        with open(fname, "w", encoding="utf-8") as f:
                            f.write(j.get("outer_html", "<no-html>"))
                        self.logger.info(f"🧾 Dump do card salvo: {os.path.basename(fname)} | easy_apply={j.get('easy_apply')} applied={j.get('already_applied')} title='{j.get('title')}' company='{j.get('company')}'")
                    except Exception as e:
                        self.logger.warning(f"Não foi possível salvar dump do card #{idx}: {e}")
                # também salvar um resumo em logs para inspeção
                self.logger.info("ℹ️ arquivos de debug gerados em: %s", self.debug_dir)
                return applied

            # limitar
            candidates = candidates[:max_apply]

            for i, job in enumerate(candidates, start=1):
                if applied >= max_apply:
                    break
                try:
                    self.logger.info(f"🧭 [{i}/{len(candidates)}] Processando vaga: {job.get('url') or 'element'} | {job.get('title')} - {job.get('company')}")
                    ok = False
                    # prioriza abrir via elemento quando disponível (mantém painel direito)
                    if job.get("el"):
                        ok = self.open_and_process_job_card(job["el"], i)
                    else:
                        ok = self.open_and_process_job_card(job["url"], i)
                    if ok:
                        applied += 1
                        self.logger.info(f"✅ Aplicação confirmada [{applied}] -> {job.get('url')}")
                    else:
                        self.logger.info(f"⏭️ Aplicação NÃO confirmada (pular) -> {job.get('url')}")
                except Exception as e:
                    self.logger.exception(f"⚠️ Erro ao processar job #{i}: {e}")
                    try:
                        self._dump_html(f"process_job_error_{i}")
                    except Exception:
                        pass
                    continue

            self.logger.info(f"✅ Processamento finalizado | Total aplic. confirmadas: {applied}")
            return applied

        except Exception as e:
            self.logger.exception(f"❌ Erro crítico em process_job_listings: {e}")
            try:
                self._dump_html("process_job_listings_critical")
            except Exception:
                pass
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

    def open_and_process_job_card(self, anchor_el_or_url, idx: int) -> bool:
        """
        Abre o job (elemento ou URL), localiza o botão Easy Apply (com wrappers),
        clica e delega para handle_application_modal. Gera dumps quando houver
        problemas ou quando detecta 'já aplicado'.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        import time, os

        def _close_overlays():
            overlays_xp = [
                "//button[@aria-label='Fechar']",
                "//button[contains(normalize-space(.),'Fechar')]",
                "//button[contains(normalize-space(.),'Close')]",
                "//button[contains(normalize-space(.),'Cancelar')]",
                "//button[contains(normalize-space(.),'Dismiss')]"
            ]
            for xp in overlays_xp:
                try:
                    for b in self.driver.find_elements(By.XPATH, xp):
                        try:
                            if b.is_displayed():
                                self.driver.execute_script("arguments[0].click();", b)
                                self.safe_sleep(0.2)
                        except Exception:
                            continue
                except Exception:
                    continue

        try:
            _close_overlays()

            # abrir via url ou clicando no card
            if isinstance(anchor_el_or_url, str):
                url = anchor_el_or_url
                self.logger.info(f"🔗 Navegando para URL (fallback): {url}")
                self.driver.get(url)
                self.safe_sleep(1.2)
            else:
                li = anchor_el_or_url
                a = None
                try:
                    a = li.find_element(By.CSS_SELECTOR, "a[href*='/jobs/view/'], a.base-card__full-link")
                except Exception:
                    try:
                        a = li.find_element(By.TAG_NAME, "a")
                    except Exception:
                        a = None

                # se o próprio card tem botão easyapply, tentar clicar direto
                try:
                    card_btns = li.find_elements(By.XPATH, ".//button[contains(normalize-space(.),'Candidatura simplificada') or contains(normalize-space(.),'Easy Apply') or contains(@data-control-name,'apply') or contains(@id,'jobs-apply-button-id')]")
                    for btn in card_btns:
                        try:
                            if btn.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                                self.safe_sleep(0.2)
                                try:
                                    btn.click()
                                except Exception:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                self.safe_sleep(1.0)
                                # delega para modal handler
                                return bool(self.handle_application_modal())
                        except Exception:
                            continue
                except Exception:
                    pass

                # abrir painel direito (clicando no link/título)
                if a:
                    try:
                        self.logger.info("🖱️ Abrindo painel direito (clique no título/link do job).")
                        self.robust_click(a)
                        WebDriverWait(self.driver, min(6, max(4, int(self.timeout)))).until(
                            lambda d: d.find_elements(By.CSS_SELECTOR, "div.jobs-details__main-content, div.jobs-unified-top-card, div.job-details-jobs-unified-top-card__container--two-pane")
                        )
                        self.safe_sleep(0.6)
                    except Exception:
                        self.safe_sleep(0.8)

            _close_overlays()

            # detectar 'já aplicado' restrito ao painel (evita falsos positivos)
            panel = None
            panel_selectors = [
                "div.job-details-jobs-unified-top-card__container--two-pane",
                "div.jobs-unified-top-card",
                "div.jobs-details__main-content",
                "div.jobs-details-top-card"
            ]
            for sel in panel_selectors:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if el and el.is_displayed():
                        panel = el
                        break
                except Exception:
                    continue

            search_scope = panel if panel is not None else self.driver
            try:
                applied_badges = search_scope.find_elements(By.XPATH, ".//*[contains(normalize-space(.),'Candidatura enviada') or contains(normalize-space(.),'Candidatou-se') or contains(normalize-space(.),'Applied') or contains(normalize-space(.),'You already applied')]")
                if applied_badges:
                    snippet = (applied_badges[0].text or "")[:200]
                    self.logger.info(f"⏩ Já aplicado detectado no painel (escopo {'panel' if panel else 'page'}). Texto: {snippet}")
                    # dump para debug (screenshot + HTML do painel)
                    try:
                        self._snap(f"applied_detected_{idx}")
                    except Exception:
                        pass
                    try:
                        if panel:
                            fname = os.path.join(self.debug_dir, f"panel_out_{int(time.time())}_{idx}.html")
                            with open(fname, "w", encoding="utf-8") as f:
                                f.write(panel.get_attribute("outerHTML") or "")
                            self.logger.info(f"🧾 HTML do painel salvo: {os.path.basename(fname)}")
                        else:
                            self._dump_html(f"applied_detected_{idx}")
                    except Exception as e:
                        self.logger.warning(f"Não foi possível salvar HTML do painel (applied_detected): {e}")
                    return False
            except Exception:
                pass

            # --- procurar botão Easy Apply com heurísticas (button direto e wrappers) ---
            easy_btn = None
            candidate_xpaths = [
                "//button[@id='jobs-apply-button-id']",
                "//button[contains(@aria-label,'Candidatura simplificada') or contains(@aria-label,'Easy Apply') or contains(@aria-label,'Apply')]",
                "//button[contains(normalize-space(.),'Candidatura simplificada') or contains(normalize-space(.),'Easy Apply')]",
                "//button[contains(@data-control-name,'apply') or contains(@data-control-name,'inapply')]",
                "//a[contains(normalize-space(.),'Candidatura simplificada') or contains(normalize-space(.),'Easy Apply') or contains(normalize-space(.),'Apply')]"
            ]
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

            # fallback: procurar wrappers DIV e pegar botão interno
            if not easy_btn:
                try:
                    div_wrappers = self.driver.find_elements(By.CSS_SELECTOR, "div.jobs-apply-button, div.jobs-apply-button--top-card, div.jobs-s-apply, div.jobs-apply-button--rounded")
                    for dw in div_wrappers:
                        try:
                            btn = None
                            try:
                                btn = dw.find_element(By.TAG_NAME, "button")
                            except Exception:
                                try:
                                    btn = dw.find_element(By.CSS_SELECTOR, "a, div[role='button']")
                                except Exception:
                                    btn = None
                            if btn and (btn.is_displayed() or dw.is_displayed()):
                                easy_btn = btn
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

            if not easy_btn:
                # salvar debug e sair
                self.logger.info("🔎 Botão Easy Apply não encontrado no painel. Criando dump e pulando.")
                try:
                    self._snap(f"no_easy_apply_{idx}")
                except Exception:
                    pass
                try:
                    if panel:
                        fname = os.path.join(self.debug_dir, f"panel_no_easy_{int(time.time())}_{idx}.html")
                        with open(fname, "w", encoding="utf-8") as f:
                            f.write(panel.get_attribute("outerHTML") or "")
                        self.logger.info(f"🧾 HTML do painel salvo: {os.path.basename(fname)}")
                    else:
                        self._dump_html(f"no_easy_apply_{idx}")
                except Exception:
                    pass
                return False

            # log info do elemento antes do clique (útil para debugging)
            try:
                info = easy_btn.get_attribute("aria-label") or easy_btn.text or easy_btn.get_attribute("id") or str(easy_btn)
                self.logger.info(f"🔵 EasyApply encontrado (antes do clique): {info[:180]}")
            except Exception:
                pass

            # clicar no botão com fallback JS e delegar ao handler
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", easy_btn)
                self.safe_sleep(0.25)
                try:
                    easy_btn.click()
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].click();", easy_btn)
                    except Exception:
                        self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click',{bubbles:true}));", easy_btn)
                self.safe_sleep(1.0)
            except Exception as e:
                self.logger.warning(f"⚠️ Falha ao clicar easy_apply: {e}")
                try:
                    self._snap(f"easy_click_failed_{idx}")
                    if panel:
                        fname = os.path.join(self.debug_dir, f"panel_clickfail_{int(time.time())}_{idx}.html")
                        with open(fname, "w", encoding="utf-8") as f:
                            f.write(panel.get_attribute("outerHTML") or "")
                        self.logger.info(f"🧾 HTML do painel salvo: {os.path.basename(fname)}")
                    else:
                        self._dump_html(f"easy_click_failed_{idx}")
                except Exception:
                    pass
                return False

            # Delegar para o handler do modal (retorna True somente se envio confirmado)
            result = False
            try:
                result = bool(self.handle_application_modal())
                # quando a aplicação é confirmada, capturar um screenshot final/HTML (audit)
                if result:
                    try:
                        self.safe_sleep(0.4)  # dar tempo para modal final renderizar
                        self._snap(f"confirmation_{idx}")
                        self._dump_html(f"confirmation_{idx}")
                    except Exception:
                        pass
            except Exception as e:
                self.logger.exception(f"⚠️ Erro ao processar modal na vaga #{idx}: {e}")
                try:
                    self._dump_html(f"modal_handler_exception_{idx}")
                except Exception:
                    pass
                result = False

            _close_overlays()
            return result

        except Exception as e:
            self.logger.exception(f"❌ Erro ao abrir/processar vaga #{idx}: {e}")
            try:
                self._dump_html(f"open_proc_error_{idx}")
            except Exception:
                pass
            return False

    def _collect_jobs_from_list(self, limit: int = 30) -> List[Dict[str, Any]]:
        jobs = []
        try:
            # Seletores de containers comuns (varia entre versões do LinkedIn)
            cards = self.driver.find_elements(By.CSS_SELECTOR,
                "li[data-occludable-job-id], ul.scaffold-layout__list-container li, ul.jobs-search__results-list li, div.job-card-container--clickable"
            )
            seen = set()
            for card in cards[:limit]:
                try:
                    # pegar outerHTML para heurísticas em texto
                    try:
                        outer = (card.get_attribute("outerHTML") or "").lower()
                    except Exception:
                        outer = ""

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
                        # alguns cards aparecem sem link de vaga (ads, promoções)
                        continue
                    base = url.split('?')[0]
                    if base in seen:
                        continue
                    seen.add(base)

                    # heurísticas mais robustas para detectar Easy Apply:
                    easy_apply = False
                    try:
                        if "candidatura simplificada" in outer or "easy apply" in outer or "easyapply" in outer:
                            easy_apply = True
                        # procurar atributos/strings comuns
                        elif "jobs-apply-button" in outer or "data-control-name=\"apply\"" in outer or "data-control-name='apply'" in outer or "apply" in outer and ("button" in outer or "aria-label" in outer):
                            easy_apply = True
                        # checar elementos específicos
                        else:
                            if card.find_elements(By.XPATH, ".//*[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'easy apply')]"):
                                easy_apply = True
                            if card.find_elements(By.XPATH, ".//*[contains(normalize-space(.),'Candidatura simplificada')]"):
                                easy_apply = True
                    except Exception:
                        easy_apply = False

                    # detectar já aplicado (badge/linha)
                    already_applied = False
                    try:
                        if "candidatura enviada" in outer or "candidatou-se" in outer or "applied" in outer:
                            already_applied = True
                        else:
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
                        "outer_html": outer,
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

    def handle_application_modal(self, max_steps: int = 12) -> bool:
        """
        Handler robusto do modal Easy Apply:
        - preenche selects, radios, inputs e textareas com heurísticas;
        - rola o container interno do modal para revelar botões;
        - detecta e trata o popup 'Salvar esta candidatura?';
        - salva screenshots / HTML quando relevante (modal_stuck, confirmation, discard, etc).
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        import re, time, os

        expected_salary = getattr(self, "expected_salary", None) or getattr(self, "salary_min", None) or 1900
        expected_salary_str = str(expected_salary)
        answer_bank = getattr(self, "answer_bank", None) or {
            "salary": expected_salary_str,
            "default_text": "Tenho interesse nesta oportunidade e acredito que minha experiência é compatível.",
            "cover_letter": "Tenho interesse nesta oportunidade. Segue um breve resumo das minhas qualificações...",
            "english": "Básico"
        }
        save_on_discard = getattr(self, "save_on_discard", False)
        audit_on_submit = getattr(self, "audit_on_submit", True)

        def _safe_click(el):
            try:
                if not el:
                    return False
                if el.is_displayed():
                    el.click()
                    return True
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                    return True
                except Exception:
                    try:
                        self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click',{bubbles:true}));", el)
                        return True
                    except Exception:
                        return False
            return False

        def _set_input_value(inp, value):
            try:
                try:
                    inp.clear()
                except Exception:
                    pass
                for ch in str(value):
                    try:
                        inp.send_keys(ch)
                        time.sleep(0.02)
                    except Exception:
                        pass
                try:
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input'))", inp)
                except Exception:
                    pass
                self.logger.debug(f"📝 Campo preenchido via _set_input_value: {value}")
                return True
            except Exception:
                return False

        def _find_modal_container():
            selectors = [
                "div[data-test-modal-container][data-test-modal-id*='easy-apply']",
                "div.jobs-easy-apply-modal__content",
                "div.artdeco-modal__content",
                "div[data-test-modal-container][data-test-modal-id*='easy-apply-modal']",
                "div[role='dialog']"
            ]
            for sel in selectors:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if el and el.is_displayed():
                        return el
                except Exception:
                    continue
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, "div[role='dialog']")
                for e in els:
                    if e.is_displayed():
                        return e
            except Exception:
                pass
            return None

        def _scroll_modal(to="bottom", step=400):
            try:
                modal = _find_modal_container()
                if not modal:
                    return False
                scrollable = None
                try:
                    candidates = modal.find_elements(By.XPATH, ".//*[contains(@class,'artdeco-modal__content') or contains(@class,'jobs-easy-apply-modal__content') or contains(@style,'overflow')]")
                    for c in candidates:
                        try:
                            if c.is_displayed():
                                scrollable = c
                                break
                        except Exception:
                            continue
                except Exception:
                    scrollable = None

                if scrollable is None:
                    scrollable = modal

                if to == "bottom":
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)
                elif to == "top":
                    self.driver.execute_script("arguments[0].scrollTop = 0", scrollable)
                elif to == "step":
                    self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + %d" % step, scrollable)
                else:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", scrollable)
                    except Exception:
                        pass
                return True
            except Exception:
                return False

        try:
            try:
                WebDriverWait(self.driver, min(6, max(3, int(self.timeout)))).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, "div[data-test-modal-container][data-test-modal-id*='easy-apply']") or d.find_elements(By.CSS_SELECTOR, "div.jobs-easy-apply-modal__content") or d.find_elements(By.CSS_SELECTOR, "div.artdeco-modal__content")
                )
            except Exception:
                pass

            dialog = _find_modal_container()
            steps = 0
            last_progress = time.time()
            while steps < max_steps:
                steps += 1
                progressed = False

                # --- selects ---
                try:
                    scope = dialog or self.driver
                    selects = scope.find_elements(By.CSS_SELECTOR, "select")
                    for s in selects:
                        try:
                            opts = s.find_elements(By.TAG_NAME, "option")
                            chosen = None
                            for o in opts:
                                t = (o.text or "").strip().lower()
                                if "sim" in t or t == "yes":
                                    chosen = o
                                    break
                            if not chosen and len(opts) > 1:
                                chosen = opts[1]
                            if chosen:
                                try:
                                    chosen.click()
                                    progressed = True
                                    self.logger.info(f"📝 Select preenchido: {chosen.text[:40]}")
                                except Exception:
                                    try:
                                        self.driver.execute_script("arguments[0].selected = true; arguments[0].dispatchEvent(new Event('change'))", chosen)
                                        progressed = True
                                    except Exception:
                                        pass
                        except Exception:
                            continue
                except Exception:
                    pass

                # --- radios/checkboxes ---
                try:
                    scope = dialog or self.driver
                    inputs = scope.find_elements(By.XPATH, ".//input[@type='radio' or @type='checkbox']")
                    for i_el in inputs:
                        try:
                            label_text = ""
                            try:
                                label_text = i_el.find_element(By.XPATH, "ancestor::label").text.lower()
                            except Exception:
                                label_text = ((i_el.get_attribute("aria-label") or "") + " " + (i_el.get_attribute("name") or "")).lower()
                            if "sim" in label_text or "yes" in label_text or label_text.strip() == "":
                                if _safe_click(i_el):
                                    self.logger.info(f"📝 Radio/Check clicado (preferido): {label_text[:60]}")
                                    progressed = True
                        except Exception:
                            continue
                except Exception:
                    pass

                # --- inputs/textareas ---
                try:
                    scope = dialog or self.driver
                    fields = scope.find_elements(By.XPATH, ".//input[not(@type='hidden')] | .//textarea")
                    for f in fields:
                        try:
                            tag = f.tag_name.lower()
                            typ = (f.get_attribute("type") or "").lower()
                            aria = " ".join([f.get_attribute("aria-label") or "", f.get_attribute("placeholder") or "", f.get_attribute("name") or ""]).lower()
                            current = (f.get_attribute("value") or "").strip()
                            if current:
                                continue

                            if typ in ["number", "tel"] or re.search(r"(sal[aá]rio|pretens|remunera|salary|anos|year|years)", aria):
                                if re.search(r"(year|years|ano|anos)", aria):
                                    _set_input_value(f, "2")
                                    progressed = True
                                    self.logger.info(f"📝 Preenchido anos: 2 ({aria[:40]})")
                                    continue
                                if re.search(r"(sal[aá]rio|pretens|remunera|salary)", aria):
                                    _set_input_value(f, answer_bank.get("salary", expected_salary_str))
                                    progressed = True
                                    self.logger.info(f"📝 Preenchido salário/pretensão: {answer_bank.get('salary', expected_salary_str)} ({aria[:40]})")
                                    continue

                            if tag == "textarea" or typ in ["text","search","email","tel"]:
                                if re.search(r"(por que|why|descreva|motivo|explique|base salarial|salary base|cover letter)", aria):
                                    _set_input_value(f, answer_bank.get("cover_letter"))
                                    progressed = True
                                    self.logger.info(f"📝 Textarea preenchida com cover_letter ({aria[:40]})")
                                    continue
                                if re.search(r"(ingles|english)", aria):
                                    _set_input_value(f, answer_bank.get("english","Básico"))
                                    progressed = True
                                    self.logger.info(f"📝 Preenchido english: {answer_bank.get('english')}")
                                    continue
                                _set_input_value(f, answer_bank.get("default_text"))
                                progressed = True
                                self.logger.info(f"📝 Campo texto preenchido fallback ({aria[:40]})")
                                continue
                        except Exception:
                            continue
                except Exception:
                    pass

                # --- tentar achar/acionar botão Avançar/Revisar/Enviar ---
                try:
                    scope = dialog or self.driver
                    candidate_btns = []
                    try:
                        candidate_btns.extend(scope.find_elements(By.CSS_SELECTOR, "button[data-live-test-easy-apply-submit-button], button[data-test-dialog-primary-btn], button[data-control-name='application_btn'], button[data-control-name='save_application_btn']"))
                    except Exception:
                        pass

                    if not candidate_btns:
                        texts = ["enviar candidatura","submit application","submit","revisar","avançar","next"]
                        for t in texts:
                            try:
                                els = scope.find_elements(By.XPATH, f".//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'{t}')]")
                                if els:
                                    candidate_btns.extend(els)
                            except Exception:
                                continue

                    clicked_any = False
                    for btn in candidate_btns:
                        try:
                            txt = (btn.text or "").strip().lower()
                            try:
                                modal = _find_modal_container()
                                if modal:
                                    # scroll container so button is visible
                                    self.driver.execute_script("arguments[0].scrollTop = arguments[1].offsetTop - 24;", modal, btn)
                            except Exception:
                                try:
                                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                                except Exception:
                                    pass

                            # priorizar envio/revisar
                            if any(k in txt for k in ("enviar","submit","revisar")):
                                if _safe_click(btn):
                                    clicked_any = True
                                    progressed = True
                                    last_progress = time.time()
                                    self.safe_sleep(0.9)
                                    break
                            else:
                                if _safe_click(btn):
                                    clicked_any = True
                                    progressed = True
                                    last_progress = time.time()
                                    self.safe_sleep(0.7)
                                    break
                        except Exception:
                            continue

                    if clicked_any:
                        # esperar confirmação (texto no modal ou page source)
                        try:
                            WebDriverWait(self.driver, min(8, max(4, int(self.timeout)))).until(
                                lambda d: d.find_elements(By.XPATH, "//*[contains(normalize-space(.),'Candidatura enviada') or contains(normalize-space(.),'Application submitted') or contains(normalize-space(.),'Application sent') or contains(normalize-space(.),'Sua candidatura') or contains(normalize-space(.),'Sua candidatura na')]")
                            )
                            self.logger.info("✅ Candidatura enviada (detectada).")
                            # audit snapshot + HTML (útil quando modal some rápido)
                            try:
                                if audit_on_submit:
                                    self.safe_sleep(0.3)
                                    self._snap("confirmation_auto")
                                    self._dump_html("confirmation_auto")
                            except Exception:
                                pass
                            self.safe_sleep(0.6)
                            return True
                        except Exception:
                            # fallback por page_source
                            page_src = (self.driver.page_source or "").lower()
                            if any(k in page_src for k in ["candidatura enviada","application submitted","application sent","you applied","sua candidatura","foi enviada"]):
                                self.logger.info("✅ Candidatura enviada (detected fallback page).")
                                try:
                                    if audit_on_submit:
                                        self.safe_sleep(0.3)
                                        self._snap("confirmation_auto")
                                        self._dump_html("confirmation_auto")
                                except Exception:
                                    pass
                                self.safe_sleep(0.6)
                                return True

                except Exception:
                    pass

                # --- detectar popup 'Salvar esta candidatura?' e agir ---
                try:
                    # CORREÇÃO: selector consertado (antes tinha aspa a mais que quebrava)
                    discard_modals = self.driver.find_elements(By.CSS_SELECTOR, "div[data-test-modal-container][data-test-modal-id*='data-test-easy-apply-discard-confirmation'], div[data-test-modal-container][data-test-modal-id*='easy-apply-discard'], div[data-test-easy-apply-discard-confirmation], div[data-test-modal-id*='data-test-easy-apply-discard-confirmation']")
                    if discard_modals:
                        self.logger.info("ℹ️ Popup 'Salvar esta candidatura?' detectado.")
                        # salvar snapshot do popup para debug (sempre)
                        try:
                            self._snap("discard_popup_detected")
                            self._dump_html("discard_popup_detected")
                        except Exception:
                            pass

                        btn_discard = None
                        try:
                            btns = discard_modals[0].find_elements(By.XPATH, ".//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'descartar') or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'discard') or contains(@data-control-name,'discard_application_confirm_btn')]")
                            if btns:
                                btn_discard = btns[0]
                        except Exception:
                            btn_discard = None

                        btn_save = None
                        try:
                            bsave = discard_modals[0].find_elements(By.XPATH, ".//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'salvar') or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'save') or contains(@data-control-name,'save_application_btn')]")
                            if bsave:
                                btn_save = bsave[0]
                        except Exception:
                            btn_save = None

                        try:
                            if save_on_discard and btn_save:
                                _safe_click(btn_save)
                                self.logger.info("ℹ️ Popup 'Salvar esta candidatura' -> cliquei 'Salvar' (config save_on_discard=True).")
                                self.safe_sleep(0.6)
                                return False
                            elif btn_discard:
                                _safe_click(btn_discard)
                                self.logger.info("ℹ️ Popup 'Salvar esta candidatura' -> cliquei 'Descartar'.")
                                self.safe_sleep(0.6)
                                return False
                            else:
                                close_btns = discard_modals[0].find_elements(By.XPATH, ".//button[contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'fechar') or contains(translate(normalize-space(.),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'close')]")
                                if close_btns:
                                    _safe_click(close_btns[0])
                                    self.safe_sleep(0.4)
                                    return False
                        except Exception:
                            pass
                except Exception:
                    pass

                # se nada progrediu, rolar modal e tentar novamente
                if not progressed:
                    _scroll_modal(to="step", step=400)
                    if steps % 3 == 0:
                        _scroll_modal(to="bottom")
                    if time.time() - last_progress > 14:
                        self.logger.info("⚠️ Sem progresso no modal por >14s — salvando debug e abortando esta candidatura.")
                        try:
                            self._snap("modal_stuck")
                            self._dump_html("modal_stuck")
                        except Exception:
                            pass
                        return False

                try:
                    dialog = _find_modal_container()
                except Exception:
                    dialog = dialog

                self.safe_sleep(0.5)

            self.logger.info("⚠️ Max steps atingidos no modal; envio não detectado. Salvando debug.")
            try:
                self._snap("modal_incomplete")
                self._dump_html("modal_incomplete")
            except Exception:
                pass
            return False

        except Exception as e:
            self.logger.exception(f"❌ Erro em handle_application_modal (final): {e}")
            try:
                self._dump_html("handle_modal_exception")
            except Exception:
                pass
            return False

        
    def answer_question(self, input_el, label=""):
        """
        Preenche um input/textarea/select custom conforme heurísticas.
        - input_el: selenium WebElement
        - label: texto do rótulo/placeholder para heurísticas
        """
        from selenium.webdriver.support.ui import Select
        import re

        label = (label or "").strip()
        label_lower = label.lower()
        answer_bank = getattr(self, "answer_bank", {}) or {}
        default_text = answer_bank.get("default_text", "Tenho interesse nesta oportunidade e acredito que minha experiência é compatível.")
        salary_val = str(answer_bank.get("salary", getattr(self, "salary_min", 1900)))
        english_val = answer_bank.get("english", "Básico")
        try:
            tag = (input_el.tag_name or "").lower()
        except Exception:
            tag = ""

        def safe_click(el):
            try:
                el.click()
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                except Exception:
                    return False
            return True

        try:
            # heurística para decidir valor
            if re.search(r"sal[aá]rio|pretens|remunera|salary", label_lower):
                val = salary_val
            elif re.search(r"(por que|why|descreva|motivo|explain|tell us|qual sua pretens)", label_lower):
                val = answer_bank.get("cover_letter", default_text)
            elif re.search(r"ingles|english|proficienc", label_lower):
                val = english_val
            elif re.search(r"anos|idade|years|quantos anos", label_lower):
                # um inteiro pequeno válido (muitas perguntas pedem 0-99)
                val = "1"
            elif re.search(r"cpf|cns|documento", label_lower):
                val = answer_bank.get("document", "")
            elif re.search(r"sim|não|nao|yes|no", label_lower):
                # prefer Sim / Yes se for radio/checkbox
                val = "Sim" if "sim" in label_lower or "yes" in label_lower else "Não"
            else:
                val = default_text

            # SELECT nativo
            if tag == "select":
                try:
                    Select(input_el).select_by_visible_text(val)
                except Exception:
                    # tenta index 1
                    try:
                        Select(input_el).select_by_index(1)
                    except Exception:
                        # tenta a primeira opção que contenha "Sim" / "Yes"
                        try:
                            opts = input_el.find_elements(By.TAG_NAME, "option")
                            for o in opts:
                                t = (o.text or "").lower()
                                if ("sim" in t or "yes" in t) and "não" not in t:
                                    o.click()
                                    break
                            else:
                                if opts:
                                    opts[0].click()
                        except Exception:
                            pass

            # INPUTs (texto/number/radio/checkbox/email/tel)
            elif tag == "input":
                typ = (input_el.get_attribute("type") or "").lower()
                if typ in ["radio", "checkbox"]:
                    # se já estiver checado, nada a fazer
                    checked = input_el.get_attribute("checked") or input_el.get_attribute("aria-checked")
                    if not checked:
                        safe_click(input_el)
                elif typ in ["number"]:
                    # alguns number exigem integer/decimal - heurística
                    if re.search(r"pretens|sal[aá]rio|salary", label_lower):
                        # enviar decimal com ponto se necessário
                        num = salary_val
                    elif re.search(r"anos|years", label_lower):
                        num = "1"
                    else:
                        num = salary_val
                    try:
                        input_el.clear()
                    except Exception:
                        pass
                    input_el.send_keys(num)
                else:
                    # texto simples
                    try:
                        input_el.clear()
                    except Exception:
                        pass
                    input_el.send_keys(val)

            # TEXTAREA
            elif tag == "textarea":
                try:
                    input_el.clear()
                except Exception:
                    pass
                input_el.send_keys(val)

            # controles custom (LinkedIn usa botões/divs como selects)
            else:
                # tenta detectar combobox/listbox (custom select)
                try:
                    role = input_el.get_attribute("role") or ""
                    if "listbox" in role or "combobox" in role or "button" == (input_el.tag_name or "").lower():
                        # abrir opções
                        safe_click(input_el)
                        time.sleep(0.5)
                        # procurar opções visíveis
                        # procura por elementos com role option ou que contenham o texto desejado
                        options = self.driver.find_elements(By.XPATH, "//div[@role='option' or @role='listitem' or contains(@class,'artdeco-dropdown__option')]")
                        chosen = None
                        for o in options:
                            txt = (o.text or "").strip().lower()
                            if not txt:
                                continue
                            if "sim" in val.lower() and ("sim" in txt or "yes" in txt):
                                chosen = o
                                break
                            if val.lower() in txt:
                                chosen = o
                                break
                        if not chosen and options:
                            chosen = options[0]
                        if chosen:
                            safe_click(chosen)
                            return
                except Exception:
                    pass

            self.logger.info(f"📝 answer_question preencheu '{label}' com: {val}")
        except Exception as e:
            self.logger.warning(f"⚠️ answer_question falhou para '{label}': {e}")

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
                if self.wait_and_click(By.XPATH, "//button[contains(normalize-space(.), 'Enviar candidatura') or contains(normalize-space(.), 'Submit application') or //button[@data-live-test-easy-apply-submit-button]"):
                    # depois do clique: esperar por confirmação explícita ou modal de 'Salvar'
                    self._snap("12_after_submit_click")
                    # espera ativa por sinais de confirmação
                    confirmed = False
                    for _ in range(20):  # ~ até 10s (ajuste conforme necessário)
                        time.sleep(0.5)
                        # 1) confirmação automática / fallback page / texto
                        if "candidatura confirmada" in (self.driver.page_source or "").lower() or "candidatura enviada" in (self.driver.page_source or "").lower() or "application submitted" in (self.driver.page_source or "").lower():
                            confirmed = True
                            break
                        # 2) modal "Salvar esta candidatura?" -> clicar em SALVAR para não perder
                        try:
                            save_btn = self.driver.find_elements(By.XPATH, "//button[normalize-space(.)='Salvar' or normalize-space(.)='Save']")
                            if save_btn:
                                self.logger.info("🔔 Modal 'Salvar esta candidatura?' detectado — clicando em Salvar")
                                try:
                                    self.driver.execute_script("arguments[0].click();", save_btn[0])
                                except Exception:
                                    save_btn[0].click()
                                time.sleep(0.5)
                                # depois de salvar, pode aparecer a confirmação
                                continue
                        except Exception:
                            pass
                        # 3) elemento de confirmação estrutural (ex: div com data-test 'confirmation' ou submit status)
                        try:
                            if self.driver.find_elements(By.CSS_SELECTOR, "[data-test='confirmation'], [data-live-test='easy-apply-submitted'], .jobs-submit-confirmation"):
                                confirmed = True
                                break
                        except Exception:
                            pass

                    if confirmed:
                        self._snap("12_application_submitted_confirmed")
                        # opcional: fechar modal safe
                        try:
                            self.wait_and_click(By.XPATH, "//button[contains(normalize-space(.), 'Concluído') or contains(normalize-space(.), 'Done') or @aria-label='Fechar' or contains(@aria-label,'Close')]")
                        except Exception:
                            pass
                        return True
                    else:
                        self.logger.info("⚠️ Não detectada confirmação após envio — salvando dump e screenshot.")
                        self._snap("12_application_submitted_no_confirm")
                        self._dump_html("apply_no_confirm")
                        # tenta fechar modal com mais segurança (não clicar fora)
                        try:
                            self.wait_and_click(By.XPATH, "//button[contains(normalize-space(.), 'Fechar') or @aria-label='Fechar' or contains(@aria-label,'Close')]")
                        except Exception:
                            pass
                        return False


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
