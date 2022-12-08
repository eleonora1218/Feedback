"""Employee Feedback"""

from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import connect_db, db, User, Feedback
from forms import RegistrationForm, LoginForm, FeedbackForm,  DeleteForm, EditFeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "bunniesRbest"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

app.app_context().push()
connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)

@app.errorhandler(404)
def page_not_found(e):
    """Show 404 NOT FOUND page."""
    user = User.query.get(session['username'])
    return render_template('404.html', user=user), 404

@app.route('/')
def home_page():
    if 'username' in session:
        user = User.query.get(session['username'])
        return render_template('index.html', user=user)
    else:
        return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register_new_user():
    """New user registration form"""

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append('That username is already taken')
            return render_template('register.html', form=form)
        session['username'] = new_user.username
        return redirect(f"/users/{username}")
    else: 
        return render_template('register.html', form=form)

@app.route('/users/<username>')
def user_page(username):
    """User's profile page"""

    if 'username' not in session or username != session['username']:
        return redirect('/login')

    user = User.query.get(username)

    return render_template('user.html', user=user)

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    """Delete user"""

    if 'username' not in session or username != session['username']:
        return redirect('/register')

    user = User.query.get(username)     
    db.session.delete(user)
    db.session.commit()
    session.pop('username')

    return redirect('/register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login user form"""
    
    if 'username' in session:
        user = User.query.get(session['username'])
        return redirect(f"/users/{user.username}")

    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)

        if user:
            session['username'] = user.username
            return redirect(f'/users/{user.username}')
        else: 
            form.username.errors = ['Invalid username/password']
            return render_template("login.html", form=form)

    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Logs out user"""
    session.pop('username')
    return redirect('/login')

@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def feedback(username):
    """Form to provide feedback"""
    user = User.query.get(username)

    if 'username' not in session or username != session['username']:
        return redirect('/login')

    form = FeedbackForm()

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        feedback = Feedback(title=title, content=content, username=username)

        db.session.add(feedback)
        db.session.commit()
        return redirect(f"/users/{username}")
    
    else:
        return render_template('feedback.html', form=form, user=user)

@app.route('/feedback/<int:feedback_id>/update', methods=['GET', 'POST'])
def edit_feedback(feedback_id):
    """Form to edit feedback"""
    feedback = Feedback.query.get_or_404(feedback_id)
    user = User.query.get(feedback.username)

    if "username" not in session or feedback.username != session['username']:
        return redirect('/login')

    form = EditFeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.commit()
        return redirect(f"/users/{feedback.username}")
    
    else:
        return render_template('edit_feedback.html', form=form, feedback=feedback, user=user)

@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)
    if "username" not in session or feedback.username != session['username']:
        return redirect('/register')

    db.session.delete(feedback)
    db.session.commit()

    return redirect(f"/users/{feedback.username}")
