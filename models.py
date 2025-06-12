from extension import db
from datetime import datetime 


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    
    
class PowerUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    usage_kwh = db.Column(db.Float, nullable=False)
    cabinet_name = db.Column(db.String(100), nullable=False)
    entered_by = db.Column(db.String(100), nullable=False)
    
class CPMSLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    flow_chill = db.Column(db.Float)
    tempS = db.Column(db.Float)
    tempR = db.Column(db.Float)
    tempSCL = db.Column(db.Float)
    tempRCL = db.Column(db.Float)
    chill_btuhr = db.Column(db.Float)
    chill_ton = db.Column(db.Float)
    cooling_btuhr = db.Column(db.Float)
    cooling_ton = db.Column(db.Float)