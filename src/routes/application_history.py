from flask import Blueprint, request, jsonify
from src.models.application_history import ApplicationHistory, db

application_history_bp = Blueprint('application_history', __name__)

@application_history_bp.route('/api/applications/history', methods=['GET'])
def get_application_history():
    """Obtém o histórico de inscrições"""
    try:
        limit = request.args.get('limit', 50, type=int)
        applications = ApplicationHistory.get_recent_applications(limit)
        
        return jsonify({
            'success': True,
            'applications': applications,
            'total': len(applications)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@application_history_bp.route('/api/applications/statistics', methods=['GET'])
def get_application_statistics():
    """Obtém estatísticas gerais de inscrições"""
    try:
        # Estatísticas gerais
        total_applications = ApplicationHistory.query.count()
        successful_applications = ApplicationHistory.query.filter_by(application_status='success').count()
        failed_applications = ApplicationHistory.query.filter_by(application_status='failed').count()
        pending_applications = ApplicationHistory.query.filter_by(application_status='pending').count()
        
        success_rate = (successful_applications / total_applications * 100) if total_applications > 0 else 0
        
        # Estatísticas por empresa (top 10)
        from sqlalchemy import func
        company_stats = db.session.query(
            ApplicationHistory.company_name,
            func.count(ApplicationHistory.id).label('total'),
            func.sum(func.case([(ApplicationHistory.application_status == 'success', 1)], else_=0)).label('success')
        ).group_by(ApplicationHistory.company_name).order_by(func.count(ApplicationHistory.id).desc()).limit(10).all()
        
        company_statistics = []
        for company, total, success in company_stats:
            company_statistics.append({
                'company': company,
                'total_applications': total,
                'successful_applications': success or 0,
                'success_rate': (success / total * 100) if total > 0 and success else 0
            })
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_applications': total_applications,
                'successful_applications': successful_applications,
                'failed_applications': failed_applications,
                'pending_applications': pending_applications,
                'success_rate': round(success_rate, 2),
                'company_statistics': company_statistics
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@application_history_bp.route('/api/applications/session/<session_id>', methods=['GET'])
def get_session_statistics(session_id):
    """Obtém estatísticas de uma sessão específica"""
    try:
        statistics = ApplicationHistory.get_session_statistics(session_id)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'statistics': statistics
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@application_history_bp.route('/api/applications/check-duplicate', methods=['POST'])
def check_duplicate_application():
    """Verifica se uma vaga já foi aplicada recentemente"""
    try:
        data = request.get_json()
        job_id = data.get('job_id')
        job_url = data.get('job_url')
        days = data.get('days', 30)
        
        duplicate = ApplicationHistory.check_duplicate_application(job_id, job_url, days)
        
        if duplicate:
            return jsonify({
                'success': True,
                'is_duplicate': True,
                'existing_application': duplicate.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'is_duplicate': False
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@application_history_bp.route('/api/applications/create', methods=['POST'])
def create_application_record():
    """Cria um novo registro de inscrição"""
    try:
        data = request.get_json()
        
        job_info = {
            'title': data.get('job_title'),
            'company': data.get('company_name'),
            'url': data.get('job_url'),
            'job_id': data.get('job_id'),
            'location': data.get('location', 'São Paulo, SP'),
            'job_type': data.get('job_type')
        }
        
        status = data.get('status', 'pending')
        session_id = data.get('session_id')
        
        application = ApplicationHistory.create_application_record(job_info, status, session_id)
        
        return jsonify({
            'success': True,
            'application': application.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@application_history_bp.route('/api/applications/<int:application_id>/update', methods=['PUT'])
def update_application_status(application_id):
    """Atualiza o status de uma inscrição"""
    try:
        data = request.get_json()
        
        application = ApplicationHistory.query.get_or_404(application_id)
        
        status = data.get('status')
        error_message = data.get('error_message')
        questions = data.get('questions_answered')
        screenshot_path = data.get('screenshot_path')
        
        application.update_status(status, error_message, questions, screenshot_path)
        
        return jsonify({
            'success': True,
            'application': application.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

