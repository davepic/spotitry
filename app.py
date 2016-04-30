from flask import Flask, render_template, request, redirect, session
from flask.ext.mongoengine import MongoEngine
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user
from flask.ext.mongoengine.wtf import model_form
from wtforms import PasswordField
import datetime
import urllib
import base64
import json
from datetime import *
from flask_mail import Mail, Message
import requests.packages.urllib3
from flask.ext.paginate import Pagination


#WORKS TO PREVENT DUPS BUT MESSES UP CONNECTION
#from signal import signal, SIGPIPE, SIG_DFL
#signal(SIGPIPE,SIG_DFL)

requests.packages.urllib3.disable_warnings()



app = Flask(__name__)
app.config.update(dict(

	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_TLS=False,
	MAIL_USE_SSL= True,
	MAIL_USERNAME = 'email',
	MAIL_PASSWORD = 'password'

	))

CLIENT_ID = "68eb0b1766a64f8294da279e662232c0"
CLIENT_SECRET = "8a2d182155d64971846f16faae25f1e4"

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)


# Server-side Parameters
CLIENT_SIDE_URL = "http://0.0.0.0"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()


auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}



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
	location_name = db.StringField(required=False)
	poster = db.ReferenceField(newUser)


class SearchData(db.Document):
	user_search = db.StringField(required=False)
	category = db.StringField(required=True)
	state = db.StringField(required=True)
	num_days = db.StringField(required=True)
	sort_by = db.StringField(required=True)
	total = db.IntField(required=True)
	poster = db.StringField(required=True)
	per_page = db.StringField(required=True)
	max_price = db.StringField(required=False)


@app.route("/spotify")
def spotify():
	url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.iteritems()])
	auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
	return redirect(auth_url)

@app.route("/callback/q", methods=["POST", "GET"])
def callback():

	setlist_ids = {}


	auth_token = request.args['code']
	code_payload = {
    	"grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
	base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET))
	headers = {"Authorization": "Basic " + base64encoded}
	post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

	# Auth Step 5: Tokens are Returned to Application
	response_data = json.loads(post_request.text)
	access_token = response_data["access_token"]
	refresh_token = response_data["refresh_token"]
	token_type = response_data["token_type"]
	expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
	authorization_header = {"Authorization":"Bearer " + access_token, "Content-Type": "application/json"}

    # Get profile data
	user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
	profile_data = requests.get(user_profile_api_endpoint, headers=authorization_header).json()
	


    # Get user playlist data
	playlist_api_endpoint = "{}/playlists".format(profile_data["href"])

	request_data = {"name": "Setlist Playlist"}

	

	try:

		response = requests.post(playlist_api_endpoint, data="{\"name\":\"Setlist Playlist\"}", headers=authorization_header).json()
		song_url = response["tracks"]["href"]
		song_response = requests.post(song_url + "?uris=spotify:track:2dcoDVcOc9hGPbtZFtpcw3", headers=authorization_header).json()

		# Get profile data
		user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
		profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header).json()
    	

    	# Get user playlist data
		playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
		playlists_data = requests.get(playlist_api_endpoint, headers=authorization_header).json()
    	
		for playlist in playlists_data["items"]:
			if setlist_ids.get(playlist["name"]) == None:
				setlist_ids[playlist["name"]] = True
			else:
				playlist_url = playlist["href"] + "/followers"
				playlist_response = requests.delete(playlist_url, headers=authorization_header)

		


	except IOError:
		pass



	return render_template("spotify.html")


@app.route("/playlist")

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
		for data in SearchData.objects(poster=current_user.Email):
			data.delete()

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

			if response_dict["events"][i]["time_tbd"]:

				time_str = "Time TBA"
       
			date_list.append(date_str)
			time_list.append(time_str)
			event_count= event_count+1
			i = i +1

		else:
			i = i + 1


	return render_template("hello.html",  current_user=current_user, total=count, venue_list= venue_list, location_list=location_list, date_list=date_list, time_list=time_list, image_list=image_list, title_list=title_list, id_list=id_list)
	


