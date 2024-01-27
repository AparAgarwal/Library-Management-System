from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required
from datetime import datetime, timedelta
from sqlalchemy import or_

app = Flask(__name__)
app.config['SECRET_KEY'] = 'library_management_system'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)

# Database models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    issued_books = db.Column(db.Integer, default=0)

class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(50), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

class IssuedBooks(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    issued_date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    return_date = db.Column(db.Date, nullable=False)

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, nullable=False)
    BookName = db.Column(db.String(200), nullable=False)
    Author = db.Column(db.String(200), nullable=False)
    orderDate = db.Column(db.Date, default=datetime.utcnow, nullable=False)
 
# Configure your user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('loginType')

        if login_type == 'admin':
            return redirect(url_for('admin_login'))
        elif login_type == 'user':
            return redirect(url_for('user_login'))

    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    invalid_credentials = False
    if request.method == 'POST':
        admin_username = request.form.get('adminUsername')
        admin_password = request.form.get('adminPassword')

        admin = Admin.query.filter_by(username=admin_username, password=admin_password).first()

        if admin:
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        else:
            invalid_credentials = True

    return render_template('admin_login.html', invalid_credentials=invalid_credentials)

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    invalid_credentials = False

    if request.method == 'POST':
        user_username = request.form.get('userUsername')
        user_password = request.form.get('userPassword')

        user = User.query.filter_by(username=user_username, password=user_password).first()

        if user:
            login_user(user)
            return redirect(url_for('user_dashboard'))
        else:
            invalid_credentials = True

    return render_template('user_login.html', invalid_credentials=invalid_credentials)

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/user_dashboard')
def user_dashboard():
    return render_template('user_dashboard.html', user_name=current_user.name if current_user.is_authenticated else "")


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    success_message = None

    if request.method == 'POST':
        # Get user details from the form
        user_id = request.form.get('newUserId')
        name = request.form.get('newUserName')
        username = request.form.get('newUserUsername')
        password = request.form.get('newUserPassword')

        # Create a new user object and add it to the database
        new_user = User(id=user_id, name=name, username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        success_message = 'User added successfully!'

    return render_template('add_user.html', success_message=success_message)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    success_message = None

    if request.method == 'POST':
        # Get book details from the form
        isbn = request.form.get('bookISBN')
        title = request.form.get('bookTitle')
        author = request.form.get('bookAuthor')
        genre = request.form.get('bookGenre')
        quantity = request.form.get('bookQuantity')

        # Check if ISBN is unique before adding the book
        if Book.query.filter_by(isbn=isbn).first() is not None:
            success_message = 'Book with the provided ISBN already exists. Please use a unique ISBN.'
        else:
            # Create a new book object and add it to the database
            new_book = Book(isbn=isbn, title=title, author=author, genre=genre, quantity=quantity)
            db.session.add(new_book)
            db.session.commit()
            success_message = 'Book added successfully!'

    return render_template('add_book.html', success_message=success_message)

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    books = Book.query.all()
    return render_template('search.html',books = books)

@app.route('/issue_book/<isbn>', methods=['POST'])
@login_required
def issue_book(isbn):

    book = Book.query.filter_by(isbn=isbn).first()

    # Check if the user has already issued a copy of the same book
    existing_issue = IssuedBooks.query.filter_by(user_id=current_user.id, isbn=isbn).first()

    # Check if the user has already issued the maximum allowed books (6)
    if current_user.issued_books >= 6:
        return jsonify({'success': False, 'message': 'You have reached the maximum limit of issued books (6).'})

    # Check if the book is available and the user has not already issued a copy of it
    if book and (book.quantity > 0) and not existing_issue:
        # Calculate return date as 7 days from the issued date
        issued_date = datetime.utcnow()
        return_date = issued_date + timedelta(days=7)

        # Update the IssuedBooks table
        issued_book = IssuedBooks(
            isbn=book.isbn,
            title=book.title,
            user_id=current_user.id,
            issued_date=issued_date,
            return_date=return_date
        )
        db.session.add(issued_book)

        # Update the User table's issued_books field
        current_user.issued_books += 1

        # Decrement the book quantity and save to the database
        book.quantity -= 1

        # Commit all changes to the database
        db.session.commit()

        return jsonify({'success': True, 'message': 'Book issued successfully!'})
    elif existing_issue:
        return jsonify({'success': False, 'message': 'You have already issued a copy of this book.'})
    else:
        return jsonify({'success': False, 'message': 'Failed to issue the book. Insufficient quantity.'})

@app.route('/issued_books')
def issued_books():
    issued_books = IssuedBooks.query.all()
    return render_template('issued_books.html', issued_books = issued_books)

@app.route('/return_book')
@login_required
def return_book():
    # Get the books issued by the current user
    issued_books = IssuedBooks.query.filter_by(user_id=current_user.id).all()

    return render_template('return_book.html', issued_books=issued_books)

@app.route('/return_book/<isbn>', methods=['POST'])
@login_required
def handle_return_book(isbn):
    book = Book.query.filter_by(isbn=isbn).first()

    # Check if the book is issued to the current user and not returned yet
    issued_book = IssuedBooks.query.filter_by(user_id=current_user.id, isbn=isbn).first()

    if book and issued_book:
        db.session.delete(issued_book)

        # Update the User table's issued_books field
        current_user.issued_books -= 1

        # Increment the book quantity and save to the database
        book.quantity += 1

        # Commit all changes to the database
        db.session.commit()

        return jsonify({'success': True, 'message': 'Book returned successfully!'})
    else:
        return jsonify({'success': False, 'message': 'Failed to return the book. Book not found or already returned.'})


@app.route('/view_all_books')
def view_all_books():
    books = Book.query.all()
    return render_template('view_all_books.html', books=books)

@app.route('/place_order', methods=['GET', 'POST'])
def place_order():
    if request.method == 'POST':
        author_name = request.form.get('authorName')
        book_title = request.form.get('bookTitle')

        # Check if the user has already placed a similar order
        existing_order = Orders.query.filter_by(userId=current_user.id, Author=author_name, BookName=book_title).first()

        if existing_order:
            error_message = 'You have already placed an order for this book and author.'
            return render_template('place_order.html', message=error_message)

        # If no similar order found, proceed with placing the order
        new_order = Orders(userId=current_user.id, Author=author_name, BookName=book_title)
        db.session.add(new_order)
        db.session.commit()

        success_message = 'Order placed successfully!'
        return render_template('place_order.html', message=success_message)

    return render_template('place_order.html')

@app.route('/view_orders')
def view_orders():
    # Fetch all orders from the database
    orders = Orders.query.all()
    return render_template('view_orders.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True)
