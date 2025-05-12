from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
app.config['APP_NAME'] = 'DonePath'
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Models
class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	full_name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	username = db.Column(db.String(80), unique=True, nullable=False)
	password = db.Column(db.String(200), nullable=False)
	tasks = db.relationship('Task', backref='user', lazy=True)

class Task(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	content = db.Column(db.String(200), nullable=False)
	completed = db.Column(db.Boolean, default=False)
	priority = db.Column(db.Integer, default=1)
	due_date = db.Column(db.Date, nullable=True)
	due_time = db.Column(db.Time, nullable=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))

# Routes

@app.route('/')
@login_required
def home():
	today = date.today()
	priority_filter = request.args.get("priority")
	status_filter = request.args.get("status")

	base_query = Task.query.filter_by(user_id=current_user.id)

	if priority_filter:
		try:
			priority_filter = int(priority_filter)
			base_query = base_query.filter_by(priority=priority_filter)
		except ValueError:
			pass

	if status_filter == "overdue":
		base_query = base_query.filter(Task.completed == False, Task.due_date < today)
	elif status_filter == "upcoming":
		base_query = base_query.filter(Task.completed == False, (Task.due_date == None) | (Task.due_date >= today))
	elif status_filter == "completed":
		base_query = base_query.filter_by(completed=True)

	overdue_tasks = base_query.filter(Task.completed == False, Task.due_date < today).order_by(Task.due_date.asc(), Task.priority.desc()).all()
	upcoming_tasks = base_query.filter(Task.completed == False, (Task.due_date == None) | (Task.due_date >= today)).order_by(Task.due_date.asc().nullslast(), Task.priority.desc()).all()
	completed_tasks = base_query.filter(Task.completed == True).order_by(Task.due_date.asc().nullslast(), Task.priority.desc()).all()

	return render_template("home.html", overdue_tasks=overdue_tasks, upcoming_tasks=upcoming_tasks, completed_tasks=completed_tasks, current_date=today,app_name=app.config['APP_NAME'])

@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if request.method == 'POST':
		full_name = request.form['full_name'].strip()
		email = request.form['email'].strip().lower()
		username = request.form['username'].strip().lower()
		password = request.form['password']

		print(f"📨 Signup attempt: {username}, {email}, {full_name}")

		if User.query.filter_by(username=username).first():
			flash('❌ Username already exists.')
			return redirect(url_for('signup'))

		if User.query.filter_by(email=email).first():
			flash('❌ Email already registered.')
			return redirect(url_for('signup'))

		hashed_password = generate_password_hash(password)
		new_user = User(full_name=full_name, email=email, username=username, password=hashed_password)

		db.session.add(new_user)
		db.session.commit()

		flash('✅ Account created! Please log in.')
		return redirect(url_for('login'))

	return render_template('signup.html', app_name=app.config['APP_NAME'])


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user:
            print(f"👤 User found: {user.username}")
            print(f"🔐 Stored hash: {user.password}")
        else:
            print("❌ No user found")

        # Check password
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('✅ Logged in successfully!')
            print("✅ Login successful")
            return redirect(url_for('home'))
        else:
            flash('❌ Invalid username or password.')
            print("🚫 Login failed")
            return redirect(url_for('login'))

    return render_template('login.html', app_name=app.config['APP_NAME'])


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))

@app.route("/add", methods=["POST"])
@login_required
def add():
	task_content = request.form.get("content")
	due_date_str = request.form.get("due_date")
	due_time_str = request.form.get("due_time")
	priority = int(request.form.get("priority", 1))

	due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
	due_time = datetime.strptime(due_time_str, "%H:%M").time() if due_time_str else None

	if task_content:
		new_task = Task(
			content=task_content,
			due_date=due_date,
			due_time=due_time,
			priority=priority,
			user_id=current_user.id
		)
		db.session.add(new_task)
		db.session.commit()
		flash('Task Added Successfully!')
	return redirect(url_for("home"))

@app.route("/delete/<int:id>")
@login_required
def delete(id):
	task_to_delete = Task.query.get_or_404(id)
	if task_to_delete.user_id != current_user.id:
		flash("Not authorized to delete this task.")
		return redirect(url_for("home"))

	db.session.delete(task_to_delete)
	db.session.commit()
	flash('Task Deleted Successfully!')
	return redirect(url_for("home"))

@app.route("/complete/<int:id>")
@login_required
def complete(id):
	task = Task.query.get_or_404(id)
	if task.user_id != current_user.id:
		flash("Not authorized to update this task.")
		return redirect(url_for("home"))

	task.completed = not task.completed
	db.session.commit()
	flash('Task updated successfully!')
	return redirect(url_for("home"))

@app.route("/edit/<int:id>", methods=["POST"])
@login_required
def edit(id):
	task = Task.query.get_or_404(id)
	if task.user_id != current_user.id:
		flash("Not authorized to edit this task.")
		return redirect(url_for("home"))

	task.content = request.form.get("content")
	due_date_str = request.form.get("due_date")
	due_time_str = request.form.get("due_time")
	task.due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date() if due_date_str else None
	task.due_time = datetime.strptime(due_time_str, "%H:%M").time() if due_time_str else None
	task.priority = int(request.form.get("priority"))
	db.session.commit()
	flash("Task updated successfully!")
	return redirect(url_for("home"))

if __name__ == "__main__":
	app.run(debug=True)
