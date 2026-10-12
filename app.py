from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import bcrypt
import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# دالة للاتصال بقاعدة البيانات
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']

        # التحقق من البيانات
        if not name:
            flash('Name is required', 'danger')
            return render_template('register.html')
        if not email:
            flash('Email is required', 'danger')
            return render_template('register.html')
        if not password:
            flash('Password is required', 'danger')
            return render_template('register.html')
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')

        # تشفير كلمة المرور
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)', 
                           (email, name, hashed_pw.decode('utf-8')))
            conn.commit()
            
            # تسجيل الدخول التلقائي بعد التسجيل
            cursor.execute('SELECT user_id, name FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            
            return redirect(url_for('index'))
        except pymysql.err.IntegrityError as e:
            if e.args[0] == 1062: # Duplicate entry error
                flash('Email Already Exists', 'danger')
        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        if not email or not password:
            flash('Invalid email or password', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, password_hash FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            session['user_id'] = user['user_id']
            session['name'] = user['name']
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC', (session['user_id'],))
    todos = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html', todos=todos)

@app.route('/add', methods=['POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    title = request.form['title'].strip()
    if not title:
        flash('Title is required', 'danger')
    elif len(title) > 200:
        flash('Title is too long', 'danger')
    else:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO todos (user_id, title) VALUES (%s, %s)', (session['user_id'], title))
        conn.commit()
        cursor.close()
        conn.close()
        
    return redirect(url_for('index'))

@app.route('/edit/<int:todo_id>', methods=['POST'])
def edit_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    title = request.form['title'].strip()
    if title:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s', 
                       (title, todo_id, session['user_id']))
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for('index'))

@app.route('/toggle/<int:todo_id>', methods=['POST'])
def toggle_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    is_done = request.form['is_done']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s', 
                   (int(is_done), todo_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:todo_id>', methods=['POST'])
def delete_todo(todo_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM todos WHERE todo_id = %s AND user_id = %s', (todo_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)