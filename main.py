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
app.secret_key = os.urandom(24)

result = db['annonces'].update_many({"$or" : [
    {"likes" : {"$exists" : False}},
    {"liked_by" : {"$exists" : False}}
]},
    {
        "$set" : {  "likes" : 0,
                    "liked_by" : []
                }
    }
)

print("database uploaded")

def get_youtube_id(url):
    if not url:
        return None

    match = re.search(
        r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})",
        url
    )

    return match.group(1) if match else None


@app.route('/')

@app.route("/")
def index():
        annonce_data = list(db['annonces'].find({}))
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
            annonce["youtube_id"] = get_youtube_id(
                annonce.get("youtube_url")
            )
        return render_template("front/index.html", annonce=annonce_data)

@app.route("/search", methods = ['GET'])
def search():
    
    print(db["annonces"].find_one())
    query = request.args.get('q', '').strip()

    if query == '':
        result = list(db["annonces"].find({}))
    else :
        result =   list(db["annonces"].find({
            "$or" : [
                {"titre_annonces" : {"$regex" : query, "$options" : "i"} },
                {"phrase_annonces" : {"$regex" : query, "$options" : "i"} }
            ]
        }))
    return render_template("front/search_result.html", annonces=result, query=query)

@app.route("/viewpost/<id>")
def viewpost(id):
    item = db['annonces'].find_one({"_id": ObjectId(id)})
    return render_template("front/viewpost.html", item=item)

@app.route('/connect', methods=['GET', 'POST'])
def connect():
    # Si c'est un GET, afficher le formulaire
    if request.method == 'GET':
        return render_template('front/connect.html')

    # Sinon, POST = tentative de connexion
    utilisateur = request.form.get('utilisateur')
    mots_de_passe = request.form.get('mots_de_passe')

    if not utilisateur or not mots_de_passe:
        return render_template('front/connect.html', erreur="Veuillez remplir tous les champs")

    user = db.user.find_one({'utilisateur': utilisateur})

    if not user:
        return render_template('front/connect.html', erreur="Le nom d'utilisateur n'existe pas")

    # Vérification du mot de passe (hashé avec bcrypt)
    if bcrypt.checkpw(mots_de_passe.encode('utf-8'), user['mots_de_passe']):
        # Création de la session, on créer les cookies pour une session
        session['role'] = user['role']
        session['user'] = utilisateur
        return redirect(url_for("index"))
    else:
        return render_template('front/connect.html', erreur="Le mot de passe est incorrect")

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

                if len(mdp) < 8:
                    return redirect(url_for("front/register"))

                new_user = ({
                    "utilisateur" : utilisateur,
                    "mots_de_passe" : mdp_hash,
                    "role" : "user"
                })

                db["user"].insert_one(new_user)
                session['user'] = utilisateur
                session['role'] = "user"
                return redirect("/")
            else :
                return render_template('front/register.html', erreur = "les mots de passe ne corresponde pas")
    else :
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
        youtube_url = request.form.get("youtube_url", "").strip()

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
                'youtube_url': youtube_url,
                'n_inventaire' : N_inventaire,
                "likes" : 0,
                "liked_by" : []
            })
            return redirect("/")
        else: 
            return render_template("front/publish.html", erreur = 'Veuillez remplir tout les champs obligatoires svp')
    return render_template("front/publish.html")

@app.route("/post/like/<annonces_id>")
def like_post(annonces_id):
    if 'user' not in session:
        return redirect(url_for('register'))
    user = session['user']

    annonces = db['annonces'].find_one({"_id" : ObjectId(annonces_id)})

    if not annonces:
        return redirect(url_for("index"))

    if user in annonces.get("liked_by", []):
        db['annonces'].update_one({"_id" : ObjectId(annonces_id)},
                          {"$inc" : {"likes" : 1},
                           "$pull" : {"liked_by" : user}
                           })

    else : 
        db['annonces'].update_one({"_id" : ObjectId(annonces_id)},
                          {"$inc" : {"likes" : 1},
                           "$pull" : {"liked_by" : user}
                           })
    return redirect(url_for("index"))

    



###########ADMIN############

@app.route('/admin')
def admin():
    annonce_data = list(db['annonces'].find({}))
    user_data = list(db['user'].find({}))
    if 'user' in session and session['role'] == 'admin' :
        return render_template('back/back_accueil.html', annonce = annonce_data, user = user_data)
    else : 
        return render_template('index.html', erreur = "vous n'avez pas les droit", annonce = annonce_data, user = user_data)

@app.route('/admin/update_role/<user_id>')
def update_role(user_id):
    if 'user' in session and session['role'] == 'admin':
        new_role = request.form.get('role')

        db['user'].update_one({"_id" : ObjectId(user_id)}, {"$set" : {"role" : new_role}})

    return redirect(url_for('admin'))

@app.route('/admin/delete_user/<user_id>')
def delete_user(user_id):
    if 'user' in session and session['role'] == 'admin':
        db['user'].delete_one({"_id" : ObjectId(user_id)})
    return redirect(url_for('admin'))

@app.route('/erreur404')
def error_404():
    return render_template("front/erreur_404.html"), 404

@app.errorhandler(404)
def page_not_found(error):
    return render_template('front/erreur_404.html'),404


if __name__ == "__main__":
    app.run(host ='0.0.0.0', port=int(os.environ.get("PORT", 5000)))