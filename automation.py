import json
import os
from flask import Blueprint, request, jsonify, current_app
from src.models.user import db
from src.models.credentials import Credentials
from src.models.jobs import Job
from src.automation.linkedin_automation import LinkedInAutomation

automation_bp = Blueprint('automation', __name__)

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
            existing_cred.google_linked = data.get('google_linked', False)
        else:
            # Cria nova credencial
            new_cred = Credentials(
                platform=data['platform'],
                username=data['username'],
                password=data['password'],
                google_linked=data.get('google_linked', False)
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
            cred_dict = cred.to_dict()
            # Remove a senha da resposta por segurança
            cred_dict.pop('password', None)
            result.append(cred_dict)
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@automation_bp.route('/search-jobs', methods=['POST'])
def search_jobs():
    """Inicia a busca de vagas"""
    try:
        data = request.get_json()
        
        # Valida os dados recebidos
        required_fields = ['job_types', 'platforms']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo {field} é obrigatório'}), 400
        
        job_types = data['job_types']
        platforms = data['platforms']
        filters = data.get('filters', {})
        
        results = {
            'total_jobs_found': 0,
            'total_applications': 0,
            'platform_results': {},
            'errors': []
        }
        
        # Processa cada plataforma
        for platform in platforms:
            try:
                platform_result = _search_platform_jobs(platform, job_types, filters)
                results['platform_results'][platform] = platform_result
                results['total_jobs_found'] += platform_result['jobs_found']
                results['total_applications'] += platform_result['applications_sent']
                
            except Exception as e:
                error_msg = f"Erro na plataforma {platform}: {str(e)}"
                results['errors'].append(error_msg)
                current_app.logger.error(error_msg)
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _search_platform_jobs(platform, job_types, filters):
    """Busca vagas em uma plataforma específica"""
    result = {
        'jobs_found': 0,
        'applications_sent': 0,
        'jobs': [],
        'errors': []
    }
    
    try:
        # Busca as credenciais da plataforma
        credentials = Credentials.query.filter_by(platform=platform).first()
        if not credentials:
            raise Exception(f"Credenciais não encontradas para {platform}")
        
        if platform.lower() == 'linkedin':
            result = _search_linkedin_jobs(credentials, job_types, filters)
        elif platform.lower() == 'infojobs':
            result = _search_infojobs_jobs(credentials, job_types, filters)
        elif platform.lower() == 'catho':
            result = _search_catho_jobs(credentials, job_types, filters)
        elif platform.lower() == 'gupy':
            result = _search_gupy_jobs(credentials, job_types, filters)
        else:
            raise Exception(f"Plataforma {platform} não suportada")
            
    except Exception as e:
        result['errors'].append(str(e))
        
    return result

def _search_linkedin_jobs(credentials, job_types, filters):
    """Busca vagas no LinkedIn"""
    result = {
        'jobs_found': 0,
        'applications_sent': 0,
        'jobs': [],
        'errors': []
    }
    
    automation = None
    try:
        automation = LinkedInAutomation(headless=True)
        automation.setup_driver()
        
        # Faz login
        if not automation.login(credentials.username, credentials.password):
            raise Exception("Falha no login do LinkedIn")
        
        # Busca vagas
        jobs_found = automation.search_jobs(
            job_types=job_types,
            location=filters.get('location', 'São Paulo'),
            salary_min=filters.get('salary_min', 1900)
        )
        
        result['jobs_found'] = len(jobs_found)
        
        # Salva as vagas no banco de dados
        for job_data in jobs_found:
            try:
                # Verifica se a vaga já existe
                existing_job = Job.query.filter_by(
                    job_id=job_data['job_id'],
                    platform=job_data['platform']
                ).first()
                
                if not existing_job:
                    new_job = Job(
                        job_id=job_data['job_id'],
                        platform=job_data['platform'],
                        title=job_data['title'],
                        company=job_data['company'],
                        location=job_data['location'],
                        url=job_data['url'],
                        salary_range=job_data.get('salary_range'),
                        status='found'
                    )
                    db.session.add(new_job)
                    result['jobs'].append(job_data)
                    
            except Exception as e:
                result['errors'].append(f"Erro ao salvar vaga: {str(e)}")
        
        db.session.commit()
        
    except Exception as e:
        result['errors'].append(str(e))
        db.session.rollback()
    finally:
        if automation:
            automation.close_driver()
    
    return result

def _search_infojobs_jobs(credentials, job_types, filters):
    """Busca vagas no Infojobs (placeholder)"""
    # TODO: Implementar automação do Infojobs
    return {
        'jobs_found': 0,
        'applications_sent': 0,
        'jobs': [],
        'errors': ['Infojobs ainda não implementado']
    }

def _search_catho_jobs(credentials, job_types, filters):
    """Busca vagas no Catho (placeholder)"""
    # TODO: Implementar automação do Catho
    return {
        'jobs_found': 0,
        'applications_sent': 0,
        'jobs': [],
        'errors': ['Catho ainda não implementado']
    }

def _search_gupy_jobs(credentials, job_types, filters):
    """Busca vagas no Gupy (placeholder)"""
    # TODO: Implementar automação do Gupy
    return {
        'jobs_found': 0,
        'applications_sent': 0,
        'jobs': [],
        'errors': ['Gupy ainda não implementado']
    }

@automation_bp.route('/jobs', methods=['GET'])
def get_jobs():
    """Retorna as vagas encontradas"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        platform = request.args.get('platform')
        status = request.args.get('status')
        
        query = Job.query
        
        if platform:
            query = query.filter_by(platform=platform)
        if status:
            query = query.filter_by(status=status)
            
        jobs = query.order_by(Job.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = {
            'jobs': [job.to_dict() for job in jobs.items],
            'total': jobs.total,
            'pages': jobs.pages,
            'current_page': page
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@automation_bp.route('/apply-jobs', methods=['POST'])
def apply_jobs():
    """Aplica para vagas selecionadas"""
    try:
        data = request.get_json()
        job_ids = data.get('job_ids', [])
        resume_path = data.get('resume_path')
        
        if not job_ids:
            return jsonify({'error': 'Nenhuma vaga selecionada'}), 400
        
        results = {
            'total_applications': 0,
            'successful_applications': 0,
            'failed_applications': 0,
            'details': []
        }
        
        for job_id in job_ids:
            job = Job.query.get(job_id)
            if not job:
                continue
                
            try:
                success = _apply_to_job(job, resume_path)
                if success:
                    job.status = 'applied'
                    results['successful_applications'] += 1
                else:
                    job.status = 'application_failed'
                    results['failed_applications'] += 1
                    
                results['total_applications'] += 1
                results['details'].append({
                    'job_id': job_id,
                    'title': job.title,
                    'company': job.company,
                    'success': success
                })
                
            except Exception as e:
                job.status = 'application_error'
                results['failed_applications'] += 1
                results['details'].append({
                    'job_id': job_id,
                    'title': job.title,
                    'company': job.company,
                    'success': False,
                    'error': str(e)
                })
        
        db.session.commit()
        return jsonify(results), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def _apply_to_job(job, resume_path):
    """Aplica para uma vaga específica"""
    automation = None
    try:
        # Busca as credenciais da plataforma
        credentials = Credentials.query.filter_by(platform=job.platform).first()
        if not credentials:
            return False
        
        if job.platform.lower() == 'linkedin':
            automation = LinkedInAutomation(headless=True)
            automation.setup_driver()
            
            if automation.login(credentials.username, credentials.password):
                return automation.apply_to_job(job.url, resume_path)
                
    except Exception as e:
        current_app.logger.error(f"Erro ao aplicar para vaga {job.job_id}: {str(e)}")
    finally:
        if automation:
            automation.close_driver()
    
    return False

