import json
import time
import threading
import uuid
from flask import Blueprint, request, jsonify, current_app
from src.automation.linkedin_full_flow import LinkedInFullFlow
from src.models.jobs import Job, db
from src.models.credentials import Credentials

automation_bp = Blueprint('automation', __name__)

# Variável global para controlar o status da automação
automation_status = {
    'running': False,
    'progress': 0,
    'current_platform': '',
    'logs': [],
    'results': {
        'total_jobs': 0,
        'applications_sent': 0,
        'success_rate': 0,
        'jobs_by_platform': {}
    }
}

def add_log(message, level="INFO"):
    """Adiciona log ao status da automação"""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = {
        'timestamp': timestamp,
        'level': level,
        'message': message
    }
    automation_status['logs'].append(log_entry)
    
    # Mantém apenas os últimos 100 logs
    if len(automation_status['logs']) > 100:
        automation_status['logs'] = automation_status['logs'][-100:]

def run_linkedin_automation(credentials, job_criteria, session_id):
    """Executa a automação do LinkedIn em thread separada"""
    try:
        add_log("🚀 Iniciando automação do LinkedIn...", "SUCCESS")
        automation_status['current_platform'] = 'LinkedIn'
        automation_status['progress'] = 10
        
        # Inicializa a automação com histórico no banco de dados
        linkedin_bot = LinkedInFullFlow(
            headless=False  # Não headless para debug visual e verificação manual
        )
        add_log("✅ Bot do LinkedIn com histórico no banco inicializado")
        
        automation_status['progress'] = 20
        
        # Prepara tipos de vaga
        job_types = []
        if job_criteria.get('analista_financeiro'):
            job_types.append("analista financeiro")
        if job_criteria.get('contas_pagar'):
            job_types.append("contas a pagar")
        if job_criteria.get('contas_receber'):
            job_types.append("contas a receber")
        if job_criteria.get('analista_precificacao'):
            job_types.append("analista de precificacao")
        if job_criteria.get('custos'):
            job_types.append("custos")
            
        if not job_types:
            job_types = ["analista financeiro"]  # Padrão
            
        add_log(f"🎯 Tipos de vaga selecionados: {', '.join(job_types)}")
        
        # Máximo de aplicações
        max_applications = job_criteria.get('max_applications', 3)
        add_log(f"📊 Máximo de aplicações configurado: {max_applications}")
        
        # Extrai credenciais do dicionário
        linkedin_email = credentials.get("linkedin_email")
        linkedin_password = credentials.get("linkedin_password")

        if not linkedin_email or not linkedin_password:
            add_log("❌ Credenciais do LinkedIn não fornecidas ou incompletas.", "ERROR")
            return

        # Executa automação completa com histórico
        add_log("🚀 Executando automação completa com histórico no banco...")
        result = linkedin_bot.start_full_automation(
            username=linkedin_email,
            password=linkedin_password,
            job_types=job_types,
            max_applications=max_applications,
            session_id=automation_status["session_id"]
        )

        
        
        if result.get("success"):
            applications_sent = result.get("applications_sent", 0)
            applied_jobs = result.get("applied_jobs", [])
            
            add_log(f"🎉 Automação concluída com sucesso!", "SUCCESS")
            add_log(f"📈 Total de aplicações enviadas: {applications_sent}", "SUCCESS")
            
            # Atualiza resultados
            automation_status['results']['applications_sent'] += applications_sent
            automation_status['results']['total_jobs'] += len(applied_jobs)
            automation_status['results']['jobs_by_platform']['LinkedIn'] = {
                'found': len(applied_jobs),
                'applied': applications_sent
            }
            
            # Salva no banco de dados
            for job_info in applied_jobs:
                try:
                    job = Job(
                        title=job_info.get('title', ''),
                        company=job_info.get('company', ''),
                        location=job_info.get('location', ''),
                        platform='LinkedIn',
                        job_url=job_info.get('url', ''),
                        status='applied',
                        job_id=job_info.get('job_id', '')
                    )
                    db.session.add(job)
                    db.session.commit()
                    add_log(f"💾 Vaga salva: {job_info.get('title', 'N/A')}")
                except Exception as e:
                    add_log(f"⚠️ Erro ao salvar vaga: {str(e)}", "WARNING")
                    
        else:
            error_msg = result.get("error", "Erro desconhecido")
            add_log(f"❌ Falha na automação: {error_msg}", "ERROR")
        
        # Fecha o navegador
        linkedin_bot.close()
        add_log("🔚 Navegador fechado")
        
    except Exception as e:
        add_log(f"💥 Erro crítico na automação: {str(e)}", "ERROR")
        automation_status['progress'] = 100
    finally:
        automation_status['running'] = False
        automation_status['current_platform'] = ''
        add_log("🏁 Automação finalizada", "SUCCESS")

