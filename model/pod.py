from database.db import db

class Pod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    image = db.Column(db.String(120), nullable=False)
    ports = db.Column(db.String(120), nullable=True)
    ip = db.Column(db.String(15), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)