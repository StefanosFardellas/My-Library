from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import  FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.fields.html5 import EmailField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Required, Email, ValidationError, EqualTo
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_bcrypt import Bcrypt
import secrets, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Acb87Ui0IAJj2J1lMS0JSDXVYfsNYr532FT7H'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)], render_kw={"placeholder": "Username"})
    email = EmailField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "Email"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Sign up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(f'Username is taken. Please choose another one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(f'Email is taken. Please choose another one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')  

class UpdateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)], render_kw={"placeholder": "Edit Username"})
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"placeholder": "Edit Email"})
    profile_img = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username :
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(f'Username is taken. Please choose another one.')

    def validate_email(self, email):
        if email.data != current_user.email :
            user = User.query.filter_by(username=email.data).first()
            if user:
                raise ValidationError(f'Email is taken. Please choose anothre one.')

class NoteForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()], render_kw={"id":"exampleFormControlTextarea1", "rows":"10", "cols":"100", "maxlength":"250"})
    submit = SubmitField('Add')


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=1)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    profile_img = db.Column(db.String(20), default='default_profile_pic.jpg')
    notes = db.relationship('Notes', backref='author')
    books = db.relationship('MyBooks', backref='author')

    def __repr__(self):
        return "User " + str(self.id)

class Books(db.Model):
    id = db.Column(db.Integer, primary_key=1)
    title = db.Column(db.String(100), nullable=False)
    writer = db.Column(db.String(100), nullable=False, default='N/A')
    genre = db.Column(db.String(50), nullable=False, default='N/A')
    img = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return "Book " + str(self.id)

class MyBooks(db.Model):
    id = db.Column(db.Integer, primary_key=1)
    title = db.Column(db.String(100), nullable=False)
    writer = db.Column(db.String(100), nullable=False, default='N/A')
    genre = db.Column(db.String(50), nullable=False, default='N/A')
    img = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return "Book " + str(self.id)


class Notes(db.Model):
    id = db.Column(db.Integer, primary_key=1)
    content = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return "Note " + str(self.id)

@app.route('/')
def home_page():
    return render_template('home_page.html')

@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if current_user.is_authenticated:
        return redirect(url_for('mainpage'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account for { form.username.data } has been created!', 'success')
        return redirect(url_for('login'))
    return render_template("sign_up.html", title='Sign up', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('mainpage'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) :
            login_user(user)
            return redirect(url_for('mainpage'))
        else:
            flash(f"Login Unsuccessful. Please check username and password.")
    return render_template("login.html", title='Login', form=form)


@app.route('/main-page')
@login_required
def mainpage():
    books = Books.query.all()
    return render_template('main_page.html', books=books)

@app.route('/main-page/book/<int:id>', methods=['GET', 'POST'])
@login_required
def bookpage(id):
    book = Books.query.get_or_404(id)
    return render_template('bookpage.html', book=book)
    
@app.route('/main-page/book-genres/<string:genre>', methods=['GET', 'POST'])
@login_required
def bookgenres(genre):
    books = Books.query.filter_by(genre=genre).all()
    return render_template('book_list.html', books=books)

@app.route('/add-book/<int:id>')
@login_required
def addbook(id):
    book = Books.query.get_or_404(id)
    addbook = MyBooks(title=book.title, writer=book.writer, genre=book.genre, img=book.img, author=current_user, user_id=current_user.id)
    db.session.add(addbook)
    db.session.commit()
    return redirect(url_for('mybooks'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home_page'))


@app.route('/mybooks', methods=['GET', 'POST'])
@login_required
def mybooks():
    books = MyBooks.query.all()
    return render_template('mybooks.html', books=books)

@app.route('/mybooks/delete/<int:id>')
@login_required
def deletebook(id):
    book = MyBooks.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return redirect(url_for('mybooks'))

@app.route('/mynotes', methods=['GET', 'POST'])
@login_required
def mynotes():
    form = NoteForm()
    if form.validate_on_submit():
        note = Notes(content=form.content.data, author=current_user, user_id=current_user.id)
        db.session.add(note)
        db.session.commit()
        return redirect(url_for('mynotes'))
    notes = Notes.query.all()
    return render_template('mynotes.html', form=form, notes=notes)

@app.route('/mynotes/delete/<int:id>')
@login_required
def deletenote(id):
    note = Notes.query.get_or_404(id)
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for('mynotes'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename) 
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    form_picture.save(picture_path)

    return picture_fn

@app.route('/myprofile', methods=['GET', 'POST'])
@login_required
def myprofile():
    form = UpdateUserForm()
    if form.validate_on_submit():
        if form.profile_img.data:
            picture_file = save_picture(form.profile_img.data)
            current_user.profile_img = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account was successfully updated', 'success')
        return redirect(url_for('myprofile'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.profile_img)
    return render_template('myprofile.html', title='My Profile', profile_img=image_file, form=form)

if __name__ == "__main__":
    app.run(debug=True)