from . import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    goals = db.relationship('BillableHourGoal', backref='user', lazy=True)
    holidays = db.relationship('Holiday', backref='user', lazy=True)
    vacation_days = db.relationship('VacationDay', backref='user', lazy=True)
    daily_logs = db.relationship('DailyLog', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'

class BillableHourGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    annual_goal = db.Column(db.Integer, nullable=False)
    workload_weights = db.Column(db.PickleType, nullable=False)  # Dict of {month: weight}
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Holiday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(120))
    is_firm = db.Column(db.Boolean, default=False)  # True if firm-wide, False if personal
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class VacationDay(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class DailyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hours = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
