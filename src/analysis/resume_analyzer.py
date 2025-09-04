import re
import os
import logging
from typing import Dict, List, Tuple
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import PyPDF2
from collections import Counter

class ResumeAnalyzer:
    def __init__(self):
        self.setup_nltk()
        self.setup_logging()
        self.job_keywords = {
            'analista_financeiro': [
                'financeiro', 'financial', 'análise', 'analysis', 'demonstrações', 'statements',
                'balanço', 'balance', 'dre', 'fluxo de caixa', 'cash flow', 'orçamento', 'budget',
                'planejamento', 'planning', 'controladoria', 'controlling', 'excel', 'powerbi',
                'tableau', 'sql', 'python', 'r', 'sap', 'oracle', 'contabilidade', 'accounting',
                'auditoria', 'audit', 'compliance', 'risco', 'risk', 'investimento', 'investment'
            ],
            'contas_pagar': [
                'contas a pagar', 'accounts payable', 'fornecedores', 'suppliers', 'pagamentos',
                'payments', 'conciliação', 'reconciliation', 'fluxo de caixa', 'cash flow',
                'vencimentos', 'due dates', 'negociação', 'negotiation', 'desconto', 'discount',
                'juros', 'interest', 'multa', 'penalty', 'sap', 'oracle', 'totvs', 'protheus',
                'excel', 'planilhas', 'spreadsheets', 'processo', 'process', 'rotina', 'routine'
            ],
            'contas_receber': [
                'contas a receber', 'accounts receivable', 'clientes', 'customers', 'cobrança',
                'collection', 'inadimplência', 'default', 'crédito', 'credit', 'análise de crédito',
                'credit analysis', 'limite', 'limit', 'faturamento', 'billing', 'nota fiscal',
                'invoice', 'recebimentos', 'receipts', 'conciliação', 'reconciliation', 'spc',
                'serasa', 'protesto', 'protest', 'negociação', 'negotiation', 'acordo', 'agreement'
            ],
            'analista_precificacao': [
                'precificação', 'pricing', 'preço', 'price', 'margem', 'margin', 'custo', 'cost',
                'markup', 'competitividade', 'competitiveness', 'mercado', 'market', 'pesquisa',
                'research', 'análise', 'analysis', 'estratégia', 'strategy', 'produto', 'product',
                'serviço', 'service', 'valor', 'value', 'elasticidade', 'elasticity', 'demanda',
                'demand', 'oferta', 'supply', 'concorrência', 'competition', 'benchmark'
            ],
            'custos': [
                'custos', 'costs', 'custeio', 'costing', 'abc', 'activity based costing',
                'centro de custo', 'cost center', 'rateio', 'allocation', 'apropriação',
                'appropriation', 'variação', 'variance', 'padrão', 'standard', 'orçamento',
                'budget', 'controle', 'control', 'redução', 'reduction', 'otimização',
                'optimization', 'eficiência', 'efficiency', 'produtividade', 'productivity',
                'margem', 'margin', 'rentabilidade', 'profitability', 'break even'
            ]
        }
        
        self.required_skills = {
            'technical': [
                'excel', 'powerbi', 'tableau', 'sql', 'python', 'r', 'sap', 'oracle', 'totvs',
                'protheus', 'microsiga', 'senior', 'datasul', 'rm', 'logix', 'access', 'vba'
            ],
            'soft_skills': [
                'comunicação', 'communication', 'liderança', 'leadership', 'trabalho em equipe',
                'teamwork', 'organização', 'organization', 'proatividade', 'proactive',
                'analítico', 'analytical', 'detalhista', 'detail oriented', 'responsabilidade',
                'responsibility', 'pontualidade', 'punctuality', 'flexibilidade', 'flexibility'
            ],
            'education': [
                'administração', 'administration', 'economia', 'economics', 'contabilidade',
                'accounting', 'engenharia', 'engineering', 'matemática', 'mathematics',
                'estatística', 'statistics', 'mba', 'pós-graduação', 'graduate', 'mestrado',
                'master', 'doutorado', 'phd', 'crc', 'cfa', 'frm'
            ]
        }
        
    def setup_nltk(self):
        """Configura o NLTK baixando os recursos necessários"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
            
    def setup_logging(self):
        """Configura o logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrai texto de um arquivo PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            self.logger.error(f"Erro ao extrair texto do PDF: {str(e)}")
            return ""
            
    def preprocess_text(self, text: str) -> List[str]:
        """Pré-processa o texto removendo stopwords e aplicando stemming"""
        try:
            # Converte para minúsculas
            text = text.lower()
            
            # Remove caracteres especiais e números
            text = re.sub(r'[^a-záàâãéèêíïóôõöúçñ\s]', '', text)
            
            # Tokeniza
            tokens = word_tokenize(text, language='portuguese')
            
            # Remove stopwords
            stop_words = set(stopwords.words('portuguese'))
            tokens = [token for token in tokens if token not in stop_words and len(token) > 2]
            
            # Aplica stemming
            stemmer = PorterStemmer()
            tokens = [stemmer.stem(token) for token in tokens]
            
            return tokens
            
        except Exception as e:
            self.logger.error(f"Erro no pré-processamento: {str(e)}")
            return []
            
    def calculate_keyword_score(self, resume_tokens: List[str], keywords: List[str]) -> float:
        """Calcula a pontuação baseada na presença de palavras-chave"""
        if not resume_tokens or not keywords:
            return 0.0
            
        # Pré-processa as palavras-chave
        processed_keywords = []
        for keyword in keywords:
            processed_keywords.extend(self.preprocess_text(keyword))
            
        # Conta as ocorrências
        resume_counter = Counter(resume_tokens)
        keyword_matches = 0
        total_keywords = len(set(processed_keywords))
        
        for keyword in set(processed_keywords):
            if keyword in resume_counter:
                keyword_matches += 1
                
        return (keyword_matches / total_keywords) * 100 if total_keywords > 0 else 0.0
        
    def analyze_experience_level(self, text: str) -> Tuple[int, str]:
        """Analisa o nível de experiência baseado no texto"""
        experience_patterns = [
            (r'(\d+)\s*anos?\s*de\s*experiência', 'anos de experiência'),
            (r'(\d+)\s*years?\s*of\s*experience', 'years of experience'),
            (r'experiência\s*de\s*(\d+)\s*anos?', 'experiência de anos'),
            (r'(\d+)\s*anos?\s*atuando', 'anos atuando'),
            (r'(\d+)\s*anos?\s*trabalhando', 'anos trabalhando')
        ]
        
        years = []
        for pattern, description in experience_patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                try:
                    years.append(int(match))
                except ValueError:
                    continue
                    
        if years:
            max_years = max(years)
            if max_years >= 5:
                return max_years, "Sênior"
            elif max_years >= 2:
                return max_years, "Pleno"
            else:
                return max_years, "Júnior"
        else:
            return 0, "Não identificado"
            
    def analyze_education(self, text: str) -> Dict[str, bool]:
        """Analisa a formação educacional"""
        education_analysis = {
            'superior_completo': False,
            'pos_graduacao': False,
            'mba': False,
            'area_relevante': False
        }
        
        text_lower = text.lower()
        
        # Verifica ensino superior
        superior_patterns = [
            'graduação', 'graduado', 'bacharel', 'licenciatura', 'superior completo',
            'formado em', 'degree', 'bachelor', 'graduated'
        ]
        
        for pattern in superior_patterns:
            if pattern in text_lower:
                education_analysis['superior_completo'] = True
                break
                
        # Verifica pós-graduação
        pos_patterns = [
            'pós-graduação', 'pós graduação', 'especialização', 'postgraduate',
            'especialista em', 'graduate certificate'
        ]
        
        for pattern in pos_patterns:
            if pattern in text_lower:
                education_analysis['pos_graduacao'] = True
                break
                
        # Verifica MBA
        mba_patterns = ['mba', 'master of business administration', 'mestrado profissional']
        
        for pattern in mba_patterns:
            if pattern in text_lower:
                education_analysis['mba'] = True
                break
                
        # Verifica área relevante
        relevant_areas = [
            'administração', 'economia', 'contabilidade', 'ciências contábeis',
            'engenharia', 'matemática', 'estatística', 'finanças', 'business',
            'accounting', 'economics', 'finance', 'engineering', 'mathematics'
        ]
        
        for area in relevant_areas:
            if area in text_lower:
                education_analysis['area_relevante'] = True
                break
                
        return education_analysis
        
    def generate_recommendations(self, analysis_results: Dict) -> List[str]:
        """Gera recomendações de melhoria baseadas na análise"""
        recommendations = []
        
        # Recomendações baseadas nas pontuações
        for job_type, score in analysis_results['job_scores'].items():
            if score < 30:
                job_name = job_type.replace('_', ' ').title()
                recommendations.append(
                    f"Para {job_name}: Adicione mais palavras-chave específicas da área, "
                    f"como experiências com sistemas ERP, análises financeiras e processos específicos."
                )
                
        # Recomendações baseadas na experiência
        if analysis_results['experience_years'] < 2:
            recommendations.append(
                "Destaque projetos acadêmicos, estágios e cursos que demonstrem "
                "conhecimento prático na área financeira."
            )
            
        # Recomendações baseadas na educação
        education = analysis_results['education']
        if not education['superior_completo']:
            recommendations.append(
                "Considere completar um curso superior em área relacionada "
                "(Administração, Economia, Contabilidade)."
            )
            
        if not education['pos_graduacao'] and analysis_results['experience_years'] >= 3:
            recommendations.append(
                "Para posições mais seniores, considere fazer uma pós-graduação "
                "ou MBA em Finanças ou Controladoria."
            )
            
        # Recomendações de habilidades técnicas
        if analysis_results['technical_score'] < 40:
            recommendations.append(
                "Desenvolva habilidades em ferramentas como Excel avançado, "
                "Power BI, SQL e sistemas ERP (SAP, Oracle, TOTVS)."
            )
            
        if not recommendations:
            recommendations.append(
                "Seu currículo está bem estruturado! Continue atualizando "
                "com novas experiências e certificações."
            )
            
        return recommendations
        
    def analyze_resume(self, file_path: str) -> Dict:
        """Analisa um currículo e retorna pontuações e recomendações"""
        try:
            # Extrai o texto
            if file_path.lower().endswith('.pdf'):
                text = self.extract_text_from_pdf(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text = file.read()
                    
            if not text:
                raise ValueError("Não foi possível extrair texto do arquivo")
                
            # Pré-processa o texto
            tokens = self.preprocess_text(text)
            
            # Calcula pontuações para cada tipo de vaga
            job_scores = {}
            for job_type, keywords in self.job_keywords.items():
                score = self.calculate_keyword_score(tokens, keywords)
                job_scores[job_type] = round(score, 1)
                
            # Analisa habilidades técnicas
            technical_score = self.calculate_keyword_score(tokens, self.required_skills['technical'])
            
            # Analisa soft skills
            soft_skills_score = self.calculate_keyword_score(tokens, self.required_skills['soft_skills'])
            
            # Analisa experiência
            experience_years, experience_level = self.analyze_experience_level(text)
            
            # Analisa educação
            education = self.analyze_education(text)
            
            # Calcula pontuação geral (0-5 estrelas)
            overall_scores = []
            for score in job_scores.values():
                # Converte para escala de 0-5
                star_score = min(5, max(0, (score / 20)))  # 20% = 1 estrela
                overall_scores.append(star_score)
                
            average_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
            
            # Monta o resultado
            analysis_results = {
                'job_scores': job_scores,
                'technical_score': round(technical_score, 1),
                'soft_skills_score': round(soft_skills_score, 1),
                'experience_years': experience_years,
                'experience_level': experience_level,
                'education': education,
                'overall_rating': round(average_score, 1),
                'star_ratings': {job_type: round((score / 20), 1) for job_type, score in job_scores.items()}
            }
            
            # Gera recomendações
            recommendations = self.generate_recommendations(analysis_results)
            analysis_results['recommendations'] = recommendations
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Erro na análise do currículo: {str(e)}")
            return {
                'error': str(e),
                'job_scores': {},
                'technical_score': 0,
                'soft_skills_score': 0,
                'experience_years': 0,
                'experience_level': 'Erro',
                'education': {},
                'overall_rating': 0,
                'star_ratings': {},
                'recommendations': ['Erro ao analisar o currículo. Verifique o formato do arquivo.']
            }

