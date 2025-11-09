# app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Transaction, Category, Project, AuditLog # 🟢 Import AuditLog
from sqlalchemy.exc import IntegrityError
import os

# การตั้งค่าแอปพลิเคชัน
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# ===============================================
# 🛠️ ฟังก์ชันสำหรับสร้างฐานข้อมูล
# ===============================================

with app.app_context():
    # 💡 สำคัญ: รัน db.create_all() เพื่อสร้างตาราง AuditLog ใหม่
    db.create_all()

# ===============================================
# 🟢 ฟังก์ชัน Helper: สำหรับบันทึก Log
# ===============================================
def log_action(action, table_name, record_id, project_id, details=None, user='Admin'):
    """ฟังก์ชันช่วยบันทึกการกระทำลง AuditLog"""
    try:
        new_log = AuditLog(
            action=action,
            table_name=table_name,
            record_id=record_id,
            project_id=project_id,
            details=details,
            user_name=user
        )
        db.session.add(new_log)
    except Exception as e:
        print(f"Error logging action: {e}")
        # (ในระบบจริง ควรจัดการ Error นี้)


# ===============================================
# 🌐 Routes: ส่วนสำหรับให้บริการหน้าจอหลัก (Project List)
# ===============================================

@app.route('/')
def index():
    """แสดงหน้าจอหลัก (รายการโครงการ)"""
    return render_template('index.html')


# ===============================================
# 🟢 API: Projects (เพิ่มการบันทึก Log)
# ===============================================

@app.route('/api/projects', methods=['GET', 'POST'])
def projects_api():
    """จัดการ API สำหรับดึงและเพิ่มโครงการ"""
    
    if request.method == 'GET':
        projects = Project.query.order_by(Project.name).all()
        return jsonify([p.to_dict() for p in projects])

    elif request.method == 'POST':
        # (โค้ด POST Project เหมือนเดิม)
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
            
            # 🟢 บันทึก Log การสร้าง Project
            log_action('CREATE', 'Project', new_project.id, new_project.id, details=f"Project '{new_project.name}' created.")

            # (โค้ดเพิ่ม Master Data เริ่มต้นเหมือนเดิม)
            initial_categories = [
                {'name': 'ยอดขายพริก', 'type': 'Income'},
                {'name': 'ค่าเมล็ดพันธุ์', 'type': 'Expense'},
                {'name': 'ค่าปุ๋ย/ยา', 'type': 'Expense'},
            ]
            for cat in initial_categories:
                new_cat = Category(name=cat['name'], type=cat['type'], project_id=new_project.id)
                db.session.add(new_cat)
            
            # 🟢 บันทึก Log การสร้าง Category เริ่มต้น
            log_action('CREATE', 'Category', new_project.id, new_project.id, details="Initial categories created.")
            
            db.session.commit()
            return jsonify({'message': 'Project created successfully', 'project': new_project.to_dict()}), 201
        
        except IntegrityError:
            db.session.rollback()
            return jsonify({'message': 'Project name already exists.'}), 409
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'An error occurred: {e}'}), 500


# ===============================================
# 🟢 API: Categories (เพิ่มการบันทึก Log)
# ===============================================

@app.route('/api/projects/<int:project_id>/categories', methods=['GET', 'POST'])
def categories_api(project_id):
    """จัดการ API สำหรับดึงและเพิ่มหมวดหมู่ของโครงการนั้น"""
    
    project = Project.query.get_or_404(project_id)

    if request.method == 'GET':
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
                project_id=project_id 
            )
            db.session.add(new_category)
            db.session.commit()

            # 🟢 บันทึก Log
            log_action('CREATE', 'Category', new_category.id, project_id, details=f"Category '{new_category.name}' added.")
            db.session.commit()

            return jsonify({'message': 'Category added successfully', 'category': new_category.to_dict()}), 201
        
        except IntegrityError:
            db.session.rollback()
            return jsonify({'message': 'Category name already exists in this project.'}), 409
        except Exception as e:
            return jsonify({'message': f'An error occurred: {e}'}), 500


# ===============================================
# 🟢 API: Transactions (เพิ่มการบันทึก Log และ PUT)
# ===============================================

