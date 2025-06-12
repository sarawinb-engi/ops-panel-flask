from flask import Flask, render_template, request, redirect, send_file, session, flash, make_response
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash
from utils import m3h2gpm, cooling, chiller
from extension import db
import pandas as pd 
import io

app = Flask(__name__) 


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base_fmt.db'
app.secret_key = 'amt@fmt_fb01'  # ใช้รหัสที่ปลอดภัย
db.init_app(app)
from models import User, PowerUsage, CPMSLog


CABINETS = [
    "MDB-PN-01", "8DB-1PN-01", "1DB-1P-01", "8DB-1PN-02", "1DB-P-02",
    "PVDB-2.5PN-02", "MDB-PN-02", "9DB-1.5.5PN-01", "1DB-1N-01", "6DB-2P-01",
    "1DB-1N-02", "MDB-P-01", "3DB-1P-01", "PVDB-2.5P-01", "ESS-P-01 (Box 3)",
    "2DB-1P-01 & 4DB-1P-01", "2DB-1P-01", "4DB-1P-01", "MDB-P-02", "5DB-2P-01",
    "5DB-2P-02", "PVDB-2.5P-02", "MDB-P-03", "7DB-2P-02", "7DB-2P-06",
    "ESS-P-03 (Box 5)", "7DB-2P-01", "7DB-2P-05", "MDB-P-04", "7DB-2P-03",
    "7DB-2P-07", "7DB-2P-08", "MDB-N-01", "3DB-1N-01", "PVDB-2.5N-01",
    "2EDB-1N-01 Anode", "2EDB-1P-01 Cathode", "ESS-N-01 (Box 4)",
    "2DB-1N-01 & 4DB-1N-01", "2DB-1N-01", "4DB-1N-01"
]

@app.route('/') 
def home():
    return render_template('home.html')

    
    
@app.route('/login', methods=['GET', 'POST']) 
def login(): 
    if request.method == 'POST': 
        email = request.form.get('email') 
        password = request.form.get('password') 
        
        if email and password: 
            user = User.query.filter_by(email=email).first() 
            
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['username'] = user.username 
                flash('Login Success!', 'success') 
                return redirect('/menu') 
            else: 
                flash('Emain or Password Not Found', 'danger') 
        
        else :
            flash('Please Enter yours Emain and Password', 'danger') 
            
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST']) 
def signup():
    
    if request.method == 'POST': 
        username = request.form['username'] 
        email = request.form['email'] 
        password = request.form['password'] 
        
        existing_user = User.query.filter_by(email=email).first() 
        if existing_user: 
            flash('This email has already been used.', 'danger')
            return redirect('/signup')
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(username=username, email=email, password=hashed_password) 
        db.session.add(new_user) 
        db.session.commit() 
        
        flash("Successfully subscribed! Please Login", 'success') 
        return redirect('/login')
 
    return render_template('signup.html')        

@app.route('/logout')
def logout(): 
    session.clear()
    
    return redirect('/login')



@app.route('/menu', methods=['GET', 'POST'], endpoint='menu') 
def manu(): 
    if 'user_id' not in session: 
        return redirect('/login') 
    username = session.get('username') 
    return render_template('menu.html', username=username)


@app.route('/cpms', methods=['GET', 'POST'])
def cal_cpms(): 
    if 'user_id' not in session: 
        return redirect('/login') 
    
    username = session.get('username') 
    result_data = None 
    if request.method == 'POST':
        try : 
            flow_chill = float(request.form['flow']) 
            tempS = float(request.form['tempS'])
            tempR = float(request.form['tempR']) 
            tempSCL = float(request.form['tempSCL']) 
            tempRCL = float(request.form['tempRCL']) 
            
            
        # Calculations 
            chill_flow = m3h2gpm(flow_chill)
            chill_btu, chill_ton  = chiller(chill_flow, tempR, tempS) 
            cool_flow = 2111.2 
            cool_btu, cool_ton = cooling(cool_flow, tempSCL, tempRCL)
            
            log = CPMSLog(
                user_id = session['user_id'], 
                flow_chill=flow_chill, 
                tempS=tempS,
                tempR=tempR,
                tempSCL=tempSCL,
                tempRCL=tempRCL,
                chill_btuhr=chill_btu,
                chill_ton=chill_ton,
                cooling_btuhr=cool_btu,
                cooling_ton=cool_ton
            )
            
            db.session.add(log)
            db.session.commit()
        
            result_data = {
                'chiller_btuhr': chill_btu,
                'chiller_ton': chill_ton,
                'cooling_btuhr': cool_btu,
                'cooling_ton': cool_ton
            }
 
            
        except ValueError:
            result_data = {'error' : 'please enter your value'}
        except Exception as e: 
            result_data = {'error' : f'Error : {e}'} 
            
    return render_template('cpms.html', result=result_data, username=username)