@app.route("/search", methods=["POST", "GET"])
def search():

	if current_user.is_authenticated:

		if request.method == "POST":

			if SearchData.objects(poster=current_user.Email):

				for data in SearchData.objects(poster=current_user.Email):
					data.delete()

			total = 0
			date_list= []
			time_list = []
			price_list = []
			link_list = []
			song_list = []
			setlist = []
			name_list = []

			month_dict = {1: "January", 2: "February", 3: "March", 4: "April", 5:"May", 6:"June", 7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"September"}
			start_date = datetime.today().strftime('%Y-%m-%d')
			date_1 = datetime.strptime(start_date, "%Y-%m-%d")

			url = "https://api.seatgeek.com/2/events?venue.state=" + request.form["state_search"]+ "&client_id=NDM5NTU0NHwxNDU4NzUzODgz"

			if request.form["num_days"] != "":
				end_date = date_1 + (timedelta(days=int(request.form["num_days"])))
				date_1 = date_1.strftime('%Y-%m-%d')
				end_date = end_date.strftime('%Y-%m-%d')
				url = url + "&datetime_utc.gte=" + date_1 +"&datetime_utc.lte=" + end_date

			if request.form["sort_by"] != "":
				url = url + "&sort=" + request.form["sort_by"]

			if request.form["category_search"] != "":
				url = url + "&taxonomies.name=" + request.form["category_search"]

			if request.form["per_page"] != "":
				url = url + "&per_page=" + request.form["per_page"]

			if request.form["max_price"] != "":
				url = url + "&lowest_price.lte=" + request.form["max_price"]


			try:
				page = int(request.args.get('page', 1))
			except ValueError:
				page = 1

			if request.form["user_search"]:
				url = url + "&q=" + request.form["user_search"]
			else:
				url = url + "&listing_count.gt=0"

			url = url + "&page="+str(page)



			
			response_dict = requests.get(url).json()

			total = response_dict["meta"]["total"]

			if request.form["user_search"]:
				if request.form["max_price"]:
					new_search = SearchData(max_price= request.form["max_price"], per_page= request.form["per_page"], poster= current_user.Email, total = total, num_days= (request.form["num_days"]), user_search=request.form["user_search"], category=request.form["category_search"], state= request.form["state_search"], sort_by=request.form["sort_by"])
				else:
					new_search = SearchData(per_page= request.form["per_page"], poster= current_user.Email, total = total, num_days= (request.form["num_days"]), user_search=request.form["user_search"], category=request.form["category_search"], state= request.form["state_search"], sort_by=request.form["sort_by"])
			else:
				
				if request.form["max_price"]:
					new_search = SearchData(max_price= request.form["max_price"], per_page= request.form["per_page"], poster= current_user.Email, total = total, num_days= (request.form["num_days"]), category=request.form["category_search"], state= request.form["state_search"], sort_by=request.form["sort_by"])
				else:
					new_search = SearchData(per_page= request.form["per_page"], poster= current_user.Email, total = total, num_days= (request.form["num_days"]), category=request.form["category_search"], state= request.form["state_search"], sort_by=request.form["sort_by"])
			new_search.save()

			

			if total>0:

				response_dict = requests.get(url).json()
				 

				if request.form["per_page"] == "":
   
					pagination = Pagination(page=page, total = total, search=search, per_page=10, show_single_page=True, record_name="events", css_framework='foundation', found =total)
				else:
					pagination = Pagination(page=page, total = total, search=search, per_page=int(request.form["per_page"]), show_single_page=True, record_name="events", css_framework='foundation', found=total)


				for event in response_dict["events"]:

					i = 0
					index = 0

					temp_song_list = []
					temp_setlist = []

					artist_url = "https://api.seatgeek.com/2/performers/" + str(event["performers"][0]["id"])

					setlist_url = "http://api.setlist.fm/rest/0.1/search/setlists.json?artistName="+ event["performers"][0]["name"]

					song_url = "http://developer.echonest.com/api/v4/song/search?api_key=WAIWXTP9XKUFFH8GO&format=json&artist_id=seatgeek:artist:" + str(event["performers"][0]["id"])+ "&sort=song_hotttnesss-desc&results=100"
					


					artist_dict = requests.get(artist_url).json()
					song_dict = requests.get(song_url).json()




					if request.form["category_search"] == "concert":

						try:
							setlist_dict = requests.get(setlist_url).json()

							while setlist_dict["setlists"]["setlist"][index]["sets"] == "" and index<int(setlist_dict["setlists"]["@total"]):
								index=index+1

							
							if setlist_dict["setlists"]["setlist"][index]["sets"] != "":

								name_list.append(event["performers"][0]["name"])

								num_sets = len(setlist_dict["setlists"]["setlist"][index]["sets"]["set"])
						
								

								
							else:
								name_list.append("")
						
						except ValueError:
							name_list.append("")
						

						if song_dict["response"]["status"]["message"] == "Success":
							for j in range(len(song_dict["response"]["songs"])-1):
								if min(len(song_dict["response"]["songs"][j]["title"]), len(song_dict["response"]["songs"][j+1]["title"])) > 3:
									if song_dict["response"]["songs"][j]["title"][:4] != song_dict["response"]["songs"][j+1]["title"][:4]:
										temp_song_list.append(song_dict["response"]["songs"][j]["title"])
								else:
									if song_dict["response"]["songs"][j]["title"] != song_dict["response"]["songs"][j+1]["title"]:
										temp_song_list.append(song_dict["response"]["songs"][j]["title"]) 
						

						if artist_dict.get("links"):
							link_list.append(artist_dict["links"][0]["url"])
						else:
							link_list.append("nothing")
						

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
					song_list.append(temp_song_list)
					setlist.append(temp_setlist)
        	
				num_events= len(date_list)

				
				
				return render_template("results.html", name_list = name_list, song_list = song_list, link_list = link_list, max_price = request.form["max_price"], events=response_dict["events"], user_search= request.form["user_search"], category= request.form["category_search"], state = request.form["state_search"], num_days= request.form["num_days"], sort=request.form["sort_by"], per_page= request.form["per_page"], price_list=price_list, api_data=response_dict, time_list=time_list, date_list=date_list, num_events=num_events, pagination = pagination)
				
			else:
				return render_template("search.html", failed=True)

		elif request.args.get('page') or SearchData.objects.first(): 

			total = 0
			date_list= []
			time_list = []
			price_list = []
			link_list = []
			song_list = []
			name_list = []


			month_dict = {1: "January", 2: "February", 3: "March", 4: "April", 5:"May", 6:"June", 7:"July", 8:"August", 9:"September", 10:"October", 11:"November", 12:"September"}
			start_date = datetime.today().strftime('%Y-%m-%d')
			date_1 = datetime.strptime(start_date, "%Y-%m-%d")

			url = "https://api.seatgeek.com/2/events?" + "venue.state=" + SearchData.objects.first().state

			if SearchData.objects.first().user_search:
				url = url + "&q=" + SearchData.objects.first().user_search
			else:
				url = url + "&listing_count.gt=0"

			if SearchData.objects.first().num_days != "":
				end_date = date_1 + (timedelta(days=int(SearchData.objects.first().num_days)))
				date_1 = date_1.strftime('%Y-%m-%d')
				end_date = end_date.strftime('%Y-%m-%d')
				url = url + "&datetime_utc.gte=" + date_1 +"&datetime_utc.lte="+ end_date
			

			try:
				page = int(request.args.get('page', 1))
			except ValueError:
				page = 1

			total = SearchData.objects.first().total

			if SearchData.objects.first().sort_by != "":
				url = url + "&sort=" + SearchData.objects.first().sort_by

			if SearchData.objects.first().category != "":
				url = url + "&taxonomies.name=" + SearchData.objects.first().category

			

			if SearchData.objects.first().max_price:
				url = url + "&lowest_price.lte=" + SearchData.objects.first().max_price

			url = url + "&page="+str(page)



			if SearchData.objects.first().per_page != "":

				url = url + "&per_page=" + SearchData.objects.first().per_page

			url = url +  "&client_id=NDM5NTU0NHwxNDU4NzUzODgz"

			if total>0:

				

				response_dict = requests.get(url).json()


				if SearchData.objects.first().per_page == "":

					pagination = Pagination(page=page, total = total, search=search, per_page=10, show_single_page=True, record_name="events", css_framework='foundation', found =total)
				
				else:

					pagination = Pagination(page=page, total = total, search=search, per_page=int(SearchData.objects.first().per_page), show_single_page=True, record_name="events", css_framework='foundation', found =total)

				for event in response_dict["events"]:

					temp_song_list = []
					index = 0

					artist_url = "https://api.seatgeek.com/2/performers/" + str(event["performers"][0]["id"])
					song_url = "http://developer.echonest.com/api/v4/song/search?api_key=WAIWXTP9XKUFFH8GO&format=json&artist_id=seatgeek:artist:" + str(event["performers"][0]["id"])+ "&sort=song_hotttnesss-desc&results=100"
					setlist_url = "http://api.setlist.fm/rest/0.1/search/setlists.json?artistName="+ event["performers"][0]["name"]


					artist_dict = requests.get(artist_url).json()
					song_dict = requests.get(song_url).json()

					if SearchData.objects.first().category == "concert":

						try:
							setlist_dict = requests.get(setlist_url).json()

							while setlist_dict["setlists"]["setlist"][index]["sets"] == "" and index<int(setlist_dict["setlists"]["@total"]):
								index=index+1

							
							if setlist_dict["setlists"]["setlist"][index]["sets"] != "":

								name_list.append(event["performers"][0]["name"])

							
							else:
								name_list.append("")
						
						except ValueError:
							name_list.append("")



						if artist_dict.get("links"):
							link_list.append(artist_dict["links"][0]["url"])
						else:
							link_list.append("nothing")


						if song_dict["response"]["status"]["message"] == "Success":
							for j in range(len(song_dict["response"]["songs"])-1):
								if min(len(song_dict["response"]["songs"][j]["title"]), len(song_dict["response"]["songs"][j+1]["title"])) > 3:
									if song_dict["response"]["songs"][j]["title"][:4] != song_dict["response"]["songs"][j+1]["title"][:4]:
										temp_song_list.append(song_dict["response"]["songs"][j]["title"])
								else:
									if song_dict["response"]["songs"][j]["title"] != song_dict["response"]["songs"][j+1]["title"]:
										temp_song_list.append(song_dict["response"]["songs"][j]["title"]) 
						

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
					song_list.append(temp_song_list)

					price_list.append((str(event["stats"]["average_price"])+'0', str(event["stats"]["lowest_price"])+'0', str(event["stats"]["highest_price"])+'0'))

        	
				num_events= len(date_list) 
			
				return render_template("results.html", name_list = name_list, song_list = song_list, link_list=link_list, events=response_dict["events"], max_price = SearchData.objects.first().max_price, user_search= SearchData.objects.first().user_search, category= SearchData.objects.first().category, state = SearchData.objects.first().state, num_days= SearchData.objects.first().num_days, sort= SearchData.objects.first().sort_by, per_page = SearchData.objects.first().per_page, price_list=price_list, api_data=response_dict, time_list=time_list, date_list=date_list, num_events=num_events, pagination = pagination)
			else:

				return render_template("search.html", failed=True)

		else:

			return render_template("search.html", failed=False)

	else:

		return render_template("search.html", anonymous=True)

