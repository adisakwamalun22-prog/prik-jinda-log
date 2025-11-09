# models.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Transaction(db.Model):
    """
    ตารางสำหรับบันทึกรายการรายรับ-รายจ่ายของโครงการปลูกพริก
    """
    id = db.Column(db.Integer, primary_key=True)
    
    # วันที่และเวลา
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # ประเภทการทำรายการ: 'Income' (รายรับ) หรือ 'Expense' (รายจ่าย)
    type = db.Column(db.String(10), nullable=False) 
    
    # หมวดหมู่ (ใช้สำหรับวิเคราะห์)
    category = db.Column(db.String(50), nullable=False)
    
    # จำนวนเงิน
    amount = db.Column(db.Float, nullable=False)
    
    # คำอธิบาย
    description = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        """แปลง Object เป็น Dictionary เพื่อส่งกลับไปที่ Frontend ในรูปแบบ JSON"""
        return {
            'id': self.id,
            'date_recorded': self.date_recorded.isoformat(),
            'type': self.type,
            'category': self.category,
            'amount': self.amount,
            'description': self.description
        }
    
    def __repr__(self):
        return f"Transaction('{self.id}', '{self.type}', '{self.amount}')"