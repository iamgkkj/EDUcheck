from app import create_app, db

app = create_app()
with app.app_context():
    print('Dropping all existing tables...')
    db.drop_all()
    print('Creating new tables with updated schema...')
    db.create_all()
    print('Database reset complete!')