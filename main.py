from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import bcrypt

load_dotenv()

app = Flask("ArchaeoOpenBase")

mongo = os.getenv('MONGO_URI')
client = MongoClient(mongo)
db = client.get_database("ArchaeoOpenBase")

@app.route("/")
def index():
    return render_template("front/index.html")

@app.route("/viewpost")
def viewpost():
    posts_data=list(db['annonce'].find({}))
    return render_template("viewpost.html", posts = posts_data)

@app.route('/connect', methods=['POST', 'GET'])
def connect():
    if request.method == "POST":
        db_user = db["user"]
        user = db_user.find_one({"utilisateur" : request.form['utilisateur']})
        if user: 
            if bcrypt.checkpw( request.form['mots_de_passe'].encode('utf-8'), user["password"]):
                session['role'] = user['role']
                session['user'] = user['utilisateur']
                return redirect("/")
            else : 
                return render_template('front/connect.html', ereur = "ce mots de passe ne correspond pas")
        else : 
            return render_template('connect.html')
    return render_template('front/connect.html')

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        db_user = db["user"]
        if(db_user.find_one({"utilisateur" : request.form['utilisateur']})):
            return render_template('register.html', erreur = "le nom existe deja")
        else :
            if(request.form["mots_de_passe"] == request.form["confirme_mots_de_passe"]):
                utilisateur = request.form['utilisateur']
                mdp = request.form['mots_de_passe']

                mdp_crypte = mdp.encode("utf-8")
                salt = bcrypt.gensalt()
                mdp_hash = bcrypt.hashpw(mdp_crypte, salt)

                new_user = ({
                    "utilisateur" : utilisateur,
                    "mots_de_passe" : mdp_hash,
                    "role" : "user"
                })

                db["user"].insert_one(new_user)
                return redirect("/")
            else :
                return render_template('register.html', ereur = "les mots de passe ne corresponde pas")
    return render_template('front/register.html')


app.run(host ='0.0.0.0', port=81)