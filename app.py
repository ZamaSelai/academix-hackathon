# app.py - Flask Server for AcademiX

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import json
import hashlib
import os
import tempfile
import PyPDF2
from datetime import datetime
from verifier import EssayVerifier

app = Flask(__name__)
app.secret_key = 'academix-super-secret-key-2026'
CORS(app)

# Initialize AI verifier
verifier = EssayVerifier()

# ---------- USER DATABASE ----------
def load_users():
    try:
        with open("users.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

# ---------- ROUTES ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    users = load_users()

    if email in users and verify_password(password, users[email]['password']):
        # ✅ Session is set here
        session['user_email'] = email
        session['user_role'] = users[email]['role']
        session.permanent = True

        return jsonify({
            'success': True,
            'role': users[email]['role'],
            'name': users[email].get('full_name', email.split('@')[0]),
            'email': email,
            'wallet': users[email].get('wallet', 0),
            'strikes': users[email].get('strikes', 0)
        })   # ← Add this closing parenthesis!

    return jsonify({'success': False, 'error': 'Invalid email or password'})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    role = data.get('role', 'student')
    
    users = load_users()
    
    if data.get('email') in users:
        return jsonify({'success': False, 'error': 'Email already registered'})
    
    if role == 'student':
        user_data = {
            'password': hash_password(data.get('password')),
            'role': 'scribe',
            'full_name': data.get('full_name'),
            'email': data.get('email'),
            'student_num': data.get('student_num'),
            'id_num': data.get('id_num'),
            'university': data.get('university'),
            'faculty': data.get('faculty', ''),
            'degree': data.get('degree', ''),
            'year': data.get('year', '1'),
            'interests': data.get('interests', ''),
            'wallet': 0.00,
            'strikes': 0,
            'submissions': [],
            'verified': False,
            'created_at': datetime.now().isoformat()
        }
    else:
        user_data = {
            'password': hash_password(data.get('password')),
            'role': 'patron',
            'company_name': data.get('company_name'),
            'email': data.get('email'),
            'reg_number': data.get('reg_number'),
            'contact_person': data.get('contact_person'),
            'address': data.get('address', ''),
            'wallet': 0.00,
            'verified': False,
            'created_at': datetime.now().isoformat()
        }
    
    users[data.get('email')] = user_data
    save_users(users)
    
    return jsonify({'success': True, 'message': 'Account created successfully'})

@app.route('/api/upload', methods=['POST'])
def upload_essay():
    jsonify({'success': False, 'error': 'Could not read text from PDF'})
    # Get email from session or from request
    email = session.get('user_email')
    if not email:
        email = request.form.get('email')

    if not email:
        return jsonify({'success': False, 'error': 'Please login first'})
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    title = request.form.get('title', 'Untitled')
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    # Save and process file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        file.save(tmp_file.name)
        tmp_path = tmp_file.name
    
    try:
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(tmp_path)
        essay_text = ""
        for page in pdf_reader.pages:
            essay_text += page.extract_text() or ""
        
        if not essay_text.strip():
            return jsonify({'success': False, 'error': 'Could not read text from PDF'})
        
        # Run AI verification
        originality = verifier.get_originality_score(essay_text)
        academic_score = verifier.check_academic_tone(essay_text)
        word_count = verifier.count_words(essay_text)
        similarity = verifier.get_similarity_score(essay_text)
        is_published = verifier.check_against_known_sources(essay_text)
        
        earnings = round(word_count * 0.02, 2)
        
        # Check if published
        if is_published:
            return jsonify({
                'success': False,
                'error': 'Published content detected',
                'strike': True,
                'originality': originality,
                'academic_score': academic_score,
                'similarity': similarity,
                'word_count': word_count
            })
        
        # Check similarity
        if similarity > 15:
            # Add strike
            users = load_users()
            email = session['user_email']
            if email in users:
                users[email]['strikes'] = users[email].get('strikes', 0) + 1
                save_users(users)
            
            return jsonify({
                'success': False,
                'error': 'High similarity detected',
                'strike': True,
                'originality': originality,
                'academic_score': academic_score,
                'similarity': similarity,
                'word_count': word_count
            })
        
        # Check if it passes
        if originality >= 70 and academic_score >= 40:
            # Add earnings
            users = load_users()
            email = session['user_email']
            if email in users:
                users[email]['wallet'] = users[email].get('wallet', 0) + earnings
                submission = {
                    'title': title,
                    'date': datetime.now().strftime("%Y-%m-%d"),
                    'words': word_count,
                    'originality': originality,
                    'academic': academic_score,
                    'similarity': similarity,
                    'earnings': earnings,
                    'status': 'Verified'
                }
                if 'submissions' not in users[email]:
                    users[email]['submissions'] = []
                users[email]['submissions'].append(submission)
                save_users(users)
            
            return jsonify({
                'success': True,
                'message': 'Essay verified!',
                'originality': originality,
                'academic_score': academic_score,
                'similarity': similarity,
                'word_count': word_count,
                'earnings': earnings,
                'status': 'Verified'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Essay needs improvement',
                'originality': originality,
                'academic_score': academic_score,
                'similarity': similarity,
                'word_count': word_count
            })
    
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    if 'user_email' not in session:
        return jsonify({'success': False, 'error': 'Please login'})
    
    users = load_users()
    email = session['user_email']
    
    if email not in users:
        return jsonify({'success': False, 'error': 'User not found'})
    
    user = users[email]
    return jsonify({
        'success': True,
        'name': user.get('full_name', email.split('@')[0]),
        'email': email,
        'role': user.get('role', 'scribe'),
        'wallet': user.get('wallet', 0),
        'strikes': user.get('strikes', 0),
        'submissions': user.get('submissions', []),
        'verified': user.get('verified', False)
    })

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/verify', methods=['POST'])
def verify_user():
    if 'user_email' not in session:
        return jsonify({'success': False, 'error': 'Please login'})
    
    users = load_users()
    email = session['user_email']
    
    if email in users:
        users[email]['verified'] = True
        save_users(users)
        return jsonify({'success': True, 'message': 'User verified'})
    
    return jsonify({'success': False, 'error': 'User not found'})

@app.route('/api/save-bank', methods=['POST'])
def save_bank():
    if 'user_email' not in session:
        return jsonify({'success': False, 'error': 'Please login'})
    
    data = request.json
    users = load_users()
    email = session['user_email']
    
    if email in users:
        users[email]['bank_details'] = {
            'holder': data.get('holder'),
            'bank': data.get('bank'),
            'account': data.get('account'),
            'type': data.get('type', 'Cheque'),
            'branch': data.get('branch', '')
        }
        save_users(users)
        return jsonify({'success': True, 'message': 'Bank details saved'})
    
    return jsonify({'success': False, 'error': 'User not found'})

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5001)

@app.route('/api/withdraw', methods=['POST'])
def withdraw():
    # Get email from session or request
    email = session.get('user_email')
    if not email:
        email = request.json.get('email')
    
    if not email:
        return jsonify({'success': False, 'error': 'Please login first'})
    
    users = load_users()
    
    if email not in users:
        return jsonify({'success': False, 'error': 'User not found'})
    
    # Get the amount to withdraw
    amount = request.json.get('amount', 0)
    current_wallet = users[email].get('wallet', 0)
    
    if amount <= 0:
        return jsonify({'success': False, 'error': 'Invalid amount'})
    
    if current_wallet < amount:
        return jsonify({'success': False, 'error': 'Insufficient balance'})
    
    # Deduct from wallet
    users[email]['wallet'] = current_wallet - amount
    
    # Add transaction
    if 'transactions' not in users[email]:
        users[email]['transactions'] = []
    users[email]['transactions'].append({
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'activity': 'Withdrawal',
        'amount': -amount,
        'status': 'Completed'
    })
    
    save_users(users)
    
    return jsonify({
        'success': True,
        'message': 'Withdrawal successful',
        'new_balance': users[email]['wallet']
    })
