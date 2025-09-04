from flask_sqlalchemy import SQLAlchemy
from src.models.user import db

class Credentials(db.Model):
    __tablename__ = 'credentials'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)  # LinkedIn, Infojobs, Catho, Gupy
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    google_linked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'username': self.username,
            'google_linked': self.google_linked,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

