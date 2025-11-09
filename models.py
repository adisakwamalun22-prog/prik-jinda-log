# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ------------------------------------------------------------------
# ตารางใหม่: Project (รายการบัญชีหลัก)
# ------------------------------------------------------------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    # ความสัมพันธ์ไปยัง Transactions และ Categories
    transactions = db.relationship('Transaction', backref='project_ref', lazy=True, cascade="all, delete-orphan")
    categories = db.relationship('Category', backref='project_ref', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or 'ไม่มีคำอธิบาย'
        }
    
    def __repr__(self):
        return f"Project('{self.name}')"


# ------------------------------------------------------------------
# ตาราง Category (Master Data - เชื่อมกับ Project)
# ------------------------------------------------------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'Income' หรือ 'Expense'
    
    # Foreign Key: ผูกกับ Project
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # Unique Constraint: ชื่อหมวดหมู่ต้องไม่ซ้ำกันในโครงการเดียวกัน
    __table_args__ = (db.UniqueConstraint('name', 'project_id', name='_name_project_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'project_id': self.project_id
        }

# ------------------------------------------------------------------
# ตาราง Transaction (รายการ - เชื่อมกับ Project และ Category)
# ------------------------------------------------------------------
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    type = db.Column(db.String(10), nullable=False) 
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    # Foreign Key: ผูกกับ Project
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    
    # Foreign Key: ผูกกับ Category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False) 
    
    def to_dict(self):
        return {
            'id': self.id,
            'date_recorded': self.date_recorded.isoformat(),
            'type': self.type,
            'category_id': self.category_id,
            'category_name': self.category_ref.name, 
            'project_id': self.project_id,
            'project_name': self.project_ref.name,
            'amount': self.amount,
            'description': self.description
        }