@app.route('/api/projects/<int:project_id>/transactions', methods=['GET', 'POST'])
def transactions_api(project_id):
    """จัดการ API สำหรับดึงและบันทึกรายการของโครงการนั้น"""

    project = Project.query.get_or_404(project_id)
    
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
            if not Category.query.filter_by(id=category_id, project_id=project_id).first():
                 return jsonify({'message': 'Invalid category ID.'}), 400

            new_transaction = Transaction(
                type=data['type'],
                category_id=category_id, 
                project_id=project_id,
                amount=float(data['amount']),
                description=data.get('description', '')
            )
            db.session.add(new_transaction)
            db.session.commit() # Commit เพื่อรับ ID

            # 🟢 บันทึก Log การสร้าง
            log_action('CREATE', 'Transaction', new_transaction.id, project_id, details=f"Amount: {new_transaction.amount}, Category ID: {category_id}")
            db.session.commit() # Commit Log

            return jsonify({'message': 'Transaction added successfully', 'transaction': new_transaction.to_dict()}), 201
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'An error occurred: {e}'}), 500


@app.route('/api/transactions/<int:transaction_id>', methods=['PUT', 'DELETE'])
def transaction_detail_api(transaction_id):
    """🟢 API ใหม่: จัดการ แก้ไข (PUT) และ ลบ (DELETE)"""
    
    transaction = Transaction.query.get_or_404(transaction_id)
    project_id = transaction.project_id # ดึง Project ID สำหรับ Log

    # ---------------------------------
    # 🟢 PUT: การแก้ไขรายการ
    # ---------------------------------
    if request.method == 'PUT':
        data = request.get_json()
        changes = [] # เก็บรายการเปลี่ยนแปลงสำหรับ Log
        
        try:
            # ตรวจสอบและอัปเดตแต่ละฟิลด์
            if 'type' in data and data['type'] != transaction.type:
                changes.append(f"Type: {transaction.type} -> {data['type']}")
                transaction.type = data['type']
                
            if 'amount' in data and float(data['amount']) != transaction.amount:
                changes.append(f"Amount: {transaction.amount} -> {data['amount']}")
                transaction.amount = float(data['amount'])

            if 'category_id' in data and int(data['category_id']) != transaction.category_id:
                new_cat_id = int(data['category_id'])
                # ตรวจสอบว่า Category ID ใหม่ อยู่ใน Project เดียวกัน
                if not Category.query.filter_by(id=new_cat_id, project_id=project_id).first():
                     return jsonify({'message': 'Invalid category ID.'}), 400
                
                changes.append(f"Category ID: {transaction.category_id} -> {new_cat_id}")
                transaction.category_id = new_cat_id

            if 'description' in data and data['description'] != transaction.description:
                changes.append(f"Desc: '{transaction.description}' -> '{data['description']}'")
                transaction.description = data['description']

            if changes:
                # 🟢 บันทึก Log การแก้ไข
                log_action(
                    action='UPDATE', 
                    table_name='Transaction', 
                    record_id=transaction.id, 
                    project_id=project_id,
                    details='; '.join(changes)
                )
                db.session.commit()
                return jsonify({'message': 'Transaction updated successfully', 'transaction': transaction.to_dict()}), 200
            else:
                return jsonify({'message': 'No changes detected.'}), 200 # ไม่มีการเปลี่ยนแปลง
                
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'Failed to update transaction: {e}'}), 500

    # ---------------------------------
    # 🟢 DELETE: การลบรายการ
    # ---------------------------------
    elif request.method == 'DELETE':
        try:
            # 🟢 บันทึก Log การลบ (ก่อนลบจริง)
            log_action(
                action='DELETE', 
                table_name='Transaction', 
                record_id=transaction.id, 
                project_id=project_id,
                details=f"Deleted item. Amount: {transaction.amount}, Desc: {transaction.description}"
            )
            
            db.session.delete(transaction_to_delete)
            db.session.commit()
            return jsonify({'message': f'Transaction ID {transaction_id} deleted successfully'}), 200
        
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': f'Failed to delete transaction: {e}'}), 500

# ===============================================
# 🟢 API: Audit Log (สำหรับแสดงผลใน Frontend)
# ===============================================
@app.route('/api/projects/<int:project_id>/logs', methods=['GET'])
def audit_log_api(project_id):
    """ดึง Audit Log ทั้งหมดที่เกี่ยวข้องกับ Project นี้"""
    
    project = Project.query.get_or_404(project_id)
    
    logs = AuditLog.query.filter_by(project_id=project_id).order_by(AuditLog.timestamp.desc()).limit(50).all()
    return jsonify([log.to_dict() for log in logs])


# ===============================================
# 🚀 รันแอปพลิเคชัน
# ===============================================

if __name__ == '__main__': 
    app.run(debug=True)