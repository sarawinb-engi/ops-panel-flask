from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST" :
        username = request.form['username'] 
        password = request.form['password'] 
        
        # Checking username and password basic 
        if username == 'admin' and password == '1234':
            return render_template('index.html')
        else:
            return "❌ Invalid credentials"
        
    return render_template('login.html')
     
@app.route('/') 
def home():
    return render_template('index.html')


if __name__ == "__main__":
    app.run(debug=True)
