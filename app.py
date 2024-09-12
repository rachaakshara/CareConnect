from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# In-memory storage
users = {'donor': [], 'recipient': []}
medicines = []
requests = []

UPLOAD_FOLDER = 'uploads/prescriptions'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create the upload folder if it does not exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users[user_type].append({'username': username, 'password': password})
        return redirect(url_for('login', user_type=user_type))
    return render_template('register.html', user_type=user_type)

@app.route('/login/<user_type>', methods=['GET', 'POST'])
def login(user_type):
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = next((u for u in users[user_type] if u['username'] == username and u['password'] == password), None)
        if user:
            session['username'] = username
            session['user_type'] = user_type
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid credentials'
    return render_template('login.html', user_type=user_type)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('home'))
    if session['user_type'] == 'donor':
        return render_template('donor_dashboard.html', medicines=medicines, requests=requests)
    else:
        return render_template('recipient_dashboard.html', medicines=medicines)

@app.route('/add_medicine', methods=['POST'])
def add_medicine():
    if 'username' in session and session['user_type'] == 'donor':
        medicine = {
            'id': str(uuid.uuid4()),
            'donor': session['username'],
            'name': request.form['name'],
            'batch_number': request.form['batch_number'],
            'expiry_date': request.form['expiry_date'],
            'manufacturing_date': request.form['manufacturing_date'],
            'details': request.form['details']
        }
        medicines.append(medicine)
    return redirect(url_for('dashboard'))

@app.route('/search_medicine', methods=['GET', 'POST'])
def search_medicine():
    if request.method == 'POST':
        search_query = request.form['search']
        search_results = [m for m in medicines if search_query.lower() in m['name'].lower()]
        return render_template('medicine_search.html', search_results=search_results)
    return render_template('medicine_search.html', search_results=[])

@app.route('/request_medicine/<medicine_name>', methods=['GET', 'POST'])
def request_medicine(medicine_name):
    if 'username' not in session or session['user_type'] != 'recipient':
        return redirect(url_for('login', user_type='recipient'))

    if request.method == 'POST':
        prescription = request.files['prescription']
        if prescription and allowed_file(prescription.filename):
            filename = secure_filename(prescription.filename)
            prescription.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            request_info = {
                'id': str(uuid.uuid4()),
                'recipient': session['username'],
                'medicine': medicine_name,
                'details': request.form['details'],
                'prescription': filename
            }
            requests.append(request_info)
            return redirect(url_for('dashboard'))
    return render_template('request_form.html', medicine_name=medicine_name)

@app.route('/view_request/<request_id>')
def view_request(request_id):
    if 'username' in session and session['user_type'] == 'donor':
        request_info = next((r for r in requests if r['id'] == request_id), None)
        if request_info:
            return render_template('view_request.html', request_info=request_info)
    return redirect(url_for('home'))

@app.route('/uploads/prescriptions/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_type', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
