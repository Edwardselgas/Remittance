from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "remittance_secret_key"

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///remittance.db'
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

class Remittance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_name = db.Column(db.String(100))
    receiver_name = db.Column(db.String(100))
    amount = db.Column(db.Float)
    status = db.Column(db.String(50))
    date = db.Column(db.DateTime, default=datetime.now)

# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pword = request.form['password']
        user = User.query.filter_by(username=uname, password=pword).first()
        if user:
            session['user'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    total = Remittance.query.count()
    pending = Remittance.query.filter_by(status="Pending").count()
    completed = Remittance.query.filter_by(status="Completed").count()
    return render_template('dashboard.html', total=total, pending=pending, completed=completed)

@app.route('/add', methods=['GET', 'POST'])
def add_remittance():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        sender = request.form['sender']
        receiver = request.form['receiver']
        amount = request.form['amount']
        status = request.form['status']
        new_remit = Remittance(sender_name=sender, receiver_name=receiver, amount=amount, status=status)
        db.session.add(new_remit)
        db.session.commit()
        flash("Remittance record added successfully!", "success")
        return redirect(url_for('view_transactions'))
    return render_template('add_remittance.html')

@app.route('/transactions')
def view_transactions():
    if 'user' not in session:
        return redirect(url_for('login'))
    search = request.args.get('search')
    if search:
        remittances = Remittance.query.filter(
            (Remittance.sender_name.contains(search)) | (Remittance.receiver_name.contains(search))
        ).all()
    else:
        remittances = Remittance.query.all()
    return render_template('view_transactions.html', remittances=remittances)

@app.route('/delete/<int:id>')
def delete_record(id):
    if 'user' not in session:
        return redirect(url_for('login'))
    remit = Remittance.query.get(id)
    db.session.delete(remit)
    db.session.commit()
    flash("Record deleted successfully!", "info")
    return redirect(url_for('view_transactions'))

@app.route('/report')
def report():
    if 'user' not in session:
        return redirect(url_for('login'))
    remittances = Remittance.query.all()
    total_amount = sum(r.amount for r in remittances)
    return render_template('report.html', remittances=remittances, total=total_amount)

# Create database initially
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password='1234'))
        db.session.commit()

if __name__ == "__main__":
    app.run(debug=True)
