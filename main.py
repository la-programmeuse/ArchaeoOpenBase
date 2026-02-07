from flask import Flask, render_template
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask("ArchaeoOpenBase")

mongo = os.getenv('MONGO_URI')
client = MongoClient(mongo)
db = client.get_database("ArchaeoOpenBase")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/viewpost")
def viewpost():
    posts_data=list(db['annonce'].find({}))
    return render_template("viewpost.html", posts = posts_data)


app.run(host ='0.0.0.0', port=81)