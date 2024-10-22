from flask import request, jsonify
from flask_jwt_extended import get_jwt_identity
from model.group import Group
from model.user import User
from database.db import db

def create_group():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()

    if current_user.role != 'admin' or 'teacher':
        return jsonify({"msg": "Unauthorized. Admin access required."}), 403
    
    if not current_user:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    data = request.get_json()
    group_name = data.get('name')

    if not group_name:
        return jsonify({"msg": "Falta el nombre del grupo"}), 400

    # Verificar si el grupo ya existe
    existing_group = Group.query.filter_by(name=group_name).first()
    if existing_group:
        return jsonify({"msg": "El grupo ya existe"}), 400
    
    new_group = Group(name=group_name)
    db.session.add(new_group)
    db.session.commit()

    return jsonify({"msg": "Grupo creado con éxito", "group_id": new_group.id}), 201

# Actualizar un grupo
def update_group(group_id):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()

    if current_user.role != 'admin' or 'teacher':
        return jsonify({"msg": "Unauthorized. Admin access required."}), 403
    
    if not current_user:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    data = request.get_json()
    new_name = data.get('name')

    if not new_name:
        return jsonify({"msg": "Falta el nuevo nombre del grupo"}), 400

    group = Group.query.filter_by(id=group_id).first()

    if not group:
        return jsonify({"msg": "Grupo no encontrado"}), 404

    group.name = new_name
    db.session.commit()

    return jsonify({"msg": "Grupo actualizado con éxito"}), 200

def delete_group(group_id):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()

    if current_user.role != 'admin' or 'teacher':
        return jsonify({"msg": "Unauthorized. Admin access required."}), 403

    if not current_user:
        return jsonify({"msg": "Usuario no encontrado"}), 404

    group = Group.query.filter_by(id=group_id).first()

    if not group:
        return jsonify({"msg": "Grupo no encontrado"}), 404

    db.session.delete(group)
    db.session.commit()

    return jsonify({"msg": "Grupo eliminado con éxito"}), 200

def get_all_groups():
    current_user = User.query.filter_by(username=get_jwt_identity()).first()
    
    if current_user.role != 'admin' or 'teacher':
        return jsonify({"msg": "Unauthorized. Admin access required."}), 403

    groups = Group.query.all()
    group_list = [{
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "users": [user.username for user in group.users]
    } for group in groups]

    return jsonify(group_list), 200

def get_group(group_id):
    current_user = User.query.filter_by(username=get_jwt_identity()).first()

    if not current_user or (current_user.role != 'admin' and current_user.role != 'teacher'):
        return jsonify({"msg": "Unauthorized. Admin or Teacher access required."}), 403

    group = Group.query.filter_by(id=group_id).first()

    if not group:
        return jsonify({"msg": "Grupo no encontrado"}), 404

    group_info = {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "users": [user.username for user in group.users]
    }

    return jsonify(group_info), 200
