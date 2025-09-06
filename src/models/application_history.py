from datetime import datetime
from src.models.jobs import db

class ApplicationHistory(db.Model):
    """Modelo para histórico de inscrições em vagas"""
    
    __tablename__ = 'application_history'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informações da vaga
    job_title = db.Column(db.String(500), nullable=False)
    company_name = db.Column(db.String(200), nullable=False)
    job_url = db.Column(db.Text, nullable=True)
    job_id = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    
    # Informações da plataforma
    platform = db.Column(db.String(50), nullable=False, default='LinkedIn')
    
    # Status da inscrição
    application_status = db.Column(db.String(50), nullable=False)
    # Possíveis valores: 'success', 'failed', 'pending', 'skipped'
    
    # Detalhes da tentativa
    error_message = db.Column(db.Text, nullable=True)
    questions_answered = db.Column(db.Text, nullable=True)  # JSON das perguntas respondidas
    
    # Timestamps
    attempted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Informações adicionais
    salary_range = db.Column(db.String(100), nullable=True)
    job_type = db.Column(db.String(100), nullable=True)  # Analista Financeiro, Contas a Pagar, etc.
    
    # Metadados
    automation_session_id = db.Column(db.String(100), nullable=True)
    screenshot_path = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<ApplicationHistory {self.job_title} at {self.company_name} - {self.application_status}>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'job_title': self.job_title,
            'company_name': self.company_name,
            'job_url': self.job_url,
            'job_id': self.job_id,
            'location': self.location,
            'platform': self.platform,
            'application_status': self.application_status,
            'error_message': self.error_message,
            'questions_answered': self.questions_answered,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'salary_range': self.salary_range,
            'job_type': self.job_type,
            'automation_session_id': self.automation_session_id,
            'screenshot_path': self.screenshot_path
        }
    
    @staticmethod
    def create_application_record(job_info, status='pending', session_id=None):
        """Cria um novo registro de inscrição"""
        application = ApplicationHistory(
            job_title=job_info.get('title', 'Título não identificado'),
            company_name=job_info.get('company', 'Empresa não identificada'),
            job_url=job_info.get('url'),
            job_id=job_info.get('job_id'),
            location=job_info.get('location', 'São Paulo, SP'),
            platform='LinkedIn',
            application_status=status,
            job_type=job_info.get('job_type'),
            automation_session_id=session_id,
            attempted_at=datetime.utcnow()
        )
        
        db.session.add(application)
        db.session.commit()
        
        return application
    
    def update_status(self, status, error_message=None, questions=None, screenshot_path=None):
        """Atualiza o status da inscrição"""
        self.application_status = status
        
        if error_message:
            self.error_message = error_message
            
        if questions:
            self.questions_answered = questions
            
        if screenshot_path:
            self.screenshot_path = screenshot_path
            
        if status in ['success', 'failed']:
            self.completed_at = datetime.utcnow()
            
        db.session.commit()
    
    @staticmethod
    def get_session_statistics(session_id):
        """Obtém estatísticas de uma sessão de automação"""
        applications = ApplicationHistory.query.filter_by(
            automation_session_id=session_id
        ).all()
        
        total = len(applications)
        success = len([app for app in applications if app.application_status == 'success'])
        failed = len([app for app in applications if app.application_status == 'failed'])
        pending = len([app for app in applications if app.application_status == 'pending'])
        
        return {
            'total_attempts': total,
            'successful_applications': success,
            'failed_applications': failed,
            'pending_applications': pending,
            'success_rate': (success / total * 100) if total > 0 else 0,
            'applications': [app.to_dict() for app in applications]
        }
    
    @staticmethod
    def get_recent_applications(limit=50):
        """Obtém as inscrições mais recentes"""
        applications = ApplicationHistory.query.order_by(
            ApplicationHistory.attempted_at.desc()
        ).limit(limit).all()
        
        return [app.to_dict() for app in applications]
    
    @staticmethod
    def check_duplicate_application(job_id, job_url, days=30):
        """Verifica se já foi feita inscrição para esta vaga nos últimos X dias"""
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Verifica por job_id primeiro
        if job_id:
            existing = ApplicationHistory.query.filter(
                ApplicationHistory.job_id == job_id,
                ApplicationHistory.attempted_at >= cutoff_date,
                ApplicationHistory.application_status == 'success'
            ).first()
            
            if existing:
                return existing
        
        # Se não encontrou por job_id, verifica por URL
        if job_url:
            existing = ApplicationHistory.query.filter(
                ApplicationHistory.job_url == job_url,
                ApplicationHistory.attempted_at >= cutoff_date,
                ApplicationHistory.application_status == 'success'
            ).first()
            
            if existing:
                return existing
        
        return None

