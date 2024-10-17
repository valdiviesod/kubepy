from database.db import db

# Modelo Group para representar grupos de usuarios que comparten acceso a contenedores iguales
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', secondary='group_user', backref='groups', lazy=True)
    pods = db.relationship('Pod', secondary='group_pod', backref='groups', lazy=True)

# Tabla intermedia para representar la relación muchos a muchos entre Group y User
group_user = db.Table('group_user',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# Tabla intermedia para representar la relación muchos a muchos entre Group y Pod
group_pod = db.Table('group_pod',
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
    db.Column('pod_id', db.Integer, db.ForeignKey('pod.id'), primary_key=True)
)
