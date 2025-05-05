from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'vehicle_parking_system_secret_key'

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_number = db.Column(db.String(20), nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

class ParkingSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slot_number = db.Column(db.String(10), nullable=False)
    slot_type = db.Column(db.String(50), nullable=False)  # car, bike, etc.
    is_occupied = db.Column(db.Boolean, default=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('parking_slot.id'), nullable=False)
    entry_time = db.Column(db.DateTime, default=datetime.now)
    exit_time = db.Column(db.DateTime, nullable=True)
    amount = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(20), default='Pending')

# Routes for HTML templates
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/booking')
def booking_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('booking.html')

@app.route('/admin')
def admin_page():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login_page'))
    return render_template('admin.html')

@app.route('/check_in')
def check_in_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('check_in.html')

@app.route('/check_out/<int:booking_id>')
def check_out_page(booking_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    
    # Get booking details to display on checkout page
    booking_info = db.session.query(
        Booking, Vehicle, ParkingSlot
    ).join(
        Vehicle, Vehicle.id == Booking.vehicle_id
    ).join(
        ParkingSlot, ParkingSlot.id == Booking.slot_id
    ).filter(
        Booking.id == booking_id,
        Booking.exit_time.is_(None)
    ).first()
    
    if not booking_info:
        return redirect(url_for('booking_page'))
    
    return render_template('check_out.html', booking=booking_info)

@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

# API Routes for form submissions
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    # Check if email already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Email already registered'})
    
    # Create new user
    new_user = User(
        name=data['name'],
        email=data['email'],
        password=data['password'],  # In production, hash this password
        phone=data['phone']
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Registration successful'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.password == data['password']:  # In production, verify hashed password
        session['user_id'] = user.id
        session['is_admin'] = user.is_admin
        return jsonify({'success': True, 'is_admin': user.is_admin})
    
    return jsonify({'success': False, 'message': 'Invalid credentials'})

# Update the add-vehicle endpoint to return vehicle_id

@app.route('/api/add-vehicle', methods=['POST'])
def add_vehicle():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.json
    
    new_vehicle = Vehicle(
        user_id=session['user_id'],
        vehicle_number=data['vehicle_number'],
        vehicle_type=data['vehicle_type']
    )
    
    db.session.add(new_vehicle)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Vehicle added successfully',
        'vehicle_id': new_vehicle.id
    })

@app.route('/api/book-slot', methods=['POST'])
def book_slot():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.json
    
    # Find available slot
    available_slot = ParkingSlot.query.filter_by(
        slot_type=data['vehicle_type'], 
        is_occupied=False
    ).first()
    
    if not available_slot:
        return jsonify({'success': False, 'message': 'No slots available'})
    
    # Mark slot as occupied
    available_slot.is_occupied = True
    
    # Create booking
    new_booking = Booking(
        user_id=session['user_id'],
        vehicle_id=data['vehicle_id'],
        slot_id=available_slot.id
    )
    
    db.session.add(new_booking)
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': 'Booking successful',
        'slot_number': available_slot.slot_number
    })

@app.route('/api/complete-booking', methods=['POST'])
def complete_booking():
    data = request.json
    
    booking = Booking.query.get(data['booking_id'])
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found'})
    
    # Update booking
    booking.exit_time = datetime.now()
    booking.amount = data['amount']
    booking.payment_status = 'Paid'
    
    # Free up the slot
    slot = ParkingSlot.query.get(booking.slot_id)
    slot.is_occupied = False
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Checkout complete'})

# Add these routes to the existing app.py file

@app.route('/api/parking-availability', methods=['GET'])
def parking_availability():
    # Count total slots by type
    car_slots = ParkingSlot.query.filter_by(slot_type='car').count()
    bike_slots = ParkingSlot.query.filter_by(slot_type='bike').count()
    truck_slots = ParkingSlot.query.filter_by(slot_type='truck').count()
    
    # Count available slots by type
    available_car = ParkingSlot.query.filter_by(slot_type='car', is_occupied=False).count()
    available_bike = ParkingSlot.query.filter_by(slot_type='bike', is_occupied=False).count()
    available_truck = ParkingSlot.query.filter_by(slot_type='truck', is_occupied=False).count()
    
    return jsonify({
        'total': {
            'car': car_slots,
            'bike': bike_slots,
            'truck': truck_slots
        },
        'available': {
            'car': available_car,
            'bike': available_bike,
            'truck': available_truck
        }
    })

@app.route('/api/user-vehicles', methods=['GET'])
def get_user_vehicles():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in', 'vehicles': []})
    
    vehicles = Vehicle.query.filter_by(user_id=session['user_id']).all()
    vehicles_data = [{
        'id': v.id,
        'vehicle_number': v.vehicle_number,
        'vehicle_type': v.vehicle_type
    } for v in vehicles]
    
    return jsonify({'success': True, 'vehicles': vehicles_data})

