from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class Job(db.Model):
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(255), nullable=False)  # ID único da vaga
    platform = db.Column(db.String(50), nullable=False)  # LinkedIn, Infojobs, Catho, Gupy
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    url = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    applied_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    status = db.Column(db.String(50), default='pending')  # pending, applied, error, rejected
    second_stage_check = db.Column(db.Boolean, default=False)
    salary_range = db.Column(db.String(100))
    requirements = db.Column(db.Text)  # JSON string com requisitos
    modality = db.Column(db.String(50))  # híbrido, presencial, remoto
    job_type = db.Column(db.String(100))  # Analista financeiro, Contas a pagar, etc.
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'platform': self.platform,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'description': self.description,
            'applied_date': self.applied_date.isoformat() if self.applied_date else None,
            'status': self.status,
            'second_stage_check': self.second_stage_check,
            'salary_range': self.salary_range,
            'requirements': self.requirements,
            'modality': self.modality,
            'job_type': self.job_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

