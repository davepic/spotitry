from flask import Flask, render_template, request, redirect
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from flask.ext.mongoengine.wtf import model_form
from wtforms import PasswordField


import requests.packages.urllib3
#requests.packages.urllib3.disable_warnings()

app = Flask(__name__)


login_manager = LoginManager()
login_manager.init_app(app)

app.config["DEBUG"] = True
app.config['MONGODB_SETTINGS'] = {'db' : 'events'}
app.config['SECRET_KEY'] = 'ajosjdfajjjj3453453oj!!!oij'
app.config['WTF_CSRF_ENABLED'] = True

db = MongoEngine(app)

class newUser(db.Document):

	name = db.StringField(required=True, unique=True)
	password = db.StringField(required=True)

	def is_authenticated(self):
		
		users = newUser.objects(name=self.name, password=self.password)
		return len(users) != 0

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.name



@login_manager.user_loader
def load_user(name):
	
	users = newUser.objects(name=name)

	if len(users) != 0:
		return users[0]

	else:
		return None

UserForm = model_form(newUser)
UserForm.password = PasswordField('password')

class FavoriteEvent(db.Document):
	title = db.StringField(required=True)
	date_time = db.StringField(required=True)
	location = db.StringField(required=True)
	event_id = db.StringField(required=True)
	link = db.StringField(required=True)
	poster = db.ReferenceField(newUser)



@app.route("/")
def hello():

	return render_template("hello.html", current_user=current_user)



@app.route("/search", methods=["POST", "GET"])

@login_required
def search():
	if request.method == "POST":
		total = 0
		date_list= []
		time_list = []

		if request.form["other_search"]:
			url = "https://api.seatgeek.com/2/events?venue.state=" + request.form["other_search"] + "&q=" + request.form["user_search"] + "&client_id=NDM5NTU0NHwxNDU4NzUzODgz"
        
		else:
			url = "https://api.seatgeek.com/2/events?" + "q=" + request.form["user_search"] + "&client_id=NDM5NTU0NHwxNDU4NzUzODgz"
		
		response_dict = requests.get(url).json()
		print response_dict
		total = response_dict["meta"]["total"]
		url = url + "&per_page=" + str(total)
		response_dict = requests.get(url).json()

		for event in response_dict["events"]:
			date_str = ""
			time_str = ""
			mystr = ""
			temp_list=[]
			mystr = event["datetime_local"]
			mystr = mystr.replace('-', ' ')
			mystr = mystr.replace('T', ' ')
			temp_list = (mystr.split(' '))
			date_str= temp_list[1] + "/" + temp_list[2] + "/" + temp_list[0] + " "

			if int(temp_list[3][:2]) > 12:

				time_str =  str(int(temp_list[3][:2])-12) + temp_list[3][2:] + " PM"

			else:

				time_str = temp_list[3] + " AM"
       
			date_list.append(date_str)
			time_list.append(time_str)

        	
		num_events= len(date_list)
		print url
		return render_template("results.html", api_data=response_dict, time_list=time_list, date_list=date_list, num_events=num_events)
	else: 
		return render_template("search.html")


@app.route("/favorite/<id>")
@login_required

def favorite(id):
	book_url = "https://www.googleapis.com/books/v1/volumes/" + id
	book_dict = requests.get(book_url).json()
	poster = newUser.objects(name=current_user.name).first()
	new_fav = FavoriteBook(author=book_dict["volumeInfo"]["authors"][0], title=book_dict["volumeInfo"]["title"], link=book_url, poster=poster)
	new_fav.save()
	return render_template("confirm.html", api_data=book_dict)


@app.route("/favorites/delete/<id>")
@login_required
def delete_favorite(id):
	
	current_poster = newUser.objects(name=current_user.name).first()
	FavoriteBook.objects(poster=current_poster, title=id).delete()

	return redirect("/favorites")

@app.route("/favorites")
@login_required
def favorites():


	current_poster = newUser.objects(name=current_user.name).first()
	favorites = FavoriteBook.objects(poster=current_poster)
	return render_template("favorites.html", current_user = current_user, favorites=favorites)


@app.route("/register", methods=["POST", "GET"])
def register():

	form = UserForm(request.form)

	if request.method == 'POST' and form.validate():

		form.save()

		return redirect("/login")

	return render_template("register.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():

	form = UserForm(request.form)

	if request.method == 'POST' and form.validate():

		users = newUser.objects(name=form.name.data, password=form.password.data)
		
		if len(users) != 0:

			user = newUser(name=form.name.data, password=form.password.data)
			login_user(user)
			return redirect('/')

		else:
			return render_template('login.html', form=form, failed=True)
	else:

		return render_template('login.html', form=form)

@app.route("/logout")
def logout():

	logout_user()
	return redirect("/logout_confirm")

@app.route("/logout_confirm")
def logout_confirm():

	return render_template('logout.html')


if __name__ == "__main__":

	app.run(host="0.0.0.0")

