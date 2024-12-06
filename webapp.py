from flask import Flask, redirect, url_for, session, request, jsonify
from flask_oauthlib.client import OAuth
from markupsafe import Markup
#from flask_oauthlib.contrib.apps import github #import to make requests to GitHub's OAuth
from flask import render_template
from bson.objectid import ObjectId
from pymongo import MongoClient



import pymongo
import pprint
import os
import sys

#https://www.perplexity.ai/search/file-c-users-dsw-desktop-fast-CZttmv_aSG.fWt_DlZRu8Q
#david's CONVERSATION WITH PERPLEXITY

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

connection_string = os.environ["MONGO_CONNECTION_STRING"]
db_name = os.environ["MONGO_DBNAME"]
client = pymongo.MongoClient(connection_string)
db = client[db_name]
Posts = db['Posts']


#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
    is_logged_in = 'github_token' in session #this will be true if the token is in the session and false otherwise
    return {"logged_in":is_logged_in}
    
def data(text):
#insert data
    print(text)
    db.Posts.insert_one({"Posts":text})
    
@app.route('/')
def home():
    return render_template('home.html', past_posts=forum_post())

@app.route('/delete', methods=['POST'])
def delete_post():
    id = ObjectId(request.form['delete'])
    Posts.delete_one({'_id': id})
    return home()
    
@app.route('/posted', methods=['POST'])
def get_post():
    print(request.form['message'])
    message = [str(request.form['message'])]
    data(message)
    return home()

def forum_post():
    comment = ""
    comment += Markup("<h2>Join the Conversation!</h2>")
	
    for i in Posts.find():
        s = str(i['_id'])
        comment += Markup(f'''
            <div class="container mt-3">
                <table class="table table-hover">
                    <thead><tr><th>Username</th></tr></thead>
                    <tbody>
                        <tr><td>{i['Posts']}</td></tr>
                        <tr><td>
                            <form action="/delete" method="post">
                                <button type="submit" name="delete" value="{s}">Delete</button>
                            </form>
                        </td></tr>
                    </tbody>
                </table>
            </div>
        ''')
       
    print(comment)
    return comment
    
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You are logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)      
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('use').rdata
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
    

if __name__ == '__main__':
    app.run()
