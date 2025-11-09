# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ------------------------------------------------------------------
# ตารางใหม่: Categories (Master Data)
# ------------------------------------------------------------------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False) # ชื่อหมวดหมู่ (ต้องไม่ซ้ำ)
    type = db.Column(db.String(10), nullable=False) # 'Income' หรือ 'Expense'
    
    # กำหนดความสัมพันธ์ (Relationship) เพื่อดึงรายการ Transactions ที่อ้างอิงหมวดหมู่นี้
    transactions = db.relationship('Transaction', backref='category_ref', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type
        }
    
    def __repr__(self):
        return f"Category('{self.name}', '{self.type}')"

# ------------------------------------------------------------------
# ตาราง Transaction (ปรับปรุง)
# ------------------------------------------------------------------
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    type = db.Column(db.String(10), nullable=False) 
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)

    # 🟢 ใช้ Foreign Key อ้างอิงตาราง Category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False) 
    
    def to_dict(self):
        return {
            'id': self.id,
            'date_recorded': self.date_recorded.isoformat(),
            'type': self.type,
            'category_id': self.category_id,
            'category_name': self.category_ref.name, # ดึงชื่อหมวดหมู่ผ่าน relationship
            'amount': self.amount,
            'description': self.description
        }
    
    def __repr__(self):
        return f"Transaction('{self.id}', '{self.type}', '{self.amount}')"