@automation_bp.route('/start', methods=['POST'])
def start_automation():
    """Inicia o processo de automação"""
    try:
        if automation_status['running']:
            return jsonify({'error': 'Automação já está em execução'}), 400
            
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
            
        # Reseta status        automation_status["running"] = True
        automation_status["logs"] = []
        automation_status['results'] = {
            'total_jobs': 0,
            'applications_sent': 0,
            'success_rate': 0,
            'jobs_by_platform': {}
        }
        
        add_log("🎬 Iniciando processo de automação...", "SUCCESS")
        
        # Obtém credenciais do banco
        credentials = {}
        try:
            linkedin_cred = Credentials.query.filter_by(platform='linkedin').first()
            if linkedin_cred:
                credentials['linkedin_email'] = linkedin_cred.username
                credentials['linkedin_password'] = linkedin_cred.password
                add_log("✅ Credenciais do LinkedIn carregadas")
            else:
                add_log("⚠️ Credenciais do LinkedIn não encontradas", "WARNING")
        except Exception as e:
            add_log(f"❌ Erro ao carregar credenciais: {str(e)}", "ERROR")
            
        # Critérios de busca
        job_criteria = data.get('criteria', {})
        add_log(f"📋 Critérios de busca configurados: {json.dumps(job_criteria, indent=2)}")
        
        # Inicia automação em thread separada
        if data.get('platforms', {}).get('linkedin', False):
            session_id = str(uuid.uuid4())
            automation_status['session_id'] = session_id
            thread = threading.Thread(
                target=run_linkedin_automation,
                args=(credentials, job_criteria, session_id)
            )

            thread.daemon = True
            thread.start()
            add_log("🚀 Thread de automação do LinkedIn iniciada")
        else:
            add_log("ℹ️ LinkedIn não selecionado para automação", "INFO")
            automation_status['running'] = False
            
        return jsonify({
            'success': True,
            'message': 'Automação iniciada com sucesso'
        }), 200
        
    except Exception as e:
        automation_status['running'] = False
        add_log(f"💥 Erro ao iniciar automação: {str(e)}", "ERROR")
        return jsonify({'error': f'Erro ao iniciar automação: {str(e)}'}), 500

@automation_bp.route('/status', methods=['GET'])
def get_automation_status():
    """Retorna o status atual da automação"""
    try:
        # Calcula taxa de sucesso
        if automation_status['results']['total_jobs'] > 0:
            success_rate = (automation_status['results']['applications_sent'] / 
                          automation_status['results']['total_jobs']) * 100
            automation_status['results']['success_rate'] = round(success_rate, 1)
            
        return jsonify({
            'success': True,
            'status': automation_status
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter status: {str(e)}'}), 500

@automation_bp.route('/stop', methods=['POST'])
def stop_automation():
    """Para a automação em execução"""
    try:
        if not automation_status['running']:
            return jsonify({'error': 'Nenhuma automação em execução'}), 400
            
        automation_status['running'] = False
        add_log("🛑 Automação interrompida pelo usuário", "WARNING")
        
        return jsonify({
            'success': True,
            'message': 'Automação interrompida'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao parar automação: {str(e)}'}), 500

@automation_bp.route('/results', methods=['GET'])
def get_results():
    """Retorna os resultados das aplicações"""
    try:
        # Busca vagas do banco de dados
        jobs = Job.query.order_by(Job.created_at.desc()).limit(50).all()
        
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                'id': job.id,
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'platform': job.platform,
                'status': job.status,
                'applied_at': job.created_at.isoformat() if job.created_at else None,
                'job_url': job.job_url
            })
            
        return jsonify({
            'success': True,
            'results': automation_status['results'],
            'jobs': jobs_data
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter resultados: {str(e)}'}), 500

@automation_bp.route('/logs', methods=['GET'])
def get_logs():
    """Retorna os logs da automação"""
    try:
        return jsonify({
            'success': True,
            'logs': automation_status['logs']
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao obter logs: {str(e)}'}), 500

@automation_bp.route('/credentials', methods=['POST'])
def save_credentials():
    """Salva as credenciais das plataformas"""
    try:
        data = request.get_json()
        
        # Valida os dados recebidos
        required_fields = ['platform', 'username', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        # Verifica se já existe credencial para esta plataforma
        existing_cred = Credentials.query.filter_by(platform=data['platform']).first()
        
        if existing_cred:
            # Atualiza credencial existente
            existing_cred.username = data['username']
            existing_cred.password = data['password']
        else:
            # Cria nova credencial
            new_cred = Credentials(
                platform=data['platform'],
                username=data['username'],
                password=data['password']
            )
            db.session.add(new_cred)
        
        db.session.commit()
        return jsonify({'message': 'Credenciais salvas com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@automation_bp.route('/credentials', methods=['GET'])
def get_credentials():
    """Retorna as credenciais salvas (sem senhas)"""
    try:
        credentials = Credentials.query.all()
        result = []
        
        for cred in credentials:
            result.append({
                'id': cred.id,
                'platform': cred.platform,
                'username': cred.username,
                'created_at': cred.created_at.isoformat() if cred.created_at else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

