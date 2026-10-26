from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import bcrypt
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
load_dotenv()

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = 'static/images'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.secret_key = os.getenv('SECRET_KEY')

def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )

# دالة اتصال منفصلة لقاعدة بيانات اللاب (library) عشان منبوظش الـ Todos
def get_library_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        database='library',
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm = request.form['confirm_password']
        
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

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)', 
                           (email, name, hashed_pw.decode('utf-8')))
            conn.commit()
            
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

# ==========================================
# LAB 3: LIBRARY ROUTES (BONUS INCLUDED)
# ==========================================

@app.route('/library')
def library():
    conn = get_library_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM AUTHOR")
    authors = cursor.fetchall()
    
    cursor.execute("SELECT * FROM BOOK")
    books = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('library.html', authors=authors, books=books)

@app.route('/add_author', methods=['POST'])
def add_author():
    author_id = request.form['author_id']
    name = request.form['name']
    country = request.form['country']
    photo = request.files.get('photo')
    
    photo_path = None
    if photo and photo.filename:
        filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        photo_path = f"images/{filename}"
        
    conn = get_library_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO AUTHOR (author_id, name, country, photo) VALUES (%s, %s, %s, %s)", 
                   (author_id, name, country, photo_path))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('library'))

@app.route('/add_book', methods=['POST'])
def add_book():
    book_id = request.form['book_id']
    title = request.form['title']
    price = request.form['price']
    author_id = request.form['author_id']
    cover = request.files.get('cover')
    
    cover_path = None
    if cover and cover.filename:
        filename = secure_filename(cover.filename)
        cover.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        cover_path = f"images/{filename}"
        
    conn = get_library_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO BOOK (book_id, title, price, author_id, cover) VALUES (%s, %s, %s, %s, %s)", 
                   (book_id, title, price, author_id, cover_path))
    conn.commit()
    cursor.close()
    conn.close()
    
    return redirect(url_for('library'))

# ---------- F2.3: EDIT ----------

@app.route('/edit_author/<int:id>', methods=['GET', 'POST'])
def edit_author(id):
    conn = get_library_connection()
    cursor = conn.cursor()
    try:
        if request.method == 'POST':
            name = request.form['name'].strip()
            country = request.form['country'].strip()
            photo = request.files.get('photo')

            if not name:
                flash('Name is required', 'danger')
                return redirect(url_for('edit_author', id=id))

            if photo and photo.filename:
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cursor.execute(
                    "UPDATE AUTHOR SET name = %s, country = %s, photo = %s WHERE author_id = %s",
                    (name, country, f"images/{filename}", id))
            else:
                # مفيش صورة جديدة: سيب الصورة القديمة زي ما هي
                cursor.execute(
                    "UPDATE AUTHOR SET name = %s, country = %s WHERE author_id = %s",
                    (name, country, id))
            conn.commit()
            return redirect(url_for('library'))

        cursor.execute("SELECT * FROM AUTHOR WHERE author_id = %s", (id,))
        author = cursor.fetchone()
        if not author:
            flash('Author not found', 'danger')
            return redirect(url_for('library'))
        return render_template('edit_author.html', author=author)
    finally:
        cursor.close()
        conn.close()

@app.route('/edit_book/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    conn = get_library_connection()
    cursor = conn.cursor()
    try:
        if request.method == 'POST':
            title = request.form['title'].strip()
            price = request.form['price']
            author_id = request.form['author_id']
            cover = request.files.get('cover')

            if not title:
                flash('Title is required', 'danger')
                return redirect(url_for('edit_book', id=id))

            try:
                if cover and cover.filename:
                    filename = secure_filename(cover.filename)
                    cover.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    cursor.execute(
                        "UPDATE BOOK SET title = %s, price = %s, author_id = %s, cover = %s WHERE book_id = %s",
                        (title, price, author_id, f"images/{filename}", id))
                else:
                    cursor.execute(
                        "UPDATE BOOK SET title = %s, price = %s, author_id = %s WHERE book_id = %s",
                        (title, price, author_id, id))
                conn.commit()
            except pymysql.err.IntegrityError:
                # الـ foreign key اترفض: الـ author_id مش موجود
                flash('Author ID does not exist', 'danger')
                return redirect(url_for('edit_book', id=id))
            return redirect(url_for('library'))

        cursor.execute("SELECT * FROM BOOK WHERE book_id = %s", (id,))
        book = cursor.fetchone()
        if not book:
            flash('Book not found', 'danger')
            return redirect(url_for('library'))
        return render_template('edit_book.html', book=book)
    finally:
        cursor.close()
        conn.close()

# ---------- F2.4 / F2.5: DELETE ----------

@app.route('/delete_book/<int:id>')
def delete_book(id):
    conn = get_library_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM BOOK WHERE book_id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('library'))

@app.route('/delete_author/<int:id>')
def delete_author(id):
    conn = get_library_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM AUTHOR WHERE author_id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('library'))

if __name__ == '__main__':
    app.run(debug=True)