from flask import Flask, jsonify, url_for, redirect, render_template, session 
from dotenv import load_dotenv
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired
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

class idForm(FlaskForm):
    id = StringField('id', validators=[DataRequired()])
    submit = SubmitField('Go')

class friendListForm(FlaskForm):
    submit = SubmitField(validators=[DataRequired()])
    friends = SelectMultipleField("Friends", choices = [], validators=[DataRequired()])
    #overriding the __init__ method of the form class
    def __init__(self, choices = None, *args, **kwargs): 
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

def type_of(param):
    return type(param)

@app.route("/", methods = ['GET', 'POST'])
def home():
    form = idForm()
    if form.validate_on_submit():
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
        choices.append(friend)
        
    form = friendListForm(choices = choices)

    if form.is_submitted():
        selected = form.friends.data

        return render_template("sharedgames.html", type_of = type_of, form = form,  selected = selected)
        #session["selection"] = form
        #return redirect(url_for("sharedgames"))

    elif response.status_code == 200:
        return render_template("friendslist.html", form = form)
    
    else: 
        return ("Error, API responded with code: " + str(response.status_code))

@app.route("/sharedgames", methods = ["GET"])
def sharedgames():
    selected = session.get('selection')
    selected = selected.friends
    return render_template("sharedgames.html", selected = selected, data = data)


#Only use reloader in dev branch
#app.run(use_reloader=True, debug=True)
if __name__ == "__main__":
    app.run(use_reloader=True, debug=True)