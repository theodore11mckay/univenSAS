from datetime import datetime
from werkzeug.security import generate_password_hash
from . import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False, default="student")
    full_name = db.Column(db.String(120), nullable=False)
    sa_id = db.Column(db.String(13), unique=True, nullable=True)
    phone = db.Column(db.String(10), nullable=True)
    student_number = db.Column(db.String(8), unique=True, nullable=True)
    email = db.Column(db.String(160), unique=True, nullable=False)
    pin_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    applications = db.relationship("Application", backref="student", lazy=True)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(220), nullable=False)
    distance = db.Column(db.String(80), nullable=False)
    contact = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    amenities = db.Column(db.Text, nullable=False)
    rooms = db.Column(db.Integer, nullable=False, default=10)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey("listing.id"), nullable=False)
    funding_source = db.Column(db.String(40), nullable=False)
    academic_year = db.Column(db.Integer, nullable=False)
    degree_code = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="Submitted")
    room_number = db.Column(db.String(30), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    listing = db.relationship("Listing")

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    document_type = db.Column(db.String(40), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("application.id"), nullable=False)
    subject = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), nullable=False, default="Unread")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    application = db.relationship("Application")

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    subject = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    broadcast = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def seed_data():
    if User.query.filter_by(role="admin").first() is None:
        admin_pin = __import__("os").environ.get("ADMIN_PIN", "246813")
        db.session.add(User(
            role="admin", full_name="Accommodation Administrator",
            email="admin@mvula.univen.ac.za",
            pin_hash=generate_password_hash(admin_pin)
        ))

    if Listing.query.count() == 0:
        amenities_pool = [
            "Wi-Fi|Water|Electricity|Security|Study Area",
            "Wi-Fi|Laundry|Parking|Security|Kitchen",
            "Wi-Fi|Furnished|Water|Security|Shuttle",
            "Wi-Fi|Study Area|CCTV|Parking|Kitchen",
        ]
        for i in range(1, 13):
            db.session.add(Listing(
                name=f"UNIVEN Accommodation Listing {i}",
                address=f"Campus Area, Thohoyandou, Limpopo, South Africa",
                distance=f"{0.7 + i * 0.12:.1f} km from campus",
                contact=f"+27 15 000 {1000+i:04d}",
                price=2800 + i * 175,
                amenities=amenities_pool[(i-1) % len(amenities_pool)],
                rooms=10 + i
            ))
    db.session.commit()
