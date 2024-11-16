from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Секретный ключ для сессий
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rooms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель для хранения информации о комнатах
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False)  # Email пользователя, создавшего комнату

# Создание таблиц, если они ещё не созданы
with app.app_context():
    db.create_all()

# Маршрут для упрощенного входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        
        # Проверка домена email
        if email.endswith('@g.nsu.ru'):
            # Сохраняем email в сессии для авторизации
            session['user_email'] = email
            flash('Вы успешно вошли в систему!')
            return redirect(url_for('home'))
        else:
            flash('Только университетские email разрешены!')
            return redirect(url_for('login'))
    
    return render_template('login.html')

# Маршрут для выхода
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Вы вышли из системы.')
    return redirect(url_for('login'))

# Главная страница (доступна только для авторизованных пользователей)
@app.route('/')
def home():
    # Проверяем, что пользователь авторизован
    if 'user_email' not in session:
        return redirect(url_for('login'))
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

# Маршрут для добавления комнаты (доступен только если пользователь не создал комнату ранее)
@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    # Проверяем, есть ли уже комната, созданная этим пользователем
    existing_room = Room.query.filter_by(email=session['user_email']).first()
    if existing_room:
        flash('Вы уже создали комнату. Редактируйте её, если хотите внести изменения.')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        room_number = request.form['room_number']
        description = request.form['description']
        
        # Создаем новую комнату и связываем её с пользователем
        new_room = Room(room_number=room_number, description=description, email=session['user_email'])
        db.session.add(new_room)
        db.session.commit()
        
        flash('Комната успешно добавлена!')
        return redirect(url_for('home'))
    
    return render_template('add_room.html')

# Запуск приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

import logging
from flask import Flask, request

app = Flask(__name__)

# Настройка логов
logging.basicConfig(filename='user_activity.log', level=logging.INFO, format='%(asctime)s - %(message)s')

@app.before_request
def log_activity():
    user = request.remote_addr  # IP-адрес пользователя
    path = request.path  # Какой маршрут посещен
    method = request.method  # GET, POST и т.д.
    logging.info(f'User: {user}, Path: {path}, Method: {method}')

from datetime import datetime

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100))  # Почта или IP
    action = db.Column(db.String(200))  # Описание действия
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Не забудь создать таблицу
with app.app_context():
    db.create_all()
@app.before_request
def log_to_db():
    user_email = session.get('user_email', 'Anonymous')  # Получаем почту, если пользователь залогинен
    action = f'{request.method} {request.path}'
    activity = UserActivity(user_email=user_email, action=action)
    db.session.add(activity)
    db.session.commit()
@app.route('/admin/activity')
def view_activity():
    activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).all()
    return render_template('admin_activity.html', activities=activities)