@app.route('/api/vehicle/<int:vehicle_id>', methods=['GET'])
def get_vehicle(vehicle_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    vehicle = Vehicle.query.get(vehicle_id)
    
    if not vehicle or vehicle.user_id != session['user_id']:
        return jsonify({'success': False, 'message': 'Vehicle not found'})
    
    return jsonify({
        'success': True,
        'id': vehicle.id,
        'vehicle_number': vehicle.vehicle_number,
        'vehicle_type': vehicle.vehicle_type
    })

@app.route('/api/admin/current-bookings', methods=['GET'])
def admin_current_bookings():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized', 'bookings': []})
    
    # Get bookings with no exit time (current bookings)
    bookings = db.session.query(
        Booking, User, Vehicle, ParkingSlot
    ).join(
        User, User.id == Booking.user_id
    ).join(
        Vehicle, Vehicle.id == Booking.vehicle_id
    ).join(
        ParkingSlot, ParkingSlot.id == Booking.slot_id
    ).filter(
        Booking.exit_time.is_(None)
    ).all()
    
    bookings_data = [{
        'id': booking.Booking.id,
        'user_name': booking.User.name,
        'vehicle_number': booking.Vehicle.vehicle_number,
        'slot_number': booking.ParkingSlot.slot_number,
        'entry_time': booking.Booking.entry_time.isoformat()
    } for booking in bookings]
    
    return jsonify({'success': True, 'bookings': bookings_data})

@app.route('/api/admin/parking-slots', methods=['GET'])
def admin_parking_slots():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized', 'slots': []})
    
    slots = ParkingSlot.query.all()
    slots_data = [{
        'id': slot.id,
        'slot_number': slot.slot_number,
        'slot_type': slot.slot_type,
        'is_occupied': slot.is_occupied
    } for slot in slots]
    
    return jsonify({'success': True, 'slots': slots_data})

@app.route('/api/admin/booking-history', methods=['GET'])
def admin_booking_history():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized', 'bookings': []})
    
    # Get all completed bookings
    bookings = db.session.query(
        Booking, User, Vehicle, ParkingSlot
    ).join(
        User, User.id == Booking.user_id
    ).join(
        Vehicle, Vehicle.id == Booking.vehicle_id
    ).join(
        ParkingSlot, ParkingSlot.id == Booking.slot_id
    ).filter(
        Booking.exit_time.isnot(None)
    ).all()
    
    bookings_data = [{
        'id': booking.Booking.id,
        'user_name': booking.User.name,
        'vehicle_number': booking.Vehicle.vehicle_number,
        'slot_number': booking.ParkingSlot.slot_number,
        'entry_time': booking.Booking.entry_time.isoformat(),
        'exit_time': booking.Booking.exit_time.isoformat() if booking.Booking.exit_time else None,
        'amount': booking.Booking.amount,
        'payment_status': booking.Booking.payment_status
    } for booking in bookings]
    
    return jsonify({'success': True, 'bookings': bookings_data})

@app.route('/api/admin/users', methods=['GET'])
def admin_users():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized', 'users': []})
    
    users = User.query.all()
    users_data = [{
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'phone': user.phone,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat()
    } for user in users]
    
    return jsonify({'success': True, 'users': users_data})

@app.route('/api/admin/add-slot', methods=['POST'])
def admin_add_slot():
    if 'user_id' not in session or not session.get('is_admin'):
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    data = request.json
    
    # Check if slot number already exists
    existing_slot = ParkingSlot.query.filter_by(slot_number=data['slot_number']).first()
    if existing_slot:
        return jsonify({'success': False, 'message': 'Slot number already exists'})
    
    new_slot = ParkingSlot(
        slot_number=data['slot_number'],
        slot_type=data['slot_type'],
        is_occupied=False
    )
    
    db.session.add(new_slot)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Parking slot added successfully'})

@app.route('/api/user-bookings', methods=['GET'])
def get_user_bookings():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in', 'bookings': []})
    
    # Get active bookings (no exit time) for this user
    bookings = db.session.query(
        Booking, Vehicle, ParkingSlot
    ).join(
        Vehicle, Vehicle.id == Booking.vehicle_id
    ).join(
        ParkingSlot, ParkingSlot.id == Booking.slot_id
    ).filter(
        Booking.user_id == session['user_id'],
        Booking.exit_time.is_(None)
    ).all()
    
    bookings_data = [{
        'id': b.Booking.id,
        'vehicle_number': b.Vehicle.vehicle_number,
        'slot_number': b.ParkingSlot.slot_number,
        'entry_time': b.Booking.entry_time.isoformat()
    } for b in bookings]
    
    return jsonify({'success': True, 'bookings': bookings_data})

# Add logout route for convenience
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Add this function before "if __name__ == '__main__':" 
def create_default_admin():
    # Check if admin exists
    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        # Create default admin user
        default_admin = User(
            name="Admin User",
            email="admin@parkease.com",
            password="admin123",  # In production, use a hashed password
            phone="1234567890",
            is_admin=True
        )
        db.session.add(default_admin)
        db.session.commit()
        print("Default admin user created:")
        print("Email: admin@parkease.com")
        print("Password: admin123")
    else:
        print(f"Admin already exists: {admin.email}")

# Update the main block to call this function
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_admin()
    app.run(host='0.0.0.0', port=5000,debug=True)
    # app.run(debug=True)

