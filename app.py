# app.py

from dotenv import load_dotenv
load_dotenv() # 🟢 นี่คือคำสั่งให้อ่านไฟล์ .env (ต้องอยู่บนสุด)

from flask import Flask, render_template, request, jsonify
from extensions import db  # 🟢 Import db จาก extensions
from models import Project, Category, Transaction, AuditLog
from sqlalchemy.exc import IntegrityError
import os 

def create_app():
    """
    Application Factory: สร้างและกำหนดค่าแอป Flask
    """
    app = Flask(__name__)

    # --- Database Configuration ---
    # 🟢 ย้าย Config ทั้งหมดเข้ามาใน Factory
    DATABASE_URL = os.environ.get('DATABASE_URL') 
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 🟢 เริ่มต้น DB กับแอป
    db.init_app(app) 

    # ===============================================
    # 🛠️ ฟังก์ชันสำหรับสร้างฐานข้อมูล
    # ===============================================
    @app.before_request
    def create_tables():
        if not hasattr(app, 'tables_created'):
            with app.app_context():
                db.create_all()
            app.tables_created = True # ตั้ง flag ว่าสร้างแล้ว

    # ===============================================
    # 🟢 ฟังก์ชัน Helper: สำหรับบันทึก Log
    # ===============================================
    def log_action(action, table_name, project_id, record_id=None, details=None, user='Admin'):
        try:
            new_log = AuditLog(
                action=action, table_name=table_name, record_id=record_id,
                project_id=project_id, details=details, user_name=user
            )
            db.session.add(new_log)
        except Exception as e:
            print(f"Error logging action: {e}")

    # ===============================================
    # 🌐 Routes: ส่วนสำหรับให้บริการหน้าจอหลัก
    # ===============================================
    @app.route('/')
    def index():
        return render_template('index.html')

    # ===============================================
    # 🟢 API: Projects (Full CRUD)
    # ===============================================
    @app.route('/api/projects', methods=['GET', 'POST'])
    def projects_api():
        if request.method == 'GET':
            projects = Project.query.order_by(Project.name).all()
            return jsonify([p.to_dict() for p in projects])

        elif request.method == 'POST':
            data = request.get_json()
            if not data or 'name' not in data or not data['name']:
                return jsonify({'message': 'Project name is required.'}), 400
            
            try:
                new_project = Project(name=data['name'].strip(), description=data.get('description', ''))
                db.session.add(new_project)
                db.session.commit()
                
                log_action('CREATE', 'Project', new_project.id, new_project.id, f"Project '{new_project.name}' created.")

                initial_categories = [
                    {'name': 'ยอดขาย', 'type': 'Income'},
                    {'name': 'ค่าใช้จ่ายทั่วไป', 'type': 'Expense'},
                ]
                for cat in initial_categories:
                    db.session.add(Category(name=cat['name'], type=cat['type'], project_id=new_project.id))
                
                log_action('CREATE', 'Category', new_project.id, None, "Initial categories created.")
                db.session.commit()
                return jsonify({'message': 'Project created successfully', 'project': new_project.to_dict()}), 201
            
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'Project name already exists.'}), 409
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': f'An error occurred: {e}'}), 500

    @app.route('/api/projects/<int:project_id>', methods=['PUT', 'DELETE'])
    def project_detail_api(project_id):
        project = Project.query.get_or_404(project_id)
        
        if request.method == 'PUT':
            data = request.get_json()
            if not data or 'name' not in data or not data['name']:
                return jsonify({'message': 'Project name is required.'}), 400
            
            old_name = project.name
            old_desc = project.description
            
            try:
                project.name = data['name'].strip()
                project.description = data.get('description', '')
                
                details = f"Project name: '{old_name}' -> '{project.name}', Desc: '{old_desc}' -> '{project.description}'"
                log_action('UPDATE', 'Project', project_id, project_id, details)
                
                db.session.commit()
                return jsonify({'message': 'Project updated.', 'project': project.to_dict()}), 200
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'Project name already exists.'}), 409
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': f'An error occurred: {e}'}), 500

        elif request.method == 'DELETE':
            try:
                log_action('DELETE', 'Project', project_id, project_id, f"Project '{project.name}' and all related data deleted.")
                db.session.delete(project)
                db.session.commit()
                return jsonify({'message': 'Project deleted successfully.'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': f'An error occurred: {e}'}), 500


    # ===============================================
    # 🟢 API: Categories (Full CRUD)
    # ===============================================
    @app.route('/api/projects/<int:project_id>/categories', methods=['GET', 'POST'])
    def categories_api(project_id):
        Project.query.get_or_404(project_id)
        
        if request.method == 'GET':
            categories = Category.query.filter_by(project_id=project_id).order_by(Category.type, Category.name).all()
            return jsonify([c.to_dict() for c in categories])

        elif request.method == 'POST':
            data = request.get_json()
            if not all(k in data for k in ('name', 'type')):
                return jsonify({'message': 'Missing fields (name, type)'}), 400
            
            try:
                new_category = Category(name=data['name'].strip(), type=data['type'], project_id=project_id)
                db.session.add(new_category)
                db.session.commit()
                log_action('CREATE', 'Category', project_id, new_category.id, f"Category '{new_category.name}' created.")
                db.session.commit()
                return jsonify(new_category.to_dict()), 201
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'Category name already exists in this project.'}), 409
            except Exception as e:
                return jsonify({'message': f'An error occurred: {e}'}), 500

    @app.route('/api/categories/<int:category_id>', methods=['PUT', 'DELETE'])
    def category_detail_api(category_id):
        category = Category.query.get_or_404(category_id)
        project_id = category.project_id

        if request.method == 'PUT':
            data = request.get_json()
            if not data or 'name' not in data or not data['name']:
                return jsonify({'message': 'Category name is required.'}), 400
            
            try:
                old_name = category.name
                category.name = data['name'].strip()
                log_action('UPDATE', 'Category', project_id, category_id, f"Category name: '{old_name}' -> '{category.name}'")
                db.session.commit()
                return jsonify(category.to_dict()), 200
            except IntegrityError:
                db.session.rollback()
                return jsonify({'message': 'Category name already exists in this project.'}), 409
            except Exception as e:
                return jsonify({'message': f'An error occurred: {e}'}), 500

        elif request.method == 'DELETE':
            try:
                if Transaction.query.filter_by(category_id=category_id).first():
                    return jsonify({'message': 'Cannot delete category: It is currently in use by transactions.'}), 409

                log_action('DELETE', 'Category', project_id, category_id, f"Category '{category.name}' deleted.")
                db.session.delete(category)
                db.session.commit()
                return jsonify({'message': 'Category deleted.'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': f'An error occurred: {e}'}), 500

    # ===============================================
    # 🟢 API: Transactions (Full CRUD)
    # ===============================================
    @app.route('/api/projects/<int:project_id>/transactions', methods=['GET', 'POST'])
    def transactions_api(project_id):
        Project.query.get_or_404(project_id)
        
        if request.method == 'GET':
            transactions = Transaction.query.filter_by(project_id=project_id).order_by(Transaction.date_recorded.desc()).all()
            return jsonify([t.to_dict() for t in transactions])

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
                db.session.commit()
                log_action('CREATE', 'Transaction', project_id, new_transaction.id, f"Amount: {new_transaction.amount}, Desc: {new_transaction.description}")
                db.session.commit()
                return jsonify(new_transaction.to_dict()), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': f'An error occurred: {e}'}), 500

    @app.route('/api/transactions/<int:transaction_id>', methods=['PUT', 'DELETE'])
    def transaction_detail_api(transaction_id):
        transaction = Transaction.query.get_or_404(transaction_id)
        project_id = transaction.project_id

        if request.method == 'PUT':
            data = request.get_json()
            changes = []
            try:
                if 'type' in data and data['type'] != transaction.type:
                    changes.append(f"Type: {transaction.type} -> {data['type']}")
                    transaction.type = data['type']
                if 'amount' in data and float(data['amount']) != transaction.amount:
                    changes.append(f"Amount: {transaction.amount} -> {data['amount']}")
                    transaction.amount = float(data['amount'])
                if 'category_id' in data and int(data['category_id']) != transaction.category_id:
                    new_cat_id = int(data['category_id'])
                    category = Category.query.filter_by(id=new_cat_id, project_id=project_id).first()
                    if not category:
                         return jsonify({'message': 'Invalid category ID.'}), 400
                    changes.append(f"Category: {transaction.category_ref.name} -> {category.name}")
                    transaction.category_id = new_cat_id
                if 'description' in data and data['description'] != transaction.description:
                    changes.append(f"Desc: '{transaction.description}' -> '{data['description']}'")
                    transaction.description = data['description']

                if changes:
                    log_action('UPDATE', 'Transaction', project_id, transaction.id, '; '.join(changes))
                    db.session.commit()
                    return jsonify(transaction.to_dict()), 200
                else:
                    return jsonify({'message': 'No changes detected.'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': f'An error occurred: {e}'}), 500

        elif request.method == 'DELETE':
            try:
                log_action('DELETE', 'Transaction', project_id, transaction.id, f"Deleted item (Amount: {transaction.amount})")
                db.session.delete(transaction)
                db.session.commit()
                return jsonify({'message': 'Transaction deleted.'}), 200
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': f'An error occurred: {e}'}), 500

    # ===============================================
    # 🟢 API: Audit Log
    # ===============================================
    @app.route('/api/projects/<int:project_id>/logs', methods=['GET'])
    def audit_log_api(project_id):
        Project.query.get_or_404(project_id)
        logs = AuditLog.query.filter_by(project_id=project_id).order_by(AuditLog.timestamp.desc()).limit(100).all()
        return jsonify([log.to_dict() for log in logs])

    # ===============================================
    # 🚀 Return App
    # ===============================================
    return app

# 🟢 หมายเหตุ: เราไม่รัน app.run() ที่นี่ Gunicorn จะเรียก create_app() เอง