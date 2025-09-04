import os
import tempfile
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from src.analysis.resume_analyzer import ResumeAnalyzer

resume_analysis_bp = Blueprint('resume_analysis', __name__)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@resume_analysis_bp.route('/upload-resume', methods=['POST'])
def upload_resume():
    """Faz upload e análise de currículo"""
    try:
        # Verifica se foi enviado um arquivo
        if 'resume' not in request.files:
            return jsonify({'error': 'Nenhum arquivo foi enviado'}), 400
        
        file = request.files['resume']
        
        # Verifica se o arquivo foi selecionado
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo foi selecionado'}), 400
        
        # Verifica se o arquivo é permitido
        if not allowed_file(file.filename):
            return jsonify({'error': 'Tipo de arquivo não permitido. Use: PDF, TXT, DOC, DOCX'}), 400
        
        # Salva o arquivo temporariamente
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        try:
            # Analisa o currículo
            analyzer = ResumeAnalyzer()
            analysis_result = analyzer.analyze_resume(file_path)
            
            # Remove o arquivo temporário
            os.remove(file_path)
            os.rmdir(temp_dir)
            
            return jsonify({
                'success': True,
                'analysis': analysis_result,
                'filename': filename
            }), 200
            
        except Exception as e:
            # Remove o arquivo temporário em caso de erro
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            raise e
            
    except Exception as e:
        current_app.logger.error(f"Erro na análise do currículo: {str(e)}")
        return jsonify({'error': f'Erro na análise: {str(e)}'}), 500

@resume_analysis_bp.route('/analyze-text', methods=['POST'])
def analyze_text():
    """Analisa texto de currículo enviado diretamente"""
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Texto do currículo é obrigatório'}), 400
        
        resume_text = data['text']
        
        if not resume_text.strip():
            return jsonify({'error': 'Texto do currículo não pode estar vazio'}), 400
        
        # Cria um arquivo temporário com o texto
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, 'resume.txt')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(resume_text)
        
        try:
            # Analisa o currículo
            analyzer = ResumeAnalyzer()
            analysis_result = analyzer.analyze_resume(file_path)
            
            # Remove o arquivo temporário
            os.remove(file_path)
            os.rmdir(temp_dir)
            
            return jsonify({
                'success': True,
                'analysis': analysis_result
            }), 200
            
        except Exception as e:
            # Remove o arquivo temporário em caso de erro
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            raise e
            
    except Exception as e:
        current_app.logger.error(f"Erro na análise do texto: {str(e)}")
        return jsonify({'error': f'Erro na análise: {str(e)}'}), 500

@resume_analysis_bp.route('/job-keywords', methods=['GET'])
def get_job_keywords():
    """Retorna as palavras-chave para cada tipo de vaga"""
    try:
        analyzer = ResumeAnalyzer()
        return jsonify({
            'success': True,
            'keywords': analyzer.job_keywords
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Erro ao obter palavras-chave: {str(e)}")
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@resume_analysis_bp.route('/analysis-tips', methods=['GET'])
def get_analysis_tips():
    """Retorna dicas para melhorar o currículo"""
    tips = {
        'general': [
            "Use palavras-chave específicas da área financeira",
            "Quantifique seus resultados sempre que possível",
            "Destaque experiências com sistemas ERP (SAP, Oracle, TOTVS)",
            "Mencione conhecimentos em Excel avançado e ferramentas de BI",
            "Inclua certificações relevantes (CRC, CFA, etc.)"
        ],
        'analista_financeiro': [
            "Destaque experiências com análise de demonstrações financeiras",
            "Mencione conhecimentos em planejamento e controle orçamentário",
            "Inclua experiências com análise de investimentos",
            "Destaque habilidades em modelagem financeira"
        ],
        'contas_pagar': [
            "Enfatize experiências com gestão de fornecedores",
            "Mencione conhecimentos em fluxo de caixa",
            "Destaque habilidades em negociação de prazos e descontos",
            "Inclua experiências com conciliação bancária"
        ],
        'contas_receber': [
            "Destaque experiências com análise de crédito",
            "Mencione conhecimentos em cobrança e recuperação",
            "Inclua experiências com gestão de inadimplência",
            "Enfatize habilidades em negociação"
        ],
        'analista_precificacao': [
            "Destaque experiências com análise de mercado",
            "Mencione conhecimentos em estratégias de pricing",
            "Inclua experiências com análise de competitividade",
            "Enfatize habilidades analíticas e de pesquisa"
        ],
        'custos': [
            "Destaque experiências com custeio ABC",
            "Mencione conhecimentos em centro de custos",
            "Inclua experiências com análise de variações",
            "Enfatize habilidades em otimização de processos"
        ]
    }
    
    return jsonify({
        'success': True,
        'tips': tips
    }), 200

