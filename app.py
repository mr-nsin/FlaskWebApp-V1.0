from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import add_single_article, get_all_articles, get_article, update_article, delete_article_id
from users import add_user, get_user_password
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from request import REQUEST
from functools import wraps

app = Flask(__name__)


#Index Page
@app.route('/')
def index():
	return render_template('index.html')

#About Page
@app.route('/about')
def about():
	return render_template('about.html')

#Articles Page to get all articles from navigation bar
@app.route('/articles')
def articles():
	#Get Articles
	articles = get_all_articles()
	if len(articles) > 0:
		return render_template('articles.html', articles = articles)
	else:
		msg = 'No Article Found'
		return render_template('articles.html', msg = msg)

	return render_template('dashboard.html')

#Get specific article information when clicked
@app.route('/article/<int:id>/')
def article(id):
	#Get Article with id
	article = get_article(id = id)
	return render_template('article.html', article = article)

#Registration Form  class to validate the all fields
class RegisterForm(Form):
	name = StringField('Name', [validators.length(min=1, max=50)])
	username = StringField('Username', [validators.length(min=4, max=25)])
	email = StringField('Email', [validators.length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message='Passwords do not match')
	])
	confirm = PasswordField('Confirm Password')

#Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
	#Get Registration Form
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
			#Get Register form fields
			name = form.name.data
			email = form.email.data
			username = form.username.data
			password = sha256_crypt.encrypt(str(form.password.data))

			add_user(name = name, email = email, username = username, password = password)

			flash('You are now registered, can log in', 'success')

			return redirect(url_for('index'))

	return render_template('register.html', form = form)

#Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		#Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']

		#Get user by Username
		result = get_user_password(username = username)

		if result['found'] == True:
			password = result['password']

			#Compare passwords
			if sha256_crypt.verify(password_candidate, password):
				#Passed
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')

				return redirect(url_for('dashboard'))
			else:
				error = 'Invald Login'
				return render_template('login.html', error = error)
		else:
			error = 'Username Not Found'
			return render_template('login.html', error = error)
	return render_template('login.html')

#Python Decorators
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap

#Logout Route
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are successfully logged out', 'success')
	return redirect(url_for('login'))

#Dashboard Route
@app.route('/dashboard')
@is_logged_in
def dashboard():
	#Get Articles
	articles = get_all_articles()
	if len(articles) > 0:
		return render_template('dashboard.html', articles = articles)
	else:
		msg = 'No Article Found'
		return render_template('dashboard.html', msg = msg)

	return render_template('dashboard.html')

#Article Form class to validate all the fields of add article
class ArticleForm(Form):
	title = StringField('Title', [validators.length(min = 1, max = 200)])
	body = TextAreaField('Body', [validators.length(min = 30)])

#Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		add_single_article(title = title, body = body, author = session['username'])

		flash('Article Created', 'success')

		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form = form)

#Edit Article
@app.route('/edit_article/<int:id>', methods=['GET', 'POST'])
#Here get method is used to fetch the page from the server and when submit button is clicked post request is send to submit the details.
@is_logged_in
def edit_article(id):
	#Get Form
	form = ArticleForm(request.form)

	#Get artic le with specific id
	article = get_article(id)

	#Populate article form fields for article got from stored articles
	form.title.data = article['title']
	form.body.data = article['body']

	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		#Update article in data.py
		update_article(id = id, title = title, body = body)

		flash('Article Updated', 'success')

		return redirect(url_for('dashboard'))

	return render_template('edit_article.html', form = form)

#Delete Article
@app.route('/delete_article/<int:id>', methods=['POST'])
@is_logged_in
#Delete Article
def delete_article(id):
	#Delete the article with id
	delete_article_id(id = id)

	flash('Article Deleted', 'success')

	return redirect(url_for('dashboard'))

if __name__ == '__main__':
	app.secret_key = 'secret123'
	app.run(debug=True)
