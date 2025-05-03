# Vehicle Parking System

A database-driven application designed to manage parking slots, user registrations, and vehicle check-in/check-out processes efficiently.

## Features

- User registration and authentication
- Vehicle check-in and assignment of parking slots
- Vehicle check-out with automated fee calculation
- Real-time tracking of parking slot availability
- Admin dashboard for system management

## Technologies Used

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask)
- **Database**: SQLite

## Installation & Setup

1. Clone the repository:
```
git clone https://github.com/yourusername/Vehicle-Parking-System.git
cd Vehicle-Parking-System
```

2. Create a virtual environment and activate it:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```
pip install flask
```

4. Run the application:
```
python app.py
```

5. Access the application at:
```
http://127.0.0.1:5000
```

## Default Admin Account

- Username: admin
- Password: admin123

## Database Structure

- **Users Table**: Stores user registration details
- **Parking Slots Table**: Manages parking slot availability
- **Vehicles Table**: Tracks vehicle check-in/check-out and fees

## License

This project is licensed under the MIT License.
