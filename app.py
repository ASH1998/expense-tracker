import os
import json
import csv
import pandas as pd
import yaml
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['DATA_DIR'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# Ensure data directory exists
os.makedirs(app.config['DATA_DIR'], exist_ok=True)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Load users from config.yaml
def load_users_from_config():
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            user_list = config.get('users', [])
            users_dict = {}
            for user in user_list:
                user_id = user.get('id')
                username = user.get('username')
                password = user.get('password')
                if user_id and username and password:
                    users_dict[user_id] = User(user_id, username, generate_password_hash(password))
            return users_dict
    return {}

# Initialize users from config
users = load_users_from_config()

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

# Default settings
DEFAULT_CATEGORIES = [
    "Food", "Groceries", "Travel", "Rent", "Utilities", 
    "Entertainment", "Healthcare", "Shopping", "Miscellaneous", "Income"
]

# Helper functions for data operations
def get_user_data_path(username):
    return os.path.join(app.config['DATA_DIR'], f"{username}_expenses.csv")

def get_user_settings_path(username):
    return os.path.join(app.config['DATA_DIR'], f"{username}_settings.json")

def initialize_user_data(username):
    data_path = get_user_data_path(username)
    if not os.path.exists(data_path):
        with open(data_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'date', 'type', 'category', 'amount', 'description'])
    
    settings_path = get_user_settings_path(username)
    if not os.path.exists(settings_path):
        settings = {
            'categories': DEFAULT_CATEGORIES,
            'currency': 'INR (₹)',
            'start_date': 1  # Day of month to start tracking
        }
        with open(settings_path, 'w') as file:
            json.dump(settings, file)
    
    return True

