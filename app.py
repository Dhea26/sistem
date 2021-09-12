
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from werkzeug.datastructures import Headers
from werkzeug.security import generate_password_hash, check_password_hash
import firebase_admin
from firebase_admin import credentials, firestore
from functools import wraps
import requests
from requests.structures import CaseInsensitiveDict

cred = credentials.Certificate('firebase.json')
firebase_admin.initialize_app(cred)

db = firestore.client() #fungsi untuk memanggil firestore


app = Flask(__name__)  #memanggil nama folder flask di dalam file flask
app.secret_key = 'dhea'

#untuk memudahkan dalam memberikan session
#session adalah tidak bisa mengakses lewat url, @login_required = disimpan untuk dibagian mana kita harus login
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' in session:
            return f(*args, **kwargs)
        else:
            flash("Anda harus login", "danger")
            return redirect(url_for('login'))
    return wrapper
def send_wa(m, p):
    api = "3c0098a183f0ae14220be237a4862f2e959e2ca1"
    url = "https://starsender.online/api/sendText"

    data = {
        "tujuan":p,
        "message": m
    }
    
    headers = CaseInsensitiveDict()
    headers["apikey"] = api

    res = requests.post(url, json=data, headers=headers)
    return res.text

    

@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/tambah_data') 
# def tambah_data():
#     data = {
#         "username": "dhea",
#         "email": "dhea@gmail.com",
#         "jurusan": "TIK"
#     }

#     db.collection("users").document().set(data)

#     return "berhasil"

