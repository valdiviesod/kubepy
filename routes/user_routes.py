from flask import Blueprint
from controller.user_controller import register, login

user_bp = Blueprint('user', __name__)

user_bp.route('/register', methods=['POST'])(register)
user_bp.route('/login', methods=['POST'])(login)