from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import os
from datetime import datetime
import time
import secrets
from functools import wraps

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Database setup
def create_tables():
    conn = sqlite3.connect('parking_system.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        is_admin INTEGER DEFAULT 0
    )
    ''')
    
    # Parking slots table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parking_slots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_number TEXT UNIQUE NOT NULL,
        status TEXT NOT NULL DEFAULT 'available',
        vehicle_id INTEGER DEFAULT NULL
    )
    ''')
    
    # Vehicles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        license_plate TEXT NOT NULL,
        vehicle_type TEXT NOT NULL,
        check_in_time TIMESTAMP DEFAULT NULL,
        check_out_time TIMESTAMP DEFAULT NULL,
        parking_slot_id INTEGER DEFAULT NULL,
        fee REAL DEFAULT 0.0,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (parking_slot_id) REFERENCES parking_slots(id)
    )
    ''')
    
    # Add default admin user if not exists
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, name, email, is_admin) VALUES (?, ?, ?, ?, ?)",
                     ('admin', 'admin123', 'Administrator', 'admin@parking.com', 1))
    
    # Add some initial parking slots if none exist
    cursor.execute("SELECT COUNT(*) FROM parking_slots")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 21):
            cursor.execute("INSERT INTO parking_slots (slot_number, status) VALUES (?, ?)",
                         (f'A{i:02d}', 'available'))
    
    conn.commit()
    conn.close()

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'is_admin' not in session or session['is_admin'] != 1:
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        
        conn = sqlite3.connect('parking_system.db')
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT INTO users (username, password, name, email, phone) VALUES (?, ?, ?, ?, ?)",
                         (username, password, name, email, phone))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'danger')
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('parking_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[2]
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('parking_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get user's vehicles
    cursor.execute("""
        SELECT v.*, p.slot_number 
        FROM vehicles v 
        LEFT JOIN parking_slots p ON v.parking_slot_id = p.id 
        WHERE v.user_id = ? 
        ORDER BY v.check_in_time DESC
    """, (session['user_id'],))
    vehicles = cursor.fetchall()
    
    conn.close()
    return render_template('dashboard.html', vehicles=vehicles)

@app.route('/check_in', methods=['GET', 'POST'])
@login_required
def check_in():
    if request.method == 'POST':
        license_plate = request.form['license_plate']
        vehicle_type = request.form['vehicle_type']
        
        conn = sqlite3.connect('parking_system.db')
        cursor = conn.cursor()
        
        # Check if vehicle is already parked
        cursor.execute("SELECT id FROM vehicles WHERE license_plate = ? AND check_out_time IS NULL", (license_plate,))
        if cursor.fetchone():
            flash('This vehicle is already parked', 'danger')
            conn.close()
            return redirect(url_for('check_in'))
        
        # Find available parking slot
        cursor.execute("SELECT id FROM parking_slots WHERE status = 'available' LIMIT 1")
        slot = cursor.fetchone()
        
        if not slot:
            flash('No parking slots available', 'danger')
            conn.close()
            return redirect(url_for('dashboard'))
        
        slot_id = slot[0]
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add vehicle and update slot status
        cursor.execute("""
            INSERT INTO vehicles (user_id, license_plate, vehicle_type, check_in_time, parking_slot_id) 
            VALUES (?, ?, ?, ?, ?)
        """, (session['user_id'], license_plate, vehicle_type, current_time, slot_id))
        
        vehicle_id = cursor.lastrowid
        
        cursor.execute("UPDATE parking_slots SET status = 'occupied', vehicle_id = ? WHERE id = ?", 
                      (vehicle_id, slot_id))
        
        conn.commit()
        conn.close()
        
        flash('Vehicle checked in successfully', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('check_in.html')

@app.route('/check_out/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def check_out(vehicle_id):
    conn = sqlite3.connect('parking_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get vehicle info
    cursor.execute("""
        SELECT v.*, p.id as slot_id, p.slot_number 
        FROM vehicles v 
        JOIN parking_slots p ON v.parking_slot_id = p.id 
        WHERE v.id = ? AND v.user_id = ?
    """, (vehicle_id, session['user_id']))
    vehicle = cursor.fetchone()
    
    if not vehicle:
        conn.close()
        flash('Vehicle not found or not authorized', 'danger')
        return redirect(url_for('dashboard'))
    
    if vehicle['check_out_time'] is not None:
        conn.close()
        flash('Vehicle already checked out', 'danger')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        check_out_time = datetime.now()
        check_in_time = datetime.strptime(vehicle['check_in_time'], '%Y-%m-%d %H:%M:%S')
        
        # Calculate parking duration in hours
        duration = (check_out_time - check_in_time).total_seconds() / 3600
        
        # Calculate fee (assume $2 per hour, minimum 1 hour)
        fee = max(1, round(duration)) * 2
        
        # Update vehicle record
        cursor.execute("""
            UPDATE vehicles 
            SET check_out_time = ?, fee = ? 
            WHERE id = ?
        """, (check_out_time.strftime('%Y-%m-%d %H:%M:%S'), fee, vehicle_id))
        
        # Free up parking slot
        cursor.execute("UPDATE parking_slots SET status = 'available', vehicle_id = NULL WHERE id = ?", 
                      (vehicle['slot_id'],))
        
        conn.commit()
        conn.close()
        
        flash(f'Vehicle checked out successfully. Fee: ${fee:.2f}', 'success')
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('check_out.html', vehicle=vehicle)

@app.route('/admin', methods=['GET'])
@login_required
@admin_required
def admin():
    conn = sqlite3.connect('parking_system.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all parking slots with their status
    cursor.execute("""
        SELECT * FROM parking_slots ORDER BY slot_number
    """)
    slots = cursor.fetchall()
    
    # Get all active vehicles
    cursor.execute("""
        SELECT v.*, u.name as user_name, p.slot_number 
        FROM vehicles v 
        JOIN users u ON v.user_id = u.id 
        JOIN parking_slots p ON v.parking_slot_id = p.id 
        WHERE v.check_out_time IS NULL
    """)
    active_vehicles = cursor.fetchall()
    
    conn.close()
    return render_template('admin.html', slots=slots, active_vehicles=active_vehicles)

@app.route('/admin/add_slots', methods=['POST'])
@login_required
@admin_required
def add_slots():
    if request.method == 'POST':
        prefix = request.form['prefix']
        start_num = int(request.form['start_num'])
        count = int(request.form['count'])
        
        conn = sqlite3.connect('parking_system.db')
        cursor = conn.cursor()
        
        for i in range(start_num, start_num + count):
            slot_number = f'{prefix}{i:02d}'
            try:
                cursor.execute("INSERT INTO parking_slots (slot_number, status) VALUES (?, ?)",
                             (slot_number, 'available'))
            except sqlite3.IntegrityError:
                # Slot number already exists, skip
                continue
                
        conn.commit()
        conn.close()
        
        flash(f'Added {count} parking slots', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
