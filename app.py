from flask import Flask, render_template, request, redirect
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from flask.ext.mongoengine.wtf import model_form
from wtforms import PasswordField
import datetime
from datetime import *
from flask_mail import Mail, Message
import requests.packages.urllib3


app = Flask(__name__)
app.config.update(dict(

	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_TLS=False,
	MAIL_USE_SSL= True,
	MAIL_USERNAME = 'email',
	MAIL_PASSWORD = 'password'

	))

mailer = Mail(app)

now = datetime.now()


login_manager = LoginManager()
login_manager.init_app(app)

app.config["DEBUG"] = True
app.config['MONGODB_SETTINGS'] = {'db' : 'events'}
app.config['SECRET_KEY'] = 'ajosjdfajjjj3453453oj!!!oij'
app.config['WTF_CSRF_ENABLED'] = True

db = MongoEngine(app)

class newUser(db.Document):

	Email = db.StringField(required=True, unique=True)
	Password = db.StringField(required=True)
	State = db.StringField(required=False)
	Username = db.StringField(required=False)

	def is_authenticated(self):
		
		users = newUser.objects(Email=self.Email, Password=self.Password, State=self.State, Username=self.Username)
		return len(users) != 0

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.Email



@login_manager.user_loader
def load_user(Email):
	
	users = newUser.objects(Email=Email)

	if len(users) != 0:
		return users[0]

	else:
		return None

UserForm = model_form(newUser)
UserForm.Password = PasswordField('Password')

class FavoriteEvent(db.Document):
	title = db.StringField(required=True)
	date_time = db.StringField(required=True)
	location = db.StringField(required=True)
	event_id = db.IntField(required=True)
	link = db.StringField(required=True)
	avg_px = db.IntField(required=False)
	min_px = db.IntField(required=False)
	max_px = db.IntField(required=False)
	num_tix = db.IntField(required=False)
	picture = db.StringField(required=False)
	poster = db.ReferenceField(newUser)




@app.route("/")
def hello():

	month_dict = {1: "January", 2: "February", 3: "March", 4: "April", 5:"May", 6:"June", 7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"September"}
	start_date = datetime.today().strftime('%Y-%m-%d')
	date_1 = datetime.strptime(start_date, "%Y-%m-%d")
	end_date = date_1 + (timedelta(days=60))
	date_1 = date_1.strftime('%Y-%m-%d')
	end_date = end_date.strftime('%Y-%m-%d')

	if current_user.is_authenticated:
		
		url ="https://api.seatgeek.com/2/events?datetime_utc.gte=" + date_1 +"&datetime_utc.lte="+ end_date + "&venue.state=" +current_user.State + "&sort=score.desc" + "&client_id=NDM5NTU0NHwxNDU4NzUzODgz"
	else:
		
		url ="https://api.seatgeek.com/2/events?datetime_utc.gte=" + date_1 +"&datetime_utc.lte="+ end_date + "&sort=score.desc" + "&client_id=NDM5NTU0NHwxNDU4NzUzODgz"

	response_dict = requests.get(url).json()
	total = response_dict["meta"]["total"]

	if total > 200:
		url = url + "&per_page=200"
	else:
		url = url + "&per_page=" + str(total)
	
	response_dict= requests.get(url).json()
	count = min(total, 10)
	image_list = []
	title_list = []
	date_list= []
	time_list= []
	id_list = []
	
	location_list = []
	venue_list= []
	event_count = 0
	i = 0
	
	while event_count < count:

		if response_dict["events"][i]["performers"][0]["image"] and not (response_dict["events"][i]["title"] in title_list):
			image_list.append(response_dict["events"][i]["performers"][0]["image"])
			title_list.append(response_dict["events"][i]["title"])
			id_list.append(response_dict["events"][i]["id"])
			venue_list.append(response_dict["events"][i]["venue"]["name"])
			location_list.append(response_dict["events"][i]["venue"]["display_location"])
			
			date_str = ""
			time_str = ""
			mystr = ""
			temp_list=[]
			mystr = response_dict["events"][i]["datetime_local"]
			mystr = mystr.replace('-', ' ')
			mystr = mystr.replace('T', ' ')
			temp_list = (mystr.split(' '))
			date_str= temp_list[1] + "/" + temp_list[2] + "/" + temp_list[0] + " "

			if int(temp_list[3][:2]) > 12:

				time_str =  str(int(temp_list[3][:2])-12) + temp_list[3][2:5] + " PM"

			else:

				time_str = temp_list[3][:5] + " AM"
       
			date_list.append(date_str)
			time_list.append(time_str)
			event_count= event_count+1
			i = i +1

		else:
			i = i + 1


	return render_template("hello.html",  current_user=current_user, total=count, venue_list= venue_list, location_list=location_list, date_list=date_list, time_list=time_list, image_list=image_list, title_list=title_list, id_list=id_list)
	



@app.route("/search", methods=["POST", "GET"])
@login_required
def search():
	if request.method == "POST":
		total = 0
		date_list= []
		time_list = []
		price_list = []

		if request.form["other_search"]:
			url = "https://api.seatgeek.com/2/events?venue.state=" + request.form["other_search"] + "&q=" + request.form["user_search"] + "&client_id=NDM5NTU0NHwxNDU4NzUzODgz"
        
		else:
			url = "https://api.seatgeek.com/2/events?" + "q=" + request.form["user_search"] + "&client_id=NDM5NTU0NHwxNDU4NzUzODgz"
		
		response_dict = requests.get(url).json()
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

				time_str =  str(int(temp_list[3][:2])-12) + temp_list[3][2:5] + " PM"

			else:

				time_str = temp_list[3][:5] + " AM"
       
			date_list.append(date_str)
			time_list.append(time_str)

			price_list.append((str(event["stats"]["average_price"])+'0', str(event["stats"]["lowest_price"])+'0', str(event["stats"]["highest_price"])+'0'))

        	
		num_events= len(date_list)
		
		return render_template("results.html", price_list=price_list, api_data=response_dict, time_list=time_list, date_list=date_list, num_events=num_events)
	else: 
		return render_template("search.html")



