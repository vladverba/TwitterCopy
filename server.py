
"""
Columbia's COMS W4111.001 Introduction to Databases
Example Webserver
To run locally:
    python server.py
Go to http://localhost:8111 in your browser.
A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""
import os
  # accessible as a variable in index.html:
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from random import randint
from datetime import datetime
from datetime import date

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following is a dummy URI that does not connect to a valid database. You will need to modify it to connect to your Part 2 database in order to use the data.
#
# XXX: The URI should be in the format of:
#
#     postgresql://USER:PASSWORD@35.243.220.243/proj1part2
#
# For example, if you had username gravano and password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://gravano:foobar@35.243.220.243/proj1part2"
#
DATABASEURI = "postgresql://nd2533:5086@35.243.220.243/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above.
#
engine = create_engine(DATABASEURI)

#
# Example of running queries in your database
# Note that this will probably not work if you already have a table named 'test' in your database, containing meaningful data. This is only an example showing you how to run queries in your database using SQLAlchemy.
#
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request.

  The variable g is globally accessible.
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't, the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to, for example, localhost:8111/foobar/ with POST or GET then you could use:
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
#
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments, e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print(request.args)


  #
  # example of a database query
  #
  cursor = g.conn.execute("SELECT name FROM test")
  names = []
  for result in cursor:
    names.append(result['name'])  # can also be accessed using result[0]
  cursor.close()

#cursor = g.conn.execute("SELECT handle FROM Users WHERE handle = name") #pseudo

#cursor = g.conn.execute("SELECT ")

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #
  #     # creates a <div> tag for each element in data
  #     # will print:
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  context = dict(data = names)


  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at:
#
#     localhost:8111/another
#
# Notice that the function name is another() rather than index()
# The functions for each app.route need to have different names
#
@app.route('/another')
def another():
  return render_template("another.html")

# Displays a user's stories
@app.route('/your_stories', methods=['GET'])
def your_stories():
    try:
        handle = request.args.get('handle')
        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            stories = get_stories_from_users([handle])
            return render_template("your_stories.html", stories=stories)
        else:
            return redirect('/')
    except:
        return redirect('/')

# Checks if the user exists.
# If the user exists, display stories of people they follow.
@app.route('/displayStories', methods=['GET'])
def displayStories():
    try:
        handle = request.args.get('handle')
        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            following = get_users_someone_follows(handle)
            stories = get_stories_from_users(following)
            return render_template("stories_of_people_you_follow.html", stories=stories)
        else:
            return redirect('/')
    except:
        return redirect('/')

# Creates an account. Every account is unverified by default.
@app.route('/create_account', methods=['GET'])
def create_account():
    date = datetime.today()
    handle = request.args.get('handle')
    checked = request.args.get('checkbox')

    # error handling
    if (len(handle) > 20):
        return redirect('/')

    try:
        if (handle is not None): # insert into users
            g.conn.execute("""INSERT INTO users VALUES (%s, %s);""", handle, date)

        if (checked): # then insert into unverified_users specifically
            g.conn.execute("""INSERT INTO unverified_users VALUES (%s, %s);""", handle, True)
        else:
            g.conn.execute("""INSERT INTO unverified_users VALUES (%s, %s);""", handle, False)

        return redirect('/')
    except:
        return redirect('/')


# Creates a tweet for a given handle.
@app.route('/create', methods=['GET'])
def create():
    try:
        handle = request.args.get('handle')
        text = request.args.get('text')
        media = request.args.get('media')

        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            create_tweet(handle, text, media)

        return redirect('/')
    except:
        return redirect('/')

# Displays a user's tweets.
@app.route('/your_tweets', methods=['GET'])
def your_tweets():
    try:
        handle = request.args.get('handle')
        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            tweets = get_tweets_from_users([handle], handle)
            return render_template("your_tweets.html", tweets=tweets)
        else:
            return redirect('/')
    except:
        return redirect('/')

# Checks if the user exists.
# If the user exists, display tweets of people they follow.
@app.route('/display', methods=['GET'])
def display():
    try:
        handle = request.args.get('handle')
        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            following = get_users_someone_follows(handle)
            tweets = get_tweets_from_users(following, handle)
            return render_template("tweets_of_people_you_follow.html", tweets=tweets)
        else:
            return redirect('/')
    except:
        return redirect('/')

# Likes a tweet. Also updates notifications table.
@app.route('/like', methods=['GET'])
def like():
    try:
        tid = 0
        users_handle = "" # person who did the liking
        user_to_send_notification_to = "" # person who receives the notification
        for key, value in request.args.items():
            if value == "like":
                user_to_send_notification_to = key.split("+")[0]
                tid = key.split("+")[1]
                users_handle = key.split("+")[2]

        # update like_num
        g.conn.execute("""UPDATE tweets_with_content t SET like_num=like_num+1 WHERE CAST(t.tid as bigint)=%s""", tid)

        # update view
        following = get_users_someone_follows(users_handle)
        tweets = get_tweets_from_users(following, users_handle)

        # send notification
        add_notification(user_to_send_notification_to, users_handle + " liked your tweet!")

        if (users_handle == user_to_send_notification_to):
            tweets = get_tweets_from_users([users_handle], users_handle)
            return render_template("your_tweets.html", tweets=tweets)
        else:
            return render_template("tweets_of_people_you_follow.html", tweets=tweets)
    except:
        return redirect('/')

# Retweets a tweet. Also updates notifications table.
@app.route('/retweet', methods=['GET'])
def retweet():
    try:
        tid = 0
        users_handle = ""
        user_to_send_notification_to = ""
        for key, value in request.args.items():
            if value == "retweet":
                user_to_send_notification_to = key.split("+")[0]
                tid = key.split("+")[1]
                users_handle = key.split("+")[2]

        # update retweet_num
        g.conn.execute("""UPDATE tweets_with_content t SET retweet_num=retweet_num+1 WHERE CAST(t.tid as bigint)=%s""", tid)

        # update view
        following = get_users_someone_follows(users_handle)
        tweets = get_tweets_from_users(following, users_handle)

        # send notification
        add_notification(user_to_send_notification_to, users_handle + " retweeted your tweet!")

        if (users_handle == user_to_send_notification_to):
            tweets = get_tweets_from_users([users_handle], users_handle)
            return render_template("your_tweets.html", tweets=tweets)
        else:
            return render_template("tweets_of_people_you_follow.html", tweets=tweets)
    except:
        return redirect('/')

# Follow a user
@app.route('/add', methods=['POST'])
def add():
    try:
      followerHandle = request.form['followerHandle']
      followingHandle = request.form['followedHandle']

      handles_exist = check_if_handle_exists(followerHandle) and check_if_handle_exists(followingHandle)
      already_following = followingHandle in get_users_someone_follows(followerHandle)

      if(handles_exist and not already_following):
          g.conn.execute("INSERT INTO following VALUES (%s, %s)", followerHandle, followingHandle)
          return redirect('/')
      else:
          return redirect('/')
    except:
        return redirect('/')

# browse someones tweets
@app.route('/browse', methods=["GET"])
def browse():
    try:
        handle = request.args.get('handle')
        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            tweets = get_tweets_from_users([handle], handle)
            return render_template("browse.html", tweets=tweets)
        else:
            return redirect('/')
    except:
        return redirect('/')

# Creates/sends a message for a given handle.
@app.route('/createMessage', methods=['GET'])
def createMessage():
    try:
        senderHandle = request.args.get('senderHandle')
        recipientHandle = request.args.get('recipientHandle')
        text = request.args.get('messageText')
        media = request.args.get('messageMedia')

        handle_exists = check_if_handle_exists(senderHandle)
        handle_exists2 = check_if_handle_exists(recipientHandle)

        if(handle_exists and handle_exists2):
            create_message(senderHandle, recipientHandle, text, media)

        return redirect('/')
    except:
        return redirect('/')

# Displays a user's recieved messages
@app.route('/your_messages', methods=['GET'])
def your_messages():
    try:
        handle = request.args.get('handle')
        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            messages = get_messages_from_users([handle], handle)
            return render_template("your_messages.html", messages=messages)
        else:
            return redirect('/')
    except:
        return redirect('/')

# Creates a story for a given handle.
@app.route('/createStory', methods=['GET'])
def createStory():
    try:
        handle = request.args.get('handle')
        text = request.args.get('text')
        media = request.args.get('media')

        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            create_story(handle, text, media)

        return redirect('/')
    except:
        return redirect('/')

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()

# Displays a user's notifications
@app.route('/your_notifications', methods=['GET'])
def your_notifications():
    try:
        handle = request.args.get('handle')
        handle_exists = check_if_handle_exists(handle)
        if(handle_exists):
            notifications = get_notifications_from_users([handle])
            return render_template("your_notifications.html", notifications=notifications)
        else:
            return redirect('/')
    except:
        return redirect('/')

# HELPER FUNCTIONS

# generates a random id
def generate_random_id():
    return randint(10000000000, 99999999999)

## returns a a dict. of notifications created from a list of users
def get_notifications_from_users(users):

    notifications={}
    for person in users:
        cursor = g.conn.execute("SELECT * FROM notification_received_by_user n where n.handle=%s", person)
        for record in cursor:
            time = g.conn.execute("SELECT date_time FROM notification_received_by_user n where CAST(n.nid as bigint)=%s", record['nid']).fetchone()[0]
            text = g.conn.execute("SELECT notification from notification_received_by_user n where CAST(n.nid as bigint)=%s", record['nid']).fetchone()[0]
            date = str(record['date_time']).split()[0]
            time = str(record['date_time']).split()[1]
            notifications[record['nid']] = (text, date, time)
    return notifications

# SQL QUERIES

## returns a a dict. of stories created from a list of users
def get_stories_from_users(users):
    stories={}
    for person in users:
        cursor = g.conn.execute("SELECT * from stories_with_content t where t.handle=%s", person)
        for record in cursor:
            handle = record['handle']
            date = str(record['datetime']).split()[0]
            time = str(record['datetime']).split()[1]
            media = g.conn.execute("SELECT media from content c where CAST(c.cid as bigint)=%s", record['cid']).fetchone()[0]
            text = g.conn.execute("SELECT text from content c where CAST(c.cid as bigint)=%s", record['cid']).fetchone()[0]
            stories[record['cid']] = (text, media, handle, date, time)
    return stories

# creates a story under a handle (calls on create_content)
def create_story(handle, text, media):
    sid = randint(10000000000, 99999999999)
    while(g.conn.execute("SELECT * FROM stories_with_content t where CAST(t.sid as bigint)=%s", sid).fetchone() is not None):
        sid = randint(10000000000, 99999999999)

    date_time = str(datetime.now()).split(".")[0]

    cid = create_content(text, media)
    g.conn.execute("""INSERT INTO stories_with_content VALUES(%s, %s, %s, %s)""", sid, date_time, cid, handle)

# adds a notification to the database
def add_notification(handle, notification):
    id = generate_random_id()
    date_time = str(datetime.now()).split(".")[0]

    g.conn.execute("""INSERT INTO notification_received_by_user VALUES(%s, %s, %s, %s);""", id, notification, handle, date_time)


# creates a tweet under a handle (calls on create_content)
def create_tweet(handle, text, media):
    id = generate_random_id()
    while(g.conn.execute("SELECT * from tweets_with_content t where CAST(t.tid as bigint)=%s", id).fetchone() is not None):
        id = randint(10000000000, 99999999999)

    like_num = 0
    retweet_num = 0
    date_time = str(datetime.now()).split(".")[0]

    cid = create_content(text, media)
    g.conn.execute("""INSERT INTO tweets_with_content VALUES(%s, %s, %s, %s, %s, %s)""", id, date_time, like_num, retweet_num, cid, handle)

# creates a content, returns its cid (for use in create_tweet)
def create_content(text, media):
    cid = generate_random_id()
    while(g.conn.execute("SELECT * from content c where CAST(c.cid as bigint)=%s", cid).fetchone() is not None):
        cid = generate_random_id()
    g.conn.execute("""INSERT INTO content VALUES (%s, %s, %s);""", cid, text, media)

    return cid

# checks if a handle exists
def check_if_handle_exists(handle):
    cursor = g.conn.execute("SELECT * from users u where u.handle=%s", handle)
    record = cursor.fetchone()
    if(record is None):
        return False
    else:
        return True

# returns a list of people someone follows
def get_users_someone_follows(handle):
    cursor = g.conn.execute("SELECT * from following f where f.follower=%s", handle)
    following = []
    for record in cursor:
        following.append(record['followed'])

    return following

# returns a a dict. of tweets created from a list of users
# users_handle is the user which called on this method
def get_tweets_from_users(users, users_handle):

    tweets={}
    for person in users:
        # all tweets of the person they follow
        cursor = g.conn.execute("SELECT * from tweets_with_content t where t.handle=%s", person)
        for record in cursor:
            tid = record['tid']
            text = g.conn.execute("SELECT text from content c where CAST(c.cid as bigint)=%s", record['cid']).fetchone()[0]
            media = g.conn.execute("SELECT media from content c where CAST(c.cid as bigint)=%s", record['cid']).fetchone()[0]
            like_num = record['like_num']
            retweet_num = record['retweet_num']
            date = str(record['date_time']).split()[0]
            time = str(record['date_time']).split()[1]
            tweets[record['cid']] = (person, tid, text, media, like_num, retweet_num, users_handle, date, time)
    return tweets

# creates a message under a handle (calls on create_content)
def create_message(senderHandle, recipientHandle, text, media):
    mid = generate_random_id()
    while(g.conn.execute("SELECT * FROM messages_with_content m where CAST(m.mid as bigint)=%s", mid).fetchone() is not None):
        mid = randint(10000000000, 99999999999)

    date_time = str(datetime.now()).split(".")[0]

    cid = create_content(text, media)
    g.conn.execute("""INSERT INTO messages_with_content VALUES(%s, %s, %s, %s, %s)""", mid, date_time, cid, senderHandle, recipientHandle)

## returns a a dict. of messages
def get_messages_from_users(users, users_handle):

    messages={}
    for person in users:
        cursor = g.conn.execute("SELECT * from messages_with_content t where t.recipient=%s", person)
        for record in cursor:
            mid = record['mid']
            text = g.conn.execute("SELECT text from content c where CAST(c.cid as bigint)=%s", record['cid']).fetchone()[0]
            media = g.conn.execute("SELECT media from content c where CAST(c.cid as bigint)=%s", record['cid']).fetchone()[0]
            date = str(record['date_time']).split()[0]
            time = str(record['date_time']).split()[1]
            sender = record['sender']
            messages[record['cid']] = (person, mid, text, media, users_handle, date, time, sender)
    return messages

if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using:

        python server.py

    Show the help text using:

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)

  run()