def load_user_expenses(username):
    try:
        data_path = get_user_data_path(username)
        if os.path.exists(data_path):
            # Open the file with explicit encoding and verify it has content
            with open(data_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:  # If file is empty, initialize it
                    df = pd.DataFrame(columns=['id', 'date', 'type', 'category', 'amount', 'description'])
                    df.to_csv(data_path, index=False)
                    return df
            
            # Read the CSV with specified parameters
            df = pd.read_csv(data_path, encoding='utf-8')
            
            # Debug: Print record count
            print(f"Loaded {len(df)} records from {data_path}")
            
            # Convert date strings to datetime objects with more flexible parsing
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            # Drop any rows with invalid dates
            df = df.dropna(subset=['date'])
            return df
        return pd.DataFrame(columns=['id', 'date', 'type', 'category', 'amount', 'description'])
    except Exception as e:
        print(f"Error loading expenses: {str(e)}")
        return pd.DataFrame(columns=['id', 'date', 'type', 'category', 'amount', 'description'])

def load_user_settings(username):
    settings_path = get_user_settings_path(username)
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as file:
            return json.load(file)
    return {
        'categories': DEFAULT_CATEGORIES,
        'currency': 'INR (₹)',
        'start_date': 1
    }

def save_user_settings(username, settings):
    settings_path = get_user_settings_path(username)
    with open(settings_path, 'w') as file:
        json.dump(settings, file)
    return True

# Routes
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = next((u for u in users.values() if u.username == username), None)
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            initialize_user_data(user.username)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    df = load_user_expenses(current_user.username)
    settings = load_user_settings(current_user.username)
    
    # Calculate summary stats
    if not df.empty:
        # Force amount to numeric to ensure proper calculation
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        
        # Calculate totals with explicit grouping
        earnings = df[df['type'] == 'Earning']['amount'].sum()
        spends = df[df['type'] == 'Spend']['amount'].sum()
        investments = df[df['type'] == 'Investment']['amount'].sum()
        savings = earnings - spends
        
        print(f"Dashboard calculations - Earnings: {earnings}, Spends: {spends}, Investments: {investments}")
        
        # Get latest 5 records and ensure they have the right format for template
        latest_records = df.sort_values('date', ascending=False).head(5)
        latest_records_list = latest_records.to_dict('records')
        
        # Monthly breakdown for chart (last 12 months)
        df['month'] = df['date'].dt.strftime('%Y-%m')
        monthly_data = {}
        for type_val in ['Earning', 'Spend', 'Investment']:
            type_df = df[df['type'] == type_val]
            monthly_data[type_val] = type_df.groupby('month')['amount'].sum().to_dict()
    else:
        earnings, spends, investments, savings = 0, 0, 0, 0
        latest_records_list = []
        monthly_data = {'Earning': {}, 'Spend': {}, 'Investment': {}}
    
    return render_template('dashboard.html', 
                          earnings=earnings, spends=spends, 
                          investments=investments, savings=savings,
                          latest_records=latest_records_list,
                          monthly_data=json.dumps(monthly_data),
                          settings=settings)

@app.route('/analysis')
@login_required
def analysis():
    df = load_user_expenses(current_user.username)
    settings = load_user_settings(current_user.username)
    
    # Process data for charts
    if not df.empty:
        # Category breakdown for pie chart
        category_data = df[df['type'] == 'Spend'].groupby('category')['amount'].sum().to_dict()
        
        # Monthly trend for all types
        df['month'] = df['date'].dt.strftime('%Y-%m')
        monthly_trends = df.groupby(['month', 'type'])['amount'].sum().reset_index()
        monthly_trends_dict = monthly_trends.pivot(index='month', columns='type', values='amount').fillna(0).to_dict('index')
        
        # Yearly trends
        df['year'] = df['date'].dt.year
        yearly_trends = df.groupby(['year', 'type'])['amount'].sum().reset_index()
        yearly_trends_dict = yearly_trends.pivot(index='year', columns='type', values='amount').fillna(0).to_dict('index')
    else:
        category_data = {}
        monthly_trends_dict = {}
        yearly_trends_dict = {}
    
    return render_template('analysis.html', 
                          category_data=json.dumps(category_data),
                          monthly_trends=json.dumps(monthly_trends_dict),
                          yearly_trends=json.dumps(yearly_trends_dict),
                          settings=settings)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    current_settings = load_user_settings(current_user.username)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save_categories':
            categories = [cat.strip() for cat in request.form.getlist('categories[]') if cat.strip()]
            current_settings['categories'] = categories
            save_user_settings(current_user.username, current_settings)
            flash('Categories saved successfully')
        
        elif action == 'save_currency':
            currency = request.form.get('currency')
            if currency:
                current_settings['currency'] = currency
                save_user_settings(current_user.username, current_settings)
                flash('Currency setting saved successfully')
        
        elif action == 'save_start_date':
            start_date = request.form.get('start_date')
            if start_date and start_date.isdigit() and 1 <= int(start_date) <= 31:
                current_settings['start_date'] = int(start_date)
                save_user_settings(current_user.username, current_settings)
                flash('Start date setting saved successfully')
        
        return redirect(url_for('settings'))
    
    return render_template('settings.html', settings=current_settings)

@app.route('/expenses', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_expenses():
    if request.method == 'GET':
        df = load_user_expenses(current_user.username)
        settings = load_user_settings(current_user.username)
        return render_template('expenses.html', expenses=df.to_dict('records'), settings=settings)
    
    elif request.method == 'POST':
        data_path = get_user_data_path(current_user.username)
        
        date = request.form.get('date')
        expense_type = request.form.get('type')
        category = request.form.get('category')
        amount = request.form.get('amount')
        description = request.form.get('description')
        
        if not all([date, expense_type, category, amount]):
            flash('All fields are required')
            return redirect(url_for('manage_expenses'))
        
        try:
            # Force amount to be float
            amount = float(amount)
            
            # Read existing data first to ensure we don't lose records
            existing_data = []
            if os.path.exists(data_path) and os.path.getsize(data_path) > 0:
                try:
                    with open(data_path, 'r', encoding='utf-8') as f:
                        # Read and parse CSV manually to avoid pandas issues
                        import csv
                        reader = csv.DictReader(f)
                        for row in reader:
                            existing_data.append(row)
                except Exception as e:
                    print(f"Error reading existing file: {str(e)}")
            
            # Find the highest ID or start at 1
            max_id = 0
            for record in existing_data:
                try:
                    record_id = int(record['id'])
                    if record_id > max_id:
                        max_id = record_id
                except (ValueError, KeyError):
                    pass
            
            new_id = max_id + 1
            
            # Format the date consistently (without time component)
            formatted_date = date  # Already in YYYY-MM-DD format from the form
            
            # Create new record
            new_record = {
                'id': str(new_id),
                'date': formatted_date,
                'type': expense_type,
                'category': category,
                'amount': str(amount),
                'description': description or ''
            }
            
            # Add to existing data
            existing_data.append(new_record)
            
            # Write all data back to file
            with open(data_path, 'w', newline='', encoding='utf-8') as f:
                if existing_data:
                    writer = csv.DictWriter(f, fieldnames=['id', 'date', 'type', 'category', 'amount', 'description'])
                    writer.writeheader()
                    writer.writerows(existing_data)
            
            # Print debug info
            print(f"Added new record with ID {new_id}. Total records: {len(existing_data)}")
            print(f"CSV file size after write: {os.path.getsize(data_path)} bytes")
            
            flash('Expense added successfully')
            
        except Exception as e:
            error_msg = f'Error adding expense: {str(e)}'
            print(f"EXCEPTION: {error_msg}")
            flash(error_msg)
        
        return redirect(url_for('manage_expenses'))

@app.route('/expenses/<int:expense_id>', methods=['PUT', 'DELETE'])
@login_required
def expense_operations(expense_id):
    data_path = get_user_data_path(current_user.username)
    df = load_user_expenses(current_user.username)
    
    if request.method == 'PUT':
        data = request.get_json()
        
        try:
            # Find the record by ID and update it
            idx = df[df['id'] == expense_id].index[0]
            for key, value in data.items():
                if key in df.columns:
                    df.at[idx, key] = value
            
            df.to_csv(data_path, index=False)
            return jsonify({'success': True, 'message': 'Expense updated successfully'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error updating expense: {str(e)}'}), 400
    
    elif request.method == 'DELETE':
        try:
            # Remove the record by ID
            df = df[df['id'] != expense_id]
            df.to_csv(data_path, index=False)
            return jsonify({'success': True, 'message': 'Expense deleted successfully'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error deleting expense: {str(e)}'}), 400

@app.route('/api/expenses')
@login_required
def api_expenses():
    df = load_user_expenses(current_user.username)
    
    # Apply filters if provided
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')
    expense_type = request.args.get('type')
    
    if start_date:
        df = df[df['date'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['date'] <= pd.to_datetime(end_date)]
    if category:
        df = df[df['category'] == category]
    if expense_type:
        df = df[df['type'] == expense_type]
    
    # Convert dates to string for JSON serialization
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
    
    return jsonify(df.to_dict('records'))

@app.route('/import_export', methods=['GET', 'POST'])
@login_required
def import_export():
    settings = load_user_settings(current_user.username)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'export_csv':
            # We'll return the current data as a download
            data_path = get_user_data_path(current_user.username)
            if os.path.exists(data_path):
                return send_file(data_path, as_attachment=True, download_name=f"{current_user.username}_expenses.csv")
            else:
                flash('No data to export')
        
        elif action == 'export_json':
            df = load_user_expenses(current_user.username)
            if not df.empty:
                # Convert to JSON format
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                json_data = df.to_dict('records')
                
                # Save to temp file and return
                json_path = os.path.join(app.config['DATA_DIR'], f"{current_user.username}_expenses.json")
                with open(json_path, 'w') as f:
                    json.dump(json_data, f)
                
                return send_file(json_path, as_attachment=True, download_name=f"{current_user.username}_expenses.json")
            else:
                flash('No data to export')
        
        elif action == 'import_csv':
            if 'file' not in request.files:
                flash('No file selected')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected')
                return redirect(request.url)
            
            if not file.filename.endswith('.csv'):
                flash('Only CSV files are allowed')
                return redirect(request.url)
            
            try:
                # Read the uploaded file
                df = pd.read_csv(file)
                
                # Validate required columns
                required_cols = ['date', 'type', 'category', 'amount', 'description']
                if not all(col in df.columns for col in required_cols):
                    flash('Invalid format: Missing required columns')
                    return redirect(request.url)
                
                # Convert date strings to datetime objects
                df['date'] = pd.to_datetime(df['date'])
                
                # Generate IDs if not present
                if 'id' not in df.columns:
                    df['id'] = range(1, len(df) + 1)
                
                # Save to user's data file
                data_path = get_user_data_path(current_user.username)
                df.to_csv(data_path, index=False)
                
                flash('Data imported successfully')
            except Exception as e:
                flash(f'Error importing data: {str(e)}')
        
        elif action == 'import_json':
            if 'file' not in request.files:
                flash('No file selected')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected')
                return redirect(request.url)
            
            if not file.filename.endswith('.json'):
                flash('Only JSON files are allowed')
                return redirect(request.url)
            
            try:
                # Read the uploaded JSON file
                json_data = json.load(file)
                
                # Convert to DataFrame
                df = pd.DataFrame(json_data)
                
                # Validate required columns
                required_cols = ['date', 'type', 'category', 'amount', 'description']
                if not all(col in df.columns for col in required_cols):
                    flash('Invalid format: Missing required columns')
                    return redirect(request.url)
                
                # Convert date strings to datetime objects
                df['date'] = pd.to_datetime(df['date'])
                
                # Generate IDs if not present
                if 'id' not in df.columns:
                    df['id'] = range(1, len(df) + 1)
                
                # Save to user's data file
                data_path = get_user_data_path(current_user.username)
                df.to_csv(data_path, index=False)
                
                flash('Data imported successfully')
            except Exception as e:
                flash(f'Error importing data: {str(e)}')
    
    return render_template('import_export.html', settings=settings)

@app.route('/profile')
@login_required
def profile():
    # Load user settings and expenses to display in profile
    settings = load_user_settings(current_user.username)
    df = load_user_expenses(current_user.username)
    expenses = df.to_dict('records') if not df.empty else []
    
    return render_template('profile.html', user=current_user, settings=settings, expenses=expenses)

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=True)