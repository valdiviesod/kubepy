from flask import request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token
from model.user import User
from database.db import db

bcrypt = Bcrypt()

def register():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400
    
    # Asigna el rol 'undefined' automáticamente
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, password=hashed_password, role='undefined')
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully"}), 201

def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token, role=user.role), 200
    
    return jsonify({"msg": "Invalid username or password"}), 401

def change_role():
    current_user = get_jwt_identity()
    user_to_update = request.json.get('user_id', None)
    new_role = request.json.get('role', None)
    
    # Verifica que el usuario autenticado tiene el rol admin
    current_user_obj = User.query.filter_by(username=current_user).first()
    if current_user_obj.role != 'admin':
        return jsonify({"msg": "Permission denied"}), 403
    
    if not user_to_update or not new_role:
        return jsonify({"msg": "Missing username or role"}), 400
    
    if new_role not in ['student', 'teacher']:
        return jsonify({"msg": "Invalid role. Only 'student' or 'teacher' are allowed"}), 400
    
    user = User.query.filter_by(username=user_to_update).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404
    
    user.role = new_role
    db.session.commit()
    
    return jsonify({"msg": f"Role updated to {new_role} for user {user_to_update}"}), 200