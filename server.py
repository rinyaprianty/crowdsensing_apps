from flask import Flask, render_template, request
from app.config.middleware import checkLogin
from app.controllers import misc, user, station, scrap, maps
import os
import threading

import logging

# MVC (MODEL, VIEWS, CONTROLLER)

# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

## ---------- START USERS ---------- ##
@app.route("/users")
@checkLogin
def user_index():
    return user.index() 

@app.route("/users/create")
@checkLogin
def user_create():
    return user.create() 

@app.route("/users/store", methods=['POST'])
@checkLogin
def user_store():
    return user.store(request)

@app.route("/users/<int:id>/update", methods=['POST'])
@checkLogin
def user_update(id):
    return user.update(request, id)

@app.route("/users/<int:id>/edit")
@checkLogin
def user_edit(id):
    return user.edit(id)

@app.route("/users/<int:id>/delete")
@checkLogin
def user_delete(id):
    return user.delete(id)
## ---------- END USERS ---------- ##

## ---------- START STATION ---------- ##
@app.route("/station")
@checkLogin
def station_index():
    return station.index()

@app.route("/station/create")
@checkLogin
def station_create():
    return station.create() 

@app.route("/station/store", methods=['POST'])
@checkLogin
def station_store():
    return station.store()

@app.route("/station/<int:id>/update", methods=['POST'])
@checkLogin
def station_update(id):
    return station.update(id)

@app.route("/station/<int:id>/edit")
@checkLogin
def station_edit(id):
    return station.edit(id)

@app.route("/station/<int:id>/delete")
@checkLogin
def station_delete(id):
    return station.delete(id)
## ---------- END STATION ---------- ##

## ---------- START SCRAPING ---------- ##
@app.route("/scraping")
@checkLogin
def scraping_index():
    return scrap.index()

@app.route("/scraping/get-data")
@checkLogin
def scraping_getData():
    return scrap.getDataNew()

@app.route("/scraping/start")
@checkLogin
def start_scraping():
    background_thread = threading.Thread(target=background_task)
    background_thread.start()
    return "started"

def background_task():
    return scrap.dscrap()

@app.route("/scraping/startV2")
@checkLogin
def start_scrapingV2():
    return scrap.doScrapNew()
## ---------- END SCRAPING ---------- ##


## ---------- START MAP ---------- ##
@app.route("/maps")
@checkLogin
def maps_index():
    return maps.index()


@app.route("/maps/get-data")
@checkLogin
def maps_getData_index():
    return maps.getData()
## ---------- END MAP ---------- ##

##MISC
@app.route("/")
@checkLogin
def index():
    return misc.index()

##MISC
@app.route("/login")
def login():
    return misc.login()

@app.route("/doLogin", methods=['POST'])
def doLogin():
    return misc.doLogin(request.form)

@app.route("/logout")
def logout():
    return misc.logout()

app.secret_key = '3RDLwwtFttGSxkaDHyFTmvGytBJ2MxWT8ynWm2y79G8jm9ugYxFFDPdHcBBnHp6E'
app.config['SESSION_TYPE'] = 'filesystem'

@app.context_processor
def inject_stage_and_region():
    return dict(APP_NAME=os.environ.get("APP_NAME"),
        APP_AUTHOR=os.environ.get("APP_AUTHOR"),
        APP_TITLE=os.environ.get("APP_TITLE"),
        APP_LOGO=os.environ.get("APP_LOGO"))

if __name__ == "__main__":
    app.run()
    #app.run(host='0.0.0.0', port=5299)