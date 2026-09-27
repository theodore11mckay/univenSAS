import os
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from . import db
from .models import User, Listing, Application, Document, Ticket, Message

main = Blueprint("main", __name__)

ALLOWED_DOCS = {"ID Copy", "Signed Lease", "NSFAS Proof", "Proof of Registration"}
UPLOAD_DIR = os.path.join("app", "static", "uploads")

def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None

def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user or (role and user.role != role):
                return redirect(url_for("main.index"))
            return fn(*args, **kwargs)
        return wrapper
    return deco

@main.get("/")
def index():
    return render_template("index.html", listings=Listing.query.order_by(Listing.id).all(), user=current_user())

@main.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.form
        email = data.get("email","").strip().lower()
        if not data.get("sa_id","").isdigit() or len(data.get("sa_id","")) != 13:
            flash("SA ID must contain exactly 13 digits.", "error")
            return redirect(url_for("main.register"))
        if not data.get("phone","").isdigit() or len(data.get("phone","")) != 10:
            flash("Phone must contain exactly 10 digits.", "error")
            return redirect(url_for("main.register"))
        if not data.get("student_number","").isdigit() or len(data.get("student_number","")) > 8:
            flash("Student number must be numeric and no longer than 8 digits.", "error")
            return redirect(url_for("main.register"))
        if not (email.endswith("@gmail.com") or email.endswith("@mvula.univen.ac.za")):
            flash("Email must use @gmail.com or @mvula.univen.ac.za.", "error")
            return redirect(url_for("main.register"))
        if data.get("pin") != data.get("pin_confirm"):
            flash("PIN entries do not match.", "error")
            return redirect(url_for("main.register"))
        if User.query.filter((User.email == email) | (User.sa_id == data["sa_id"]) | (User.student_number == data["student_number"])).first():
            flash("An account with one of those identifiers already exists.", "error")
            return redirect(url_for("main.register"))
        user = User(
            full_name=data["full_name"].strip(), sa_id=data["sa_id"],
            phone=data["phone"], student_number=data["student_number"],
            email=email, pin_hash=generate_password_hash(data["pin"])
        )
        db.session.add(user); db.session.commit()
        session["user_id"] = user.id
        return redirect(url_for("main.student"))
    return render_template("register.html", user=current_user())

@main.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").lower().strip()
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.pin_hash, request.form.get("pin","")):
            session["user_id"] = user.id
            return redirect(url_for("main.admin" if user.role == "admin" else "main.student"))
        flash("Invalid login details.", "error")
    return render_template("login.html", user=current_user())

@main.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))

@main.get("/student")
@login_required("student")
def student():
    user = current_user()
    apps = Application.query.filter_by(student_id=user.id).order_by(Application.created_at.desc()).all()
    tickets = Ticket.query.join(Application).filter(Application.student_id == user.id).order_by(Ticket.created_at.desc()).all()
    messages = Message.query.filter((Message.recipient_id == user.id) | (Message.broadcast == True)).order_by(Message.created_at.desc()).all()
    return render_template("student.html", user=user, listings=Listing.query.all(), applications=apps, tickets=tickets, messages=messages)

@main.post("/student/application")
@login_required("student")
def create_application():
    year = int(request.form.get("academic_year"))
    if year < 2027:
        flash("Academic year must be 2027 or later.", "error")
        return redirect(url_for("main.student"))
    app = Application(
        student_id=current_user().id,
        listing_id=int(request.form["listing_id"]),
        funding_source=request.form["funding_source"],
        academic_year=year,
        degree_code=request.form["degree_code"].strip()
    )
    db.session.add(app); db.session.commit()
    flash("Application submitted.", "success")
    return redirect(url_for("main.student"))

@main.post("/student/application/<int:application_id>/documents")
@login_required("student")
def upload_documents(application_id):
    app = Application.query.get_or_404(application_id)
    if app.student_id != current_user().id:
        return "Forbidden", 403
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    for doc_type in ALLOWED_DOCS:
        f = request.files.get(doc_type)
        if f and f.filename:
            safe = secure_filename(f.filename)
            stored = f"{application_id}_{doc_type.replace(' ','_')}_{safe}"
            f.save(os.path.join(UPLOAD_DIR, stored))
            db.session.add(Document(application_id=application_id, document_type=doc_type, filename=stored))
    db.session.commit()
    flash("Documents uploaded.", "success")
    return redirect(url_for("main.student"))

@main.post("/student/ticket")
@login_required("student")
def create_ticket():
    app = Application.query.get_or_404(int(request.form["application_id"]))
    if app.student_id != current_user().id or app.status != "Approved":
        flash("Maintenance is available only after application approval.", "error")
        return redirect(url_for("main.student"))
    db.session.add(Ticket(application_id=app.id, subject=request.form["subject"], description=request.form["description"]))
    db.session.commit()
    return redirect(url_for("main.student"))

@main.post("/student/message")
@login_required("student")
def student_message():
    db.session.add(Message(sender_id=current_user().id, recipient_id=User.query.filter_by(role="admin").first().id,
                           subject=request.form["subject"], body=request.form["body"]))
    db.session.commit()
    return redirect(url_for("main.student"))

@main.get("/admin")
@login_required("admin")
def admin():
    return render_template(
        "admin.html", user=current_user(),
        applications=Application.query.order_by(Application.created_at.desc()).all(),
        listings=Listing.query.all(),
        tickets=Ticket.query.order_by(Ticket.created_at.desc()).all(),
        students=User.query.filter_by(role="student").all(),
        messages=Message.query.order_by(Message.created_at.desc()).all()
    )

@main.post("/admin/application/<int:application_id>/decision")
@login_required("admin")
def application_decision(application_id):
    app = Application.query.get_or_404(application_id)
    decision = request.form["decision"]
    app.status = "Approved" if decision == "approve" else "Rejected"
    if app.status == "Approved" and not app.room_number:
        app.room_number = f"R-{app.listing_id}-{app.id:03d}"
    db.session.commit()
    return redirect(url_for("main.admin"))

@main.post("/admin/application/<int:application_id>/assign")
@login_required("admin")
def assign_room(application_id):
    app = Application.query.get_or_404(application_id)
    app.room_number = request.form["room_number"].strip()
    db.session.commit()
    return redirect(url_for("main.admin"))

@main.post("/admin/ticket/<int:ticket_id>/status")
@login_required("admin")
def ticket_status(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.status = request.form["status"]
    db.session.commit()
    return redirect(url_for("main.admin"))

@main.post("/admin/broadcast")
@login_required("admin")
def broadcast():
    db.session.add(Message(sender_id=current_user().id, subject=request.form["subject"], body=request.form["body"], broadcast=True))
    db.session.commit()
    return redirect(url_for("main.admin"))

@main.post("/admin/message")
@login_required("admin")
def admin_message():
    db.session.add(Message(sender_id=current_user().id, recipient_id=int(request.form["student_id"]),
                           subject=request.form["subject"], body=request.form["body"]))
    db.session.commit()
    return redirect(url_for("main.admin"))
