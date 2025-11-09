# app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Transaction
import os

# การตั้งค่าแอปพลิเคชัน
app = Flask(__name__)

# ตั้งค่าฐานข้อมูล SQLite: จะสร้างไฟล์ site.db ในโฟลเดอร์เดียวกัน
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# เริ่มต้นการใช้งานฐานข้อมูลกับแอป Flask
db.init_app(app)

# ===============================================
# 🛠️ ฟังก์ชันสำหรับสร้างฐานข้อมูล (รันครั้งแรกเท่านั้น)
# ===============================================

# ใช้ Context Manager เพื่อสร้างตารางในฐานข้อมูล
with app.app_context():
    # ถ้าไฟล์ site.db ยังไม่มีอยู่ จะทำการสร้างฐานข้อมูลและตาราง
    if not os.path.exists('site.db'):
        db.create_all()
        print("Database 'site.db' created and tables initialized.")

# ===============================================
# 🌐 Routes: ส่วนสำหรับให้บริการหน้าจอหลักและ API
# ===============================================

@app.route('/')
def index():
    """แสดงหน้าจอหลักของแอป (Frontend)"""
    return render_template('index.html')

@app.route('/api/transactions', methods=['GET', 'POST'])
def transactions_api():
    """จัดการ API สำหรับดึงและบันทึกรายการ"""
    
    # GET: ดึงรายการทั้งหมด
    if request.method == 'GET':
        # ดึงรายการทั้งหมดจากฐานข้อมูล และเรียงตามวันที่ล่าสุด
        transactions = Transaction.query.order_by(Transaction.date_recorded.desc()).all()
        # แปลงข้อมูลเป็นรูปแบบ JSON
        return jsonify([t.to_dict() for t in transactions])

    # POST: บันทึกรายการใหม่
    elif request.method == 'POST':
        data = request.get_json()
        
        # ตรวจสอบว่ามีข้อมูลที่จำเป็นครบถ้วนหรือไม่
        if not all(k in data for k in ('type', 'category', 'amount')):
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            new_transaction = Transaction(
                type=data['type'],
                category=data['category'],
                amount=float(data['amount']),
                description=data.get('description', '') # หากไม่มี description ให้เป็นค่าว่าง
                # date_recorded จะใช้ค่า default คือเวลาปัจจุบัน
            )
            db.session.add(new_transaction)
            db.session.commit()
            return jsonify({'message': 'Transaction added successfully', 'transaction': new_transaction.to_dict()}), 201
        
        except ValueError:
            return jsonify({'message': 'Invalid amount format'}), 400
        except Exception as e:
            return jsonify({'message': f'An error occurred: {e}'}), 500

@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """จัดการ API สำหรับลบรายการ"""
    
    transaction_to_delete = Transaction.query.get_or_404(transaction_id)
    
    try:
        db.session.delete(transaction_to_delete)
        db.session.commit()
        return jsonify({'message': f'Transaction ID {transaction_id} deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to delete transaction: {e}'}), 500

# ===============================================
# 🚀 รันแอปพลิเคชัน
# ===============================================

if __name__ == '__main.main__':
    # รันบนเครื่อง localhost:5000 (ในโหมด Debug)
    app.run(debug=True)