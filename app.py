from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import logging

# Настройка приложения Flask
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Секретный ключ для сессий
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rooms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Email администратора
ADMIN_EMAIL = 'v.fofanov1@g.nsu.ru'

# Логирование активности
logging.basicConfig(filename='user_activity.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Модель для хранения информации о комнатах
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False)  # Email пользователя, создавшего комнату

# Модель для записи активности пользователей
class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_email = db.Column(db.String(100))  # Email пользователя
    action = db.Column(db.String(200))  # Описание действия
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # Время действия

# Создание базы данных
with app.app_context():
    db.create_all()

# Логирование в базу данных
@app.before_request
def log_to_db():
    user_email = session.get('user_email', 'Anonymous')  # Получаем email из сессии
    action = f'{request.method} {request.path}'  # Действие пользователя
    activity = UserActivity(user_email=user_email, action=action)
    db.session.add(activity)
    db.session.commit()

# Главная страница
@app.route('/')
def home():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    rooms = Room.query.all()
    return render_template('index.html', rooms=rooms)

# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        if email.endswith('@g.nsu.ru'):
            session['user_email'] = email
            flash('Вы успешно вошли в систему!')
            return redirect(url_for('home'))
        else:
            flash('Только университетские email разрешены!')
            return redirect(url_for('login'))
    return render_template('login.html')

# Выход из системы
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    flash('Вы вышли из системы.')
    return redirect(url_for('login'))

# Добавление комнаты
@app.route('/add_room', methods=['GET', 'POST'])
def add_room():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        room_number = request.form['room_number']
        description = request.form['description']

        # Проверяем, есть ли уже такая комната
        if Room.query.filter_by(room_number=room_number).first():
            flash('Комната с таким номером уже существует!')
            return redirect(url_for('add_room'))

        new_room = Room(room_number=room_number, description=description, email=session['user_email'])
        db.session.add(new_room)
        db.session.commit()
        flash('Комната успешно добавлена!')
        return redirect(url_for('home'))
    return render_template('add_room.html')

# Удаление комнаты (только для администратора)
@app.route('/delete_room/<int:room_id>', methods=['POST'])
def delete_room(room_id):
    if session.get('user_email') != ADMIN_EMAIL:
        return "Доступ запрещен", 403
    room = Room.query.get_or_404(room_id)
    db.session.delete(room)
    db.session.commit()
    flash('Комната удалена!')
    return redirect(url_for('home'))

# Админ-панель активности
@app.route('/admin/activity')
def view_activity():
    if session.get('user_email') != ADMIN_EMAIL:
        return "Доступ запрещен", 403
    activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).all()
    return render_template('admin_activity.html', activities=activities)

# Запуск приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
@app.route('/admin/view_rooms')
def view_rooms():
    if session.get('user_email') != ADMIN_EMAIL:
        return "Доступ запрещен", 403
    rooms = Room.query.all()
    return render_template('view_rooms.html', rooms=rooms)
