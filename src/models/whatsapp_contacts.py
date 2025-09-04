from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class WhatsAppContact(db.Model):
    __tablename__ = 'whatsapp_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.String(255), nullable=False, unique=True)
    company = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    last_contact_date = db.Column(db.DateTime)
    message_type = db.Column(db.String(50))  # 'company_request', 'hr_presentation'
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=True)
    contact_source = db.Column(db.String(100))  # LinkedIn, Google, etc.
    status = db.Column(db.String(50), default='pending')  # pending, sent, error
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    # Relacionamento com Job
    job = db.relationship('Job', backref='whatsapp_contacts', foreign_keys=[job_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'contact_id': self.contact_id,
            'company': self.company,
            'phone_number': self.phone_number,
            'last_contact_date': self.last_contact_date.isoformat() if self.last_contact_date else None,
            'message_type': self.message_type,
            'job_id': self.job_id,
            'contact_source': self.contact_source,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

