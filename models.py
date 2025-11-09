# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ------------------------------------------------------------------
# ตาราง Project (เหมือนเดิม)
# ------------------------------------------------------------------
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    transactions = db.relationship('Transaction', backref='project_ref', lazy=True, cascade="all, delete-orphan")
    categories = db.relationship('Category', backref='project_ref', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description or 'ไม่มีคำอธิบาย'
        }

# ------------------------------------------------------------------
# ตาราง Category (เหมือนเดิม)
# ------------------------------------------------------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    type = db.Column(db.String(10), nullable=False) # 'Income' หรือ 'Expense'
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('name', 'project_id', name='_name_project_uc'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'project_id': self.project_id
        }

# ------------------------------------------------------------------
# ตาราง Transaction (ปรับปรุง)
# ------------------------------------------------------------------
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) # 🟢 ฟิลด์ใหม่
    type = db.Column(db.String(10), nullable=False) 
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False) 
    
    # 🟢 เพิ่ม 'category_ref' เพื่อให้ API ดึงข้อมูลได้ง่ายขึ้น
    category_ref = db.relationship('Category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date_recorded': self.date_recorded.isoformat(),
            'last_modified': self.last_modified.isoformat() if self.last_modified else None, # 🟢 ส่งฟิลด์ใหม่
            'type': self.type,
            'category_id': self.category_id,
            'category_name': self.category_ref.name if self.category_ref else 'N/A', 
            'project_id': self.project_id,
            'amount': self.amount,
            'description': self.description
        }

# ------------------------------------------------------------------
# 🟢 ตารางใหม่: AuditLog (บันทึกประวัติการดำเนินการ)
# ------------------------------------------------------------------
class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_name = db.Column(db.String(50), default='Admin') # 🟢 ใช้ชื่อ "Admin" ชั่วคราว
    action = db.Column(db.String(10), nullable=False) # 'CREATE', 'UPDATE', 'DELETE'
    table_name = db.Column(db.String(50), nullable=False) # 'Transaction', 'Category'
    record_id = db.Column(db.Integer, nullable=False) # ID ของรายการที่ถูกกระทำ
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False) # 🟢 ผูก Log กับ Project
    details = db.Column(db.Text, nullable=True) # รายละเอียดการเปลี่ยนแปลง

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'user_name': self.user_name,
            'action': self.action,
            'details': self.details
        }