from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
#from flask_oauthlib.contrib.apps import github #import to make requests to GitHub's OAuth
from flask import render_template


import pymongo
import pprint
import os
import sys

# This code originally from https://github.com/lepture/flask-oauthlib/blob/master/example/github.py
# Edited by P. Conrad for SPIS 2016 to add getting Client Id and Secret from
# environment variables, so that this will work on Heroku.
# Edited by S. Adams for Designing Software for the Web to add comments and remove flash messaging

app = Flask(__name__)

app.debug = False #Change this to False for production
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' #Remove once done debugging

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
oauth.init_app(app) #initialize the app to be able to make requests for user information

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',  
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)


#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
    is_logged_in = 'github_token' in session #this will be true if the token is in the session and false otherwise
    return {"logged_in":is_logged_in}
    
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/posted', methods=['POST'])
def post():
    return render_template('home.html')
    #This function should add the new post to the JSON file of posts and then render home.html and display the posts.  
    #Every post should include the username of the poster and text of the post. 

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            #pprint.pprint(vars(github['/email']))
            #pprint.pprint(vars(github['api/2/accounts/profile/']))
            message='You were successfully logged in as ' + session['user_data']['login'] + '.'
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
    return render_template('message.html', message=message)


#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')
    
    
def main():
    connection_string = os.environ["MONGO_CONNECTION_STRING"]
    db_name = os.environ["MONGO_DBNAME"]
    
    client = pymongo.MongoClient(connection_string)
    db = client[db_name]
    collection = db['Posts'] #1. put the name of your collection in the quotes
    
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    
    #2. add a document to your collection using the insert_one method
    
    Posts = {"Name":"Yellow", "R":255, "G":255, "B":0}
    a = collection.insert_one(Posts)
    print(a)
    #3. print the number of documents in the collection
    x=0
    for color in collection.find():
        x=x+1
    print(x)
    #loops to see how many documents there are and prints how much it recorded.
    
    #4. print the first document in the collection
    print(collection.find()[0])
    #prints first document by the zero which gets the frist valu of a dictionary.
    
    #5. print all documents in the collection
    for Posts in collection.find():
        print(Posts)
    #loops and prnts every document that is found in the collection through .find
    
    #6. print all documents with a particular value for some attribute
    for Posts in collection.find({"R":255}):
        print(Posts)
    #loops to find every document in the ocllection that has the value 255 for "R" then prints those documents

    #ex. print all documents with the birth date 12/1/1990
    for Posts in collection.find({"Birthdate":"12/1/1990"}):
        print(Posts)


if __name__ == '__main__':
    app.run()
