from flask import Flask, jsonify, url_for, redirect, render_template, session 
from dotenv import load_dotenv
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired
from wtforms.widgets import *
import logging

import os, requests, json

logging.basicConfig(level=logging.ERROR)

load_dotenv()

api_key = os.getenv('api_key')
SECRET_KEY = os.getenv('SECRET_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

#Cross site forgery protection needed to use FlaskWTF
csrf = CSRFProtect(app)


#making a custom Field for WTForms
#class MultiCheckField():
 #   def __init__(self, label, choices, **kwargs):
  #      super(MultiCheckField, self).__init__(*args, kwargs**)


class idForm(FlaskForm):
    id = StringField('id', validators=[DataRequired()])
    submit = SubmitField('Go')

class friendListForm(FlaskForm):
    submit = SubmitField()
    friends = SelectMultipleField("Friends", choices = [], widget=TableWidget(with_table_tag=False), option_widget=CheckboxInput())
    #overriding the __init__ method of the form class
    def __init__(self, choices = None, count = 0, *args, **kwargs): 
        super(friendListForm, self).__init__(*args, **kwargs)
        if choices:
            self.friends.choices = choices
        
    

def getSteamUser(steamids, requestedInfo):
    if requestedInfo == "profiles":
        url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steamids}"
        response = requests.get(url)
        return response
    
    elif requestedInfo == "friends":
        url = f"http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={api_key}&steamid={steamids}"
        response = requests.get(url)
        return response
    
    elif requestedInfo == "games":
        url = f"http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steamids}&format=json&include_appinfo=true"
        response = requests.get(url)
        return response
    
def type_of(param):
    return type(param)

@app.route("/", methods = ['GET', 'POST'])
def home():
    form = idForm()

    
    if form.validate_on_submit():
        session["my_id"] = form.id.data
        id = form.id.data #.data accesses the string data submitted in the form's field
        return redirect(url_for('friends', id = id))
    
    return render_template("index.html", form = form) 

@app.route("/friends/<id>", methods=['GET', 'POST'])
def friends(id):
    response = getSteamUser(id, "friends")
    responseJson = response.json() #json response needs to be parsed to python dict.
    friends = []
    
    for friend in responseJson["friendslist"]["friends"]: #accessing the inner "friends" dict
        friends.append(friend["steamid"])

    profilesResponse = getSteamUser(friends, "profiles")
    profilesResponseJson = profilesResponse.json()
    
    friendList = profilesResponseJson["response"]["players"]
    choices = []
    
    for friend in friendList:
        name = friend["personaname"]
        choices.append((id, name))
    
    form = friendListForm(choices = choices)

    if form.validate_on_submit():
        session["selected"] = form.friends.data
        return redirect(url_for("sharedgames"))

    elif response.status_code == 200:
        return render_template("friendslist.html", form = form)
    
    else: 
        return ("Error, API responded with code: " + str(response.status_code))

@app.route("/sharedgames", methods = ["GET"])
def sharedgames():
    friends = session.get("selected")
    games = []

    for f in friends:
        res = getSteamUser(f, "games")
        res = res.json()

        #the response returns a list of games, using the index of the attriubte I want to be included
        #"name" index = 1

        for g in res["response"]["games"]:
            games.append(g["name"])
    
    return render_template("sharedgames.html", games = games, f = friends)


#Only use reloader in dev branch
#app.run(use_reloader=True, debug=True)
if __name__ == "__main__":
    app.run(use_reloader=True, debug=True)