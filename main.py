from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import bcrypt
from bson.objectid import ObjectId

load_dotenv()

app = Flask("ArchaeoOpenBase")

mongo = os.getenv('MONGO_URI')
client = MongoClient(mongo)
db = client.get_database("ArchaeoOpenBase")

@app.route("/")
def index():
        annonce_data = list(db['annonce'].find({}))
        user_data = list(db['user'].find({}))
        for annonce in annonce_data:
            annonce["_id"] = str(annonce["_id"])
                # Conversion sécurisée en float si la clé existe
            for key in ["lat", "lng"]:
                if key in annonce and annonce[key] is not None:
                    try:
                        annonce[key] = float(annonce[key])
                    except ValueError:
                        annonce[key] = None
        return render_template("front/index.html", annonce=annonce_data)

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
            if bcrypt.checkpw( request.form['mots_de_passe'].encode('utf-8'), user["mots_de_passe"]):
                session['role'] = user['role']
                session['user'] = user['utilisateur']
                return redirect("/")
            else : 
                return render_template('front/connect.html', ereur = "ce mots de passe ne correspond pas")
        else : 
            return render_template('front/connect.html')
    return render_template('front/connect.html')

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        db_user = db["user"]
        if(db_user.find_one({"utilisateur" : request.form['utilisateur']})):
            return render_template('front/register.html', erreur = "le nom existe deja")
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
                return render_template('front/register.html', erreur = "les mots de passe ne corresponde pas")
    return render_template('front/register.html')

@app.route('/publish', methods = ['POST', 'GET']) 
def publish():
    if 'user' not in session:
        return render_template('front/register.html')

    app.config['UPLOAD_FOLDER'] = "static/uploads"
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


    if request.method == "POST":
        print("request.files keys:", request.files.keys())
        db_annonces = db['annonces']
        titre = request.form["titre_annonces"]
        description = request.form["phrase_annonces"]
        N_inventaire = request.form["n_inventaire"]
        Latitude = request.form["lat"]
        Longitude = request.form["lng"]
        image = request.files.get("image")
        video = request.files.get('video')

        filename = None
        video_filename = None

        if image and image.filename != "":
            filename = image.filename
            image.save("static/uploads/" + filename)

        else : 
            filename = None
            print("Nom fichier :", image.filename if image else "AUCUN")

        if video and video.filename != "":
            video_filename = secure_filename(video.filename)
            video.save(os.path.join(app.config['UPLOAD_FOLDER'], video_filename))

        uploads_folder = os.path.join(os.path.dirname(__file__), "static", "uploads")
        os.makedirs(uploads_folder, exist_ok=True)

        if titre and description:
            db_annonces.insert_one({
                'titre_annonces' : titre,
                'phrase_annonces' : description,
                'lat' : Latitude,
                'lng' : Longitude,
                'image': filename,
                'video': video_filename,
                'n_inventaire' : N_inventaire
            })
            return redirect("/")
        else: 
            return render_template("publish.html", erreur = 'Veuillez remplir tout les champs obligatoires svp')
    return render_template("publish.html")


###########ADMIN############

@app.route('/admin')
def admin():
    annonce_data = list(db['annonce'].find({}))
    user_data = list(db['user'].find({}))
    if 'user' in session and session['role'] == 'admin' :
        return render_template('back/back_accueil.html', annonce = annonce_data, user = user_data)
    else : 
        return render_template('index.html', erreur = "vous n'avez pas les droit", annonce = annonce_data, user = user_data)

@app.route('/admin/update_role/<user_id>')
def update_role(user_id):
    if 'util' in session and session['role'] == 'admin':
        new_role = request.form.get('role')

        db['user'].update_one({"_id" : ObjectId(user_id)}, {"$set" : {"role" : new_role}})

    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<user_id>')
def delete_user(user_id):
    if 'util' in session and session['role'] == 'admin':
        db['user'].delete_one({"_id" : ObjectId(user_id)})
    return redirect(url_for('admin'))



app.run(host ='0.0.0.0', port=81)