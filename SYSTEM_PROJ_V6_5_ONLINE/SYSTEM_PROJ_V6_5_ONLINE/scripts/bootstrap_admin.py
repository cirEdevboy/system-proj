import sys
sys.path.insert(0, "/app")
from getpass import getpass
from app.database import Base, engine, SessionLocal
from app.models import User
from app.security import hash_password
Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    print('Criar primeiro ADMIN do SYSTEM PROJ')
    full_name=input('Nome completo: ').strip(); email=input('E-mail: ').strip().lower(); username=input('Usuário: ').strip().lower(); badge=input('Crachá: ').strip(); password=getpass('Senha (mínimo 8): ')
    if db.query(User).filter(User.username==username).first(): raise SystemExit('Usuário já existe')
    u=User(full_name=full_name,email=email,username=username,badge=badge,password_hash=hash_password(password),role='ADMIN',status='ACTIVE');db.add(u);db.commit();print('ADMIN criado com sucesso.')
finally: db.close()
