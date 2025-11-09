from extensions import db
from datetime import datetime

# ------------------------------------------------------------------
# ตาราง Project (รายการบัญชีหลัก)
# ------------------------------------------------------------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    transactions = db.relationship('Transaction', back_populates='project_ref', lazy=True, cascade="all, delete-orphan")
    categories = db.relationship('Category', back_populates='project_ref', lazy=True, cascade="all, delete-orphan")
    audit_logs = db.relationship('AuditLog', back_populates='project_ref', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or 'ไม่มีคำอธิบาย'
        }

# ------------------------------------------------------------------
# ตาราง Category (Master Data - เชื่อมกับ Project)
# ------------------------------------------------------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(10), nullable=False) 
    
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    project_ref = db.relationship('Project', back_populates='categories')
    transactions = db.relationship('Transaction', back_populates='category_ref', lazy=True, cascade="all, delete-orphan")
    
    __table_args__ = (db.UniqueConstraint('name', 'project_id', name='_name_project_uc'),)
    
    def to_dict(self):
        return { 'id': self.id, 'name': self.name, 'type': self.type, 'project_id': self.project_id }

# ------------------------------------------------------------------
# ตาราง Transaction (รายการ - เชื่อมกับ Project และ Category)
# ------------------------------------------------------------------
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    type = db.Column(db.String(10), nullable=False) 
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False) 
    
    project_ref = db.relationship('Project', back_populates='transactions')
    category_ref = db.relationship('Category', back_populates='transactions')

    def to_dict(self):
        category_name = self.category_ref.name if self.category_ref else 'N/A'
        
        return {
            'id': self.id, 
            'date_recorded': self.date_recorded.isoformat(), 
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'type': self.type, 
            'category_id': self.category_id, 
            'category_name': category_name, 
            'project_id': self.project_id, 
            'amount': self.amount, 
            'description': self.description
        }

# ------------------------------------------------------------------
# ตาราง AuditLog (บันทึกประวัติการดำเนินการ)
# ------------------------------------------------------------------
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_name = db.Column(db.String(50), default='Admin')
    action = db.Column(db.String(10), nullable=False) 
    table_name = db.Column(db.String(50), nullable=False) 
    record_id = db.Column(db.Integer, nullable=True) 
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False) 
    details = db.Column(db.Text, nullable=True) 

    project_ref = db.relationship('Project', back_populates='audit_logs')

    def to_dict(self):
        return {
            'id': self.id, 
            'timestamp': self.timestamp.isoformat(), 
            'user_name': self.user_name,
            'action': self.action, 
            'table_name': self.table_name,
            'record_id': self.record_id,
            'project_id': self.project_id,
            'details': self.details
        }