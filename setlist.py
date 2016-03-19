from flask import Flask, render_template, request
from xml.dom import minidom
import urllib


import requests

app = Flask(__name__)

app.config["DEBUG"] = False

@app.route("/")

def hello():

	return render_template("hello.html")


@app.route("/name")

def name():

	return "Dave"

@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "POST":
        url = "http://api.setlist.fm/rest/0.1/search/artists?artistName=" + request.form["user_search"]
        xml_str = urllib.urlopen(url).read()
        xml_doc = minidom.parseString(xml_str)
        return render_template("new_results.html", api_data=xml_doc)
    else: # request.method == "GET"
        return render_template("search.html")




if __name__ == "__main__":

	app.run(host="0.0.0.0", port=4000)

