# app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Transaction, Category # 🟢 Import Category
from sqlalchemy.exc import IntegrityError
import os

# การตั้งค่าแอปพลิเคชัน
app = Flask(__name__)

# ตั้งค่าฐานข้อมูล SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ===============================================
# 🛠️ ฟังก์ชันสำหรับสร้างฐานข้อมูลและเพิ่ม Master Data เริ่มต้น
# ===============================================

with app.app_context():
    # ถ้าไฟล์ site.db ยังไม่มีอยู่ จะทำการสร้างฐานข้อมูลและตาราง
    if not os.path.exists('site.db'):
        db.create_all()
        print("Database 'site.db' created and tables initialized.")
    else:
        # 💡 สำคัญ: เนื่องจากเราเพิ่มตาราง Category การรัน db.create_all() ซ้ำ
        # อาจทำให้เกิดปัญหาถ้าโครงสร้างเก่ามีข้อมูลอยู่แล้ว
        # ในสภาพแวดล้อมจริง ควรใช้ Flask Migrate (Alembic)
        # แต่สำหรับโปรเจกต์นี้ เราจะใช้ db.create_all() เพื่อให้มั่นใจว่าตาราง Category ถูกสร้าง
        db.create_all() 

    # 🟢 เพิ่ม Master Data เริ่มต้น (ถ้ายังไม่มี)
    if Category.query.count() == 0:
        initial_categories = [
            {'name': 'ยอดขายพริก', 'type': 'Income'},
            {'name': 'เงินสนับสนุน', 'type': 'Income'},
            {'name': 'ค่าเมล็ดพันธุ์', 'type': 'Expense'},
            {'name': 'ค่าปุ๋ย/ยา', 'type': 'Expense'},
            {'name': 'ค่าแรงงาน', 'type': 'Expense'},
            {'name': 'ค่าน้ำมัน/ไฟฟ้า', 'type': 'Expense'},
        ]
        for cat in initial_categories:
            new_cat = Category(name=cat['name'], type=cat['type'])
            db.session.add(new_cat)
        try:
            db.session.commit()
            print("Initial Categories added.")
        except IntegrityError:
            db.session.rollback()
            print("Initial Categories already exist.")


# ===============================================
# 🌐 Routes: ส่วนสำหรับให้บริการหน้าจอหลัก
# ===============================================

@app.route('/')
def index():
    """แสดงหน้าจอหลักของแอป (Frontend)"""
    return render_template('index.html')

# ===============================================
# 🟢 API: Categories (Master Data)
# ===============================================

@app.route('/api/categories', methods=['GET', 'POST'])
def categories_api():
    """จัดการ API สำหรับดึงและเพิ่มหมวดหมู่"""
    
    # GET: ดึงรายการทั้งหมด
    if request.method == 'GET':
        categories = Category.query.order_by(Category.name).all()
        return jsonify([c.to_dict() for c in categories])

    # POST: เพิ่มหมวดหมู่ใหม่
    elif request.method == 'POST':
        data = request.get_json()
        if not all(k in data for k in ('name', 'type')):
            return jsonify({'message': 'Missing required fields (name, type)'}), 400
        
        try:
            new_category = Category(
                name=data['name'].strip(),
                type=data['type'].strip()
            )
            db.session.add(new_category)
            db.session.commit()
            return jsonify({'message': 'Category added successfully', 'category': new_category.to_dict()}), 201
        
        except IntegrityError:
            db.session.rollback()
            return jsonify({'message': 'Category name already exists.'}), 409 # Conflict
        except Exception as e:
            return jsonify({'message': f'An error occurred: {e}'}), 500

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """จัดการ API สำหรับลบหมวดหมู่"""
    
    category_to_delete = Category.query.get_or_404(category_id)
    
    # 💡 ตรวจสอบว่ามี Transaction ที่อ้างอิงหมวดหมู่นี้อยู่หรือไม่
    if category_to_delete.transactions.count() > 0:
        return jsonify({'message': 'Cannot delete category: related transactions exist.'}), 409
    
    try:
        db.session.delete(category_to_delete)
        db.session.commit()
        return jsonify({'message': f'Category ID {category_id} deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Failed to delete category: {e}'}), 500


# ===============================================
# 🌐 API: Transactions (ปรับปรุงให้ใช้ category_id)
# ===============================================

@app.route('/api/transactions', methods=['GET', 'POST'])
def transactions_api():
    """จัดการ API สำหรับดึงและบันทึกรายการ"""
    
    # GET: ดึงรายการทั้งหมด
    if request.method == 'GET':
        transactions = Transaction.query.order_by(Transaction.date_recorded.desc()).all()
        # 🟢 ดึงชื่อหมวดหมู่ผ่าน relationship ใน to_dict()
        return jsonify([t.to_dict() for t in transactions])

    # POST: บันทึกรายการใหม่
    elif request.method == 'POST':
        data = request.get_json()
        
        # 🟢 ตรวจสอบ category_id แทน category name
        if not all(k in data for k in ('type', 'category_id', 'amount')):
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            # 💡 ตรวจสอบว่า category_id มีอยู่จริง
            category_id = int(data['category_id'])
            if not Category.query.get(category_id):
                 return jsonify({'message': 'Invalid category ID.'}), 400

            new_transaction = Transaction(
                type=data['type'],
                category_id=category_id, # 🟢 ใช้ ID
                amount=float(data['amount']),
                description=data.get('description', '')
            )
            db.session.add(new_transaction)
            db.session.commit()
            return jsonify({'message': 'Transaction added successfully', 'transaction': new_transaction.to_dict()}), 201
        
        except ValueError:
            return jsonify({'message': 'Invalid amount or category ID format'}), 400
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

if __name__ == '__main__': 
    # รันบนเครื่อง localhost:5000 (ในโหมด Debug)
    app.run(debug=True)