@app.route("/events/<id>")
def event(id):

	for data in SearchData.objects(poster=current_user.Email):
		data.delete()

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


@app.route("/setlist/<artist>")
def setlist(artist):

	setlist_url = "http://api.setlist.fm/rest/0.1/search/setlists.json?artistName=" + artist
	setlist = []
	index = 0


	try:
		setlist_dict = requests.get(setlist_url).json()

		while setlist_dict["setlists"]["setlist"][index]["sets"] == "" and index<int(setlist_dict["setlists"]["@total"]):
			index=index+1

		
		if setlist_dict["setlists"]["setlist"][index]["sets"] != "":

			if type(setlist_dict["setlists"]["setlist"][index]["sets"]["set"]) is list:
				for show_setlist in setlist_dict["setlists"]["setlist"][index]["sets"]["set"]:
					if "@encore" in show_setlist.keys():
						setlist.append("Encore " + show_setlist["@encore"]+" :")
						
					if type(show_setlist["song"]) is list:
						for song in show_setlist["song"]:
							setlist.append(song["@name"])
							
					else:
						setlist.append(show_setlist["song"]["@name"])
						

			else:
				for song in setlist_dict["setlists"]["setlist"][index]["sets"]["set"]["song"]:
					setlist.append(song["@name"])
					
	except ValueError:
		pass

	session['setlist'] = setlist
	session['artist'] = artist
	return redirect("/test")
	#return render_template("setlist.html", artist= artist, setlist=setlist)