@app.route('/login', methods=["GET", "POST"])
def login():
    #menentukan method
    if request.method == "POST":
        #ambil data
        data = {
            "email": request.form["email"],
            "password": request.form["password"]
        }
        #lakukan pengecekan
        users = db.collection("users").where("email", "==", data["email"]).stream()
        user = {}

        for us in users:
            user = us.to_dict()

        if user:
            if check_password_hash(user["password"], data["password"]):
                session["user"] = user
                flash("Anda Berhasil Login", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Maaf Password Anda Salah", "danger") 
                return redirect(url_for('login'))
        else:
            flash("Email Belum Terdaftar", "danger") 
            return redirect(url_for('login'))
    if 'user' in session:
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash("anda belum login", "danger")
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/mahasiswa')
@login_required
def mahasiswa():
    #panggil data di database
    #buatkan variabel untuk menyimpan data
    #lakukan pengulangan terhadap data
    #simpan data di yang sudah di ulang di dlm sebuah array
    maba = db.collection("mahasiswa").stream() #untuk memanggil semua data
    mb = []

    for mhs in maba:
        m = mhs.to_dict()
        m["id"] = mhs.id
        mb.append(m) #append untuk memasukkan data, jadi data m masukkan datanya ke mb
    return render_template('template.html', data=mb)
    # return jsonify()

@app.route('/mahasiswa/tambah', methods=["GET", "POST"])
@login_required
def tambah_mhs():
    if request.method == 'POST':
        data = {
            "nama": request.form["nama"],
            "email": request.form["email"],
            "nim": request.form["nim"],
            "jurusan": request.form["jurusan"]
            
        }
        #.set()= untuk menambahkan data
        db.collection("mahasiswa").document().set(data) #document() dikosongkan untuk diberikan id/ primary key tersendiri
        flash("Data Berhasil Ditambah", "success") 
        return redirect(url_for('mahasiswa')) #url for ini akan dikembalikan ke @app.routenya
    return render_template('add_mhs.html')

@app.route('/mahasiswa/delete/<uid>') #tanda siku itu artinya tolong sebut itu sebagai uid
def delete_mhs(uid):
    db.collection("mahasiswa").document(uid).delete()
    flash("Data Berhasil dihapus", "success") 
    return redirect(url_for('mahasiswa'))

@app.route('/mahasiswa/lihat/<uid>')
def lihat_mhs(uid):
    #memanggil datanya didatabase
    user = db.collection("mahasiswa").document(uid).get().to_dict()
    return render_template('lihat_mhs.html', user=user)

@app.route('/mahasiswa/ubah/<uid>', methods=["GET", "POST"])
def ubah_mhs(uid):
    #menentukan method
    if request.method == "POST":
        data = {
            "nama": request.form["nama"],
            "email": request.form["email"],
            "nim": request.form["nim"],
            "jurusan": request.form["jurusan"]
            
        }

        db.collection('mahasiswa').document(uid).set(data, merge=True)
        flash("Data Berhasil Diubah", "success")
        return redirect(url_for('mahasiswa'))
    #menerima data baru
    #set di database

    #mengambil data
    user = db.collection('mahasiswa').document(uid).get().to_dict()
    user['id'] = uid
    #render template
     
    return render_template('ubah_mhs.html', user=user)
    



@app.route('/register', methods=["GET", "POST"])
def register():
    if  request.method == "POST":
        data = {
           "nama": request.form["nama"],
            "email": request.form["email"],
            "no_hp": request.form["no_hp"]
        }
        
        users = db.collection("users").where('email', '==', data['email']).stream()
        user = {}
        for us in users:
            user = us
        if user:
            flash("email sudah terdaftar", "danger")
            return redirect(url_for('register'))
        data['password'] = generate_password_hash(request.form['password'], 'sha256')
        db.collection("users").document().set(data)
        send_wa(f"Halo *{data['nama']}* Ada yang Bisa Kami Bantu??", data["no_hp"])
        return redirect(url_for('login'))
    return render_template('register.html')
    
#     pengguna = db.collection("users").stream() #untuk memanggil semua data
#     mb = []

#     for usr in pengguna:
#         m =usr.to_dict()
#         m["id"] =usr.id
#         mb.append(m) #append untuk memasukkan data, jadi data m masukkan datanya ke mb
#     return render_template('register.html', data=mb)  
# # 1. Tambahkan methods get dan post, 
# # 2. 

# @app.route('/register/tambah', methods=["GET", "POST"])
# def tambah_usr():
#     if  request.method == "POST":
#         data = {
#            "nama": request.form["nama"],
#             "email": request.form["email"],
#             "no_hp": request.form["no_hp"]
#         }
        
#         users = db.collection("users").where('email', '==', data['email'].stream())
#         user = {}
#         for us in users:
#             user = us
#         if user:
#             flash("email sudah terdaftar", "danger")
#             return redirect(url_for('register'))
#         data['password'] = generate_password_hash(request.form['password'], 'sha256')
#         db.collection("users").document().set(data)
#         flash("Data Berhasil Ditambah", "success")
#         return redirect(url_for('register'))
#     return render_template('add_register.html')

# @app.route('/register/ubah/<uid>', methods=["GET", "POST"])
# def ubah_usr(uid):
#     if request.method == "POST":
#         data = {
#             "nama": request.form["nama"],
#             "email": request.form["email"],
#             "password": request.form["password"],
#             "no_hp": request.form["no_hp"]
#         }
#         db.collection("users").document(uid).set(data, merge=True)
#         return redirect(url_for('register'))
#     #menerima data baru
#     #set di database

#     #mengambil data
#     akun = db.collection("users").document(uid).get().to_dict()
#     akun["id"] = uid
#     #render template
#     flash("Data Berhasil Diubah", "success")
#     return render_template('ubah_usr.html', akun=akun)
    
# @app.route('/register/hapus/<uid>')
# def hapus_usr(uid):
#     db.collection("users").document(uid).delete()
#     flash("Data Berhasil Dihapus", "success")
#     return redirect(url_for('register'))

# @app.route('/register/lihat/<uid>')
# def lihat_usr(uid):
#     #memanggil datanya didatabase
#     user = db.collection("users").document(uid).get().to_dict()
#     return render_template('lihat_usr.html', user=user)


if __name__ == "__main__":  #untuk menjalankan flasknya
    app.run(debug=True)