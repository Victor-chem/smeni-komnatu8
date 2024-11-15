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
    app.run()