@app.route('/power_usage', methods=['GET', 'POST'], endpoint='poweruse')
def poweruse():
    if 'user_id' not in session:
        return redirect('/login')

    username = session.get('username') 
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            entered_by = session.get('username')
            total = int(request.form.get('total_cabinet'))

            unit_multiplier = {
                "Wh": 1 / 1000,
                "kWh": 1,
                "MWh": 1000,
                "GWh": 1000000
            }

            count = 0
            for i in range(1, total + 1):
                cabinet = request.form.get(f'cabinet_{i}')
                usage_raw = request.form.get(f'usage_{i}')
                unit = request.form.get(f'unit_{i}')

                if usage_raw:
                    usage_kwh = float(usage_raw) * unit_multiplier.get(unit, 1)

                    # ตรวจสอบซ้ำ
                    existing = PowerUsage.query.filter_by(date=date, cabinet_name=cabinet).first()
                    if existing:
                        continue

                    new_entry = PowerUsage(
                        date=date,
                        cabinet_name=cabinet,
                        usage_kwh=usage_kwh,
                        entered_by=entered_by
                    )
                    db.session.add(new_entry)
                    count += 1

            db.session.commit()
            flash(f'Saved {count} entries successfully', 'success')
            return redirect('/result_data')  # ✅ REDIRECT ตรงนี้
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            print("FORM ERROR:", str(e))  # ✅ DEBUG LOG

    # กรณี GET หรือ error
    today = datetime.today().date()
    previous_data = PowerUsage.query.filter_by(date=today).all()

    return render_template('power_usage.html',
                           cabinets=CABINETS,
                           previous_data=previous_data, 
                           username=username)


    
@app.route('/result_data')
def results():
    if 'user_id' not in session:
        return redirect('/login')

    today = datetime.today().date()
    username = session.get('username')

    # ดึงข้อมูลที่เพิ่งกรอกวันนี้โดย user นี้
    submitted_data = PowerUsage.query.filter_by(date=today, entered_by=username).all()

    return render_template('confirmation.html', data=submitted_data, 
                           username=username)


@app.route('/cpms_log')
def cpms_log():
    if 'user_id' not in session:
        return redirect('/login')
    
    username = session.get('username')
    logs = CPMSLog.query.order_by(CPMSLog.timestamp.desc()).all()
    return render_template('cpms_log.html', logs=logs, username=username)



@app.route('/result_data/export/excel')
def result_export_excel(): 
    data = PowerUsage.query.all() 
    df = pd.DataFrame([(
        d.date, d.usage_kwh, d.cabinet_name, d.entered_by) for d in data],
        columns=["Date", "Usage_kwh", "Cabinet", "Entered_By"])
    output = io.BytesIO() 
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False) 
    output.seek(0) 
        
    return send_file(output, 
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    as_attachment=True, 
                    download_name='Power_consumption.xlsx' )
    
@app.route('/cpms_log/export/excel')
def cpms_export_excel(): 
    data = CPMSLog.query.all() 
    df = pd.DataFrame([(
        d.date, d.timestamp, d.flow_chill, d.tempS, 
        d.tempR, d.tempSCL, d.tempRCL, d.chill_btuhr, d.chill_ton,
        d.cooling_btuhr, d.cooling_ton) for d in data],
        columns=["Date", "Timestamp", "Flow Chill", "TempS", 
                 "TempR", "TempSCL", "TempRCL", "Chill_BTU", "Chill_Ton",
                 "Cooling_BTU", "Cooling_Ton"])
    output = io.BytesIO() 
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False) 
    output.seek(0) 
        
    return send_file(output, 
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    as_attachment=True, 
                    download_name='CPMSLogs.xlsx' )

@app.route('/clear')
def clear_data():
    if 'user_id' not in session:
        return redirect('/login')

    db.session.query(PowerUsage).delete()
    db.session.query(CPMSLog).delete()
    db.session.commit()
    flash('ลบข้อมูลทั้งหมดเรียบร้อยแล้ว', 'success')
    return redirect('/')


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
    