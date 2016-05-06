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

app.config["DEBUG"] = True
app.config['SECRET_KEY'] = 'ajosjdfajjjj3453453oj!!!oij'
app.config['WTF_CSRF_ENABLED'] = True


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

SCOPE = "playlist-modify-public playlist-modify-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()






@app.route("/playlist", methods=["POST", "GET"])
def playlist():

	REDIRECT_URI = "{}:{}/playlists/q".format(CLIENT_SIDE_URL, PORT)

	auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
	}

	url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.iteritems()])
	auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
	return redirect(auth_url)


@app.route("/spotify", methods=["POST", "GET"])
def spotify():

	REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)

	auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
	}

	url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.iteritems()])
	auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
	return redirect(auth_url)


@app.route("/playlists/q", methods=["POST", "GET"])
def playlists():

	REDIRECT_URI = "{}:{}/playlists/q".format(CLIENT_SIDE_URL, PORT)

	playlists = []

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
	
    #Get user playlist data
	playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
	playlists_data = requests.get(playlist_api_endpoint, headers=authorization_header).json()

	for playlist in playlists_data["items"]:
		playlists.append(playlist["name"])

	return render_template("home.html", playlists = playlists, current_song= session["current_song"], artist_name=session["artist_name"], album_image= session["album_image"])

@app.route("/callback/q", methods=["POST", "GET"])
def callback():

	setlist_ids = {}
	playlist = request.form["playlist"]
	save_delete = request.form["answer"]
	current_song = session.pop("current_song")
	


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

	

	

	try:

		response = requests.post(playlist_api_endpoint, data="{\"name\":\"" + setlist_name + "\"}", headers=authorization_header).json()
		song_url = response["tracks"]["href"]

		for song in setlist:
			if song[0][:6] != "Encore":

				try:
					track_info = requests.get("https://api.spotify.com/v1/search?q=track:" + song[0] +"%20artist:" + artist_name + "&type=track").json()
					
					if track_info["tracks"]["items"] == []:
						
						if song[1] != "":
							#track_info = requests.get("https://api.spotify.com/v1/search?q=track:" + song + "&type=track").json()
							track_info = requests.get("https://api.spotify.com/v1/search?q=track:" + song[0] +"%20artist:" + song[1] + "&type=track").json()
						

							if track_info["tracks"]["items"] == []:
								errors.append(song)
							else:
								song_response = requests.post(song_url + "?uris=" + track_info["tracks"]["items"][0]["uri"], headers=authorization_header).json()
								songs.append(song)
						else:
							errors.append(song)
					else:
						song_response = requests.post(song_url + "?uris=" + track_info["tracks"]["items"][0]["uri"], headers=authorization_header).json()
						songs.append(song)

				except ValueError:
					errors.append(song)

				

    	# Get user playlist data
		#playlist_api_endpoint = "{}/playlists".format(profile_data["href"])
		#playlists_data = requests.get(playlist_api_endpoint, headers=authorization_header).json()
    	
		#for playlist in playlists_data["items"]:
		#	if setlist_ids.get(playlist["name"]) == None:
		#		setlist_ids[playlist["name"]] = True
		#	else:
		#		playlist_url = playlist["href"] + "/followers"
		#		playlist_response = requests.delete(playlist_url, headers=authorization_header)

		


	except IOError:
		pass



	return render_template("spotify.html")




@app.route("/")
def hello():

	song_info = requests.get("http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=dpiccolella&api_key=e8d959e5d2743dca3d2962338084b0ed&format=json").json()
	current_song = []
	album_image = []
	artist_name = []



	if "@attr" in song_info["recenttracks"]["track"][0].keys():
		if song_info["recenttracks"]["track"][0]["@attr"]["nowplaying"] == "true":
			current_song.append(song_info["recenttracks"]["track"][0]["name"])
			album_image.append(song_info["recenttracks"]["track"][0]["image"][3]["#text"])
			artist_name.append(song_info["recenttracks"]["track"][0]["artist"]["#text"])
			#print song_info["recenttracks"]["track"][0]["image"][1]["#text"]

	session["current_song"] = current_song
	session["album_image"] = album_image
	session["artist_name"] = artist_name

	return redirect("/playlist")



if __name__ == "__main__":

	app.run(host="0.0.0.0")

