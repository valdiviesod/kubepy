from flask_migrate import Migrate, MigrateCommand
from main import app
from database.db import db

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run()
