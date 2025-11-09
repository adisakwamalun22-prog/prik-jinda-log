# app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Transaction, Category, Project
from sqlalchemy.exc import IntegrityError
import os

# การตั้งค่าแอปพลิเคชัน
app = Flask(__name__)

# ตั้งค่าฐานข้อมูล SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ===============================================
# 🛠️ ฟังก์ชันสำหรับสร้างฐานข้อมูล
# ===============================================

with app.app_context():
    # 💡 สำคัญ: เนื่องจากมีการเปลี่ยนโครงสร้างหลัก เราจะรัน db.create_all() 
    # เพื่อสร้างตาราง Project, Category, Transaction ใหม่
    db.create_all()


# ===============================================
# 🌐 Routes: ส่วนสำหรับให้บริการหน้าจอหลัก (Project List)
# ===============================================

@app.route('/')
def index():
    """แสดงหน้าจอหลัก (รายการโครงการ)"""
    return render_template('index.html')


# ===============================================
# 🟢 API: Projects (สร้าง/ดึงโครงการ)
# ===============================================

@app.route('/api/projects', methods=['GET', 'POST'])
def projects_api():
    """จัดการ API สำหรับดึงและเพิ่มโครงการ"""
    
    if request.method == 'GET':
        projects = Project.query.order_by(Project.name).all()
        return jsonify([p.to_dict() for p in projects])

    elif request.method == 'POST':
        data = request.get_json()
        if not 'name' in data:
            return jsonify({'message': 'Missing required field: name'}), 400
        
        try:
            new_project = Project(
                name=data['name'].strip(),
                description=data.get('description', '')
            )
            db.session.add(new_project)
            db.session.commit()
            
            # 💡 เมื่อสร้างโครงการแล้ว ให้เพิ่ม Master Data เริ่มต้นให้โครงการนั้นทันที
            initial_categories = [
                {'name': 'ยอดขายพริก', 'type': 'Income'},
                {'name': 'ค่าเมล็ดพันธุ์', 'type': 'Expense'},
                {'name': 'ค่าปุ๋ย/ยา', 'type': 'Expense'},
            ]
            for cat in initial_categories:
                new_cat = Category(name=cat['name'], type=cat['type'], project_id=new_project.id)
                db.session.add(new_cat)
            db.session.commit()

            return jsonify({'message': 'Project created successfully', 'project': new_project.to_dict()}), 201
        
        except IntegrityError:
            db.session.rollback()
            return jsonify({'message': 'Project name already exists.'}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'An error occurred: {e}'}), 500


# ===============================================
# 🟢 API: Categories (Master Data - อ้างอิง Project)
# ===============================================

@app.route('/api/projects/<int:project_id>/categories', methods=['GET', 'POST'])
def categories_api(project_id):
    """จัดการ API สำหรับดึงและเพิ่มหมวดหมู่ของโครงการนั้น"""
    
    if not Project.query.get(project_id):
        return jsonify({'message': 'Project not found.'}), 404

    if request.method == 'GET':
        # ดึงเฉพาะหมวดหมู่ของ project_id ที่ระบุ
        categories = Category.query.filter_by(project_id=project_id).order_by(Category.name).all()
        return jsonify([c.to_dict() for c in categories])

    elif request.method == 'POST':
        data = request.get_json()
        if not all(k in data for k in ('name', 'type')):
            return jsonify({'message': 'Missing required fields (name, type)'}), 400
        
        try:
            new_category = Category(
                name=data['name'].strip(),
                type=data['type'].strip(),
                project_id=project_id # 🟢 ผูกกับ Project ID
            )
            db.session.add(new_category)
            db.session.commit()
            return jsonify({'message': 'Category added successfully', 'category': new_category.to_dict()}), 201
        
        except IntegrityError:
            db.session.rollback()
            return jsonify({'message': 'Category name already exists in this project.'}), 409
        except Exception as e:
            return jsonify({'message': f'An error occurred: {e}'}), 500


# ===============================================
# 🌐 API: Transactions (อ้างอิง Project)
# ===============================================

@app.route('/api/projects/<int:project_id>/transactions', methods=['GET', 'POST'])
def transactions_api(project_id):
    """จัดการ API สำหรับดึงและบันทึกรายการของโครงการนั้น"""

    if not Project.query.get(project_id):
        return jsonify({'message': 'Project not found.'}), 404
    
    # GET: ดึงรายการทั้งหมดของโครงการนั้น
    if request.method == 'GET':
        transactions = Transaction.query.filter_by(project_id=project_id).order_by(Transaction.date_recorded.desc()).all()
        return jsonify([t.to_dict() for t in transactions])

    # POST: บันทึกรายการใหม่ของโครงการนั้น
    elif request.method == 'POST':
        data = request.get_json()
        
        if not all(k in data for k in ('type', 'category_id', 'amount')):
            return jsonify({'message': 'Missing required fields'}), 400

        try:
            category_id = int(data['category_id'])
            # ตรวจสอบว่า Category ID นั้นมีอยู่จริงและอยู่ในโครงการนี้จริงหรือไม่
            if not Category.query.filter_by(id=category_id, project_id=project_id).first():
                 return jsonify({'message': 'Invalid category ID or category does not belong to this project.'}), 400

            new_transaction = Transaction(
                type=data['type'],
                category_id=category_id, 
                project_id=project_id, # 🟢 ผูกกับ Project ID
                amount=float(data['amount']),
                description=data.get('description', '')
            )
            db.session.add(new_transaction)
            db.session.commit()
            return jsonify({'message': 'Transaction added successfully', 'transaction': new_transaction.to_dict()}), 201
        
        except Exception as e:
            db.session.rollback()
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
    app.run(debug=True)