@app.route("/browse/sports", methods=["POST", "GET"])
@login_required
def sports_browse():
	if request.method == "POST":
		
		total = 0
		date_list= []
		time_list = []
		price_list = []


		month_dict = {1: "January", 2: "February", 3: "March", 4: "April", 5:"May", 6:"June", 7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"September"}
		start_date = datetime.today().strftime('%Y-%m-%d')
		date_1 = datetime.strptime(start_date, "%Y-%m-%d")
		end_date = date_1 + (timedelta(days=120))
		date_1 = date_1.strftime('%Y-%m-%d')
		end_date = end_date.strftime('%Y-%m-%d')
		
		url ="https://api.seatgeek.com/2/events?datetime_utc.gte=" + date_1 +"&datetime_utc.lte="+ end_date + "&venue.state=" + request.form["user_search"] + "&taxonomies.name=sports&client_id=NDM5NTU0NHwxNDU4NzUzODgz"
        
		
		
		response_dict = requests.get(url).json()
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

				time_str =  str(int(temp_list[3][:2])-12) + temp_list[3][2:5] + " PM"

			else:

				time_str = temp_list[3][:5] + " AM"
       
			date_list.append(date_str)
			time_list.append(time_str)

			price_list.append((str(event["stats"]["average_price"])+'0', str(event["stats"]["lowest_price"])+'0', str(event["stats"]["highest_price"])+'0'))

        	
		num_events= len(date_list)
		

		return render_template("browse_results.html", category="Sports", price_list=price_list, api_data=response_dict, time_list=time_list, date_list=date_list, num_events=num_events)
	else: 

		return render_template("browse.html", category="Sports")




@app.route("/events/<id>")
def event(id):
	event_url = "https://api.seatgeek.com/2/events/" + id
	event_dict = requests.get(event_url).json()

	date_list= []
	time_list = []
	price_list = []

	date_str = ""
	time_str = ""
	mystr = ""
	temp_list=[]
	mystr = event_dict["datetime_local"]
	mystr = mystr.replace('-', ' ')
	mystr = mystr.replace('T', ' ')
	temp_list = (mystr.split(' '))
	date_str= temp_list[1] + "/" + temp_list[2] + "/" + temp_list[0] + " "

	if int(temp_list[3][:2]) > 12:

		time_str =  str(int(temp_list[3][:2])-12) + temp_list[3][2:5] + " PM"

	else:

		time_str = temp_list[3][:5] + " AM"
       
	date_list.append(date_str)
	time_list.append(time_str)

	price_list.append((str(event_dict["stats"]["average_price"])+'0', str(event_dict["stats"]["lowest_price"])+'0', str(event_dict["stats"]["highest_price"])+'0'))

	
	
	return render_template("event.html", price_list=price_list, api_data=event_dict, time_list=time_list, date_list=date_list)


@app.route("/favorite/<id>")
@login_required

def favorite(id):
	event_url = "https://api.seatgeek.com/2/events/" + id
	event_dict = requests.get(event_url).json()
	poster = newUser.objects(Email=current_user.Email).first()
	if FavoriteEvent.objects(poster=poster, event_id=id).count() == 0:
		new_fav = FavoriteEvent(avg_px = event_dict["stats"]["average_price"], min_px= event_dict["stats"]["lowest_price"], max_px=event_dict["stats"]["highest_price"], num_tix= event_dict["stats"]["highest_price"], picture= event_dict["performers"][0]["image"], title=event_dict["title"], date_time=event_dict["datetime_local"], location=event_dict["venue"]["name"], event_id=event_dict["id"], link=event_dict["url"], poster=poster)
		new_fav.save()
		return render_template("confirm.html", api_data=event_dict, err=False)
	return render_template("confirm.html", api_data=event_dict, err=True)

@app.route("/favorites/delete/<id>")
@login_required
def delete_favorite(id):
	
	current_poster = newUser.objects(Email=current_user.Email).first()
	FavoriteEvent.objects(poster=current_poster, event_id=id).delete()

	return redirect("/favorites")

@app.route("/favorites")
@login_required
def favorites():


	current_poster = newUser.objects(Email=current_user.Email).first()
	favorites = FavoriteEvent.objects(poster=current_poster)
	return render_template("favorites.html", current_user = current_user, favorites=favorites)


@app.route("/register", methods=["POST", "GET"])
def register():

	form = UserForm(request.form)

	if request.method == 'POST' and form.validate():

		form.save()

		msg = Message("Thanks for registering, " + form.Username.data, sender="davepiccolella@gmail.com", recipients=[form.Email.data])
		msg.html= render_template("email.html")
		mailer.send(msg)



		return render_template("register_confirm.html", form=form)

	return render_template("register.html", form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():

	form = UserForm(request.form)

	if request.method == 'POST' and form.validate():
		

		users = newUser.objects(Email=form.Email.data, Password=form.Password.data)
		
		if len(users) != 0:

			user = newUser(Email=form.Email.data, Password=form.Password.data)
			login_user(user)
			return redirect('/')

		else:
			return render_template('login.html', form=form, failed=True)
	else:

		return render_template('login.html', form=form)


@app.route("/logout")
def logout():

	logout_user()
	return render_template('logout.html')




if __name__ == "__main__":

	app.run(host="0.0.0.0")