@app.route("/test")
def test():
	return render_template("setlist.html", artist= session.pop('artist'), setlist=session.pop('setlist'))

@app.route("/favorite/<id>")
@login_required

def favorite(id):

	for data in SearchData.objects(poster=current_user.Email):
		data.delete()

	event_url = "https://api.seatgeek.com/2/events/" + id
	event_dict = requests.get(event_url).json()
	poster = newUser.objects(Email=current_user.Email).first()
	if FavoriteEvent.objects(poster=poster, event_id=id).count() == 0:
		new_fav = FavoriteEvent(location_name= event_dict["venue"]["display_location"], avg_px = event_dict["stats"]["average_price"], min_px= event_dict["stats"]["lowest_price"], max_px=event_dict["stats"]["highest_price"], num_tix= event_dict["stats"]["highest_price"], picture= event_dict["performers"][0]["image"], title=event_dict["title"], date_time=event_dict["datetime_local"], location=event_dict["venue"]["name"], event_id=event_dict["id"], link=event_dict["url"], poster=poster)
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

	for favorite in favorites:

		if "T" in favorite.date_time:

			date_str = ""
			time_str = ""
			mystr = ""
			temp_list=[]
			mystr = favorite.date_time
			mystr = mystr.replace('-', ' ')
			mystr = mystr.replace('T', ' ')
			temp_list = (mystr.split(' '))
			date_str= temp_list[1] + "/" + temp_list[2] + "/" + temp_list[0] + " "

			if int(temp_list[3][:2]) > 12:

				time_str =  str(int(temp_list[3][:2])-12) + temp_list[3][2:5] + " PM"

			else:

				time_str = temp_list[3][:5] + " AM"
       
			favorite.date_time= date_str + " " + time_str
			favorite.save()



	for data in SearchData.objects(poster=current_user.Email):
		data.delete()

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

			for data in SearchData.objects(poster=current_user.Email):
				data.delete()
			return redirect('/')

		else:
			return render_template('login.html', form=form, failed=True)
	else:

		return render_template('login.html', form=form)


@app.route("/logout" , methods=['GET', 'POST'])
def logout():

	if current_user.is_authenticated:
		for data in SearchData.objects(poster=current_user.Email):
			data.delete()

	logout_user()

	form= UserForm(request.form)

	return redirect('/login')




if __name__ == "__main__":

	app.run(host="0.0.0.0")

