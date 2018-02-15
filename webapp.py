from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template

import pprint
import os
import json

app = Flask(__name__)

app.debug = True #Change this to False for production

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)

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

posts_file = "posts.json" #use a JSON file to store the past posts.  A global list variable doesn't work when handling multiple requests coming in and being handled on different threads

#context processors run before templates are rendered and add variable(s) to the template's context
#context processors must return a dictionary 
#this context processor adds the variable logged_in to the conext for all templates
@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    return render_template('home.html', past_posts=posts_to_html())

@app.route('/posted', methods=['POST'])
def post():
    text = request.form['message']
    with open(posts_file, 'r+') as f:
        posts = json.load(f)
        posts.append([session['user_data']['login'],text]) #add [username,message] to the list of posts
        f.seek(0) #move to the beginning of the file
        f.truncate() #clear the file before writing to it
        json.dump(posts, f)
    return render_template('home.html', past_posts=posts_to_html())

def posts_to_html():
    try:
        print(os.path.abspath(posts_file))
        with open(posts_file, 'r') as f:
            posts = json.load(f)
            posts_code = Markup('<table class="posts"><tr><th>User</th><th>Message</th></tr>')
            for p in reversed(posts): #put most recent posts at the top
                user = p[0]
                message = p[1]
                posts_code += Markup("<tr><td>" + user + "</td><td>" + message + "</td></tr>")
            posts_code += Markup('</table>')
    except Exception as inst:
        print(inst)
        posts_code=""
    return posts_code

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():   
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

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
            message='You were successfully logged in as ' + session['user_data']['login']
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
