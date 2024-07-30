from flask import Flask, render_template, request, redirect, url_for, session, flash
import qrcode
import os
import random
import string
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'inventory.db'

def generate_item_code():
    """Generate a random 6-character alphanumeric code for items."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

def generate_qr_code(unique_key):
    """Generate a QR code with a unique key URL."""
    url = url_for('item', unique_key=unique_key, _external=True)
    qr_code = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )
    qr_code.add_data(url)
    qr_code.make(fit=True)
    qr_code_image = qr_code.make_image().convert('RGB')
    
    qr_file_path = os.path.join('static', f'qr_{unique_key}.png')
    qr_code_image.save(qr_file_path)
    
    return qr_file_path

def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DATABASE)
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        return render_template('index.html')  # or any other page
    else:
        return redirect(url_for('login'))  # Redirect to login if not logged in

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        # Insert new user into database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
        conn.commit()
        conn.close()
        
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Check user credentials in the database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):  # Check hashed password
            session['user_id'] = user[0]  # Store user ID in session
            return redirect(url_for('dashboard'))  # Redirect to the dashboard or desired page
        else:
            flash('Invalid credentials, please try again.', 'danger')
    
    return render_template('login.html')  # Render the login page

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM inventory WHERE user_id = ?', (user_id,))
        items = cursor.fetchall()

        # Initialize counts
        purchased_count = 0
        donated_count = 0
        won_count = 0

        if items:  # Only run counts if there are items
            cursor.execute('SELECT COUNT(*) FROM inventory WHERE user_id = ? AND status = "Purchased"', (user_id,))
            purchased_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM inventory WHERE user_id = ? AND status = "Donated"', (user_id,))
            donated_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM inventory WHERE user_id = ? AND status = "Won"', (user_id,))
            won_count = cursor.fetchone()[0]
            print("done")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        items = []
    
    finally:
        conn.close()
    
    return render_template('dashboard.html', items=items, purchased_count=purchased_count, donated_count=donated_count, won_count=won_count)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/add_item', methods=['POST'])
def add_item():
    name = request.form['name']
    date = request.form['date']
    year_made = request.form['year_made']
    item_type = request.form['type']
    origin = request.form['origin']
    status = request.form['status']
    
    unique_key = generate_item_code()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO inventory (unique_key, name, date, year_made, type, origin, status, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (unique_key, name, date, year_made, item_type, origin, status, session['user_id']))
    conn.commit()
    conn.close()
    
    qr_file_path = generate_qr_code(unique_key)

    return render_template('qr_code.html', qr_file_path=qr_file_path, unique_key=unique_key)

@app.route('/item/<unique_key>', methods=['GET', 'POST'])
def item(unique_key):
    """Retrieve item data by unique key."""
    if request.method == 'POST':
        entered_key = request.form['unique_key']
        if entered_key == unique_key:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM inventory WHERE unique_key = ?', (unique_key,))
            item = cursor.fetchone()
            conn.close()
            return render_template('item_details.html', item=item)
        else:
            flash('Invalid key. Please try again.', 'danger')
    
    return render_template('item_auth.html', unique_key=unique_key)

if __name__ == '__main__':
    app.run(debug=True)