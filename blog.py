from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps

#Kullanıcı Giriş Decorator kontrolü
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görmek için giriş yapın...","danger")
            return redirect(url_for("login"))
    return decorated_function

#Kullanıcı kayıt formu 
class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators=[validators.Length(min=4,max=25)])
    username = StringField("Kullanıcı Adı",validators=[validators.Length(min=5,max=35)])
    email = StringField("Email Adresi",validators=[validators.Email(message = "Lütfen Geçerli Bir Email Adresi Girin...")])
    password = PasswordField("Parola:",validators=[
        validators.DataRequired(message="Lütfen Bir Parola Belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Parolanız Uyuşmuyor")
    ])
    confirm = PasswordField("Parola Doğrula")

#Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")

#Makale Formu
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content = TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])

app = Flask(__name__) #Flask objesi oluşturuldu
app.secret_key = "sblog" #Session anahtarı oluşturuldu. Flash kullanımı için gereklidir.
#Notları htmlden alamadığımdan buraya yazacağım.
#HTML de miras alma mantığı da {% extends "layout.html" %} komutu ile çalışıyor.
#HTML de blok oluşturmak için {% block content %} {% endblock %} komutları kullanılıyor. Ayrıca bloklar başlık değiştirmek için kullanıyor yani miras sonrası
#Navbar yani yukarıda görüntülenen kısmı navbar sitesinden çektik. Navbar sitesi: https://getbootstrap.com/docs/4.0/components/navbar/
#Navbarı kendi projemize eklemek için layout.html dosyasına ekledik.({% include "includes/navbar.html" %}) Kodunu kullandık
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "sblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
#Flask MySQL bağlantısı yapıldı. Host gibi içeriklere sözlükten ulaşabilirsin.


@app.route('/') #decorator
def index(): #view function (Görüntülenen değer)
    return render_template('index.html') 


#Makaleler sayfası
@app.route('/articles') #decorator
def articles ():
    cursor = mysql.connection.cursor() #Veritabanı bağlantısı oluşturuldu
    sorgu = "Select * from articles" #Tüm makaleleri çeker
    result = cursor.execute(sorgu) # Sorguyu çalıştırır ve verileri çeker
    if result > 0:
        articles = cursor.fetchall() #Verileri çeker
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")


#Kayıt olma
@app.route("/register",methods=["GET","POST"]) #GET ve POST metotları ile çalışacak(request)
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate(): #Eğer request post ve form doğru doldurulmuş ise işlem çalışır
        name = form.name.data #Formdan gelen verileri alır
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data) #Parolayı şifreler

        cursor = mysql.connection.cursor() #Veritabanı bağlantısı oluşturuldu

        sorgu = "Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)" #Sorgu oluşturuldu Values ile verileri ekler

        cursor.execute(sorgu,(name,email,username,password)) #Verileri valuese gönderir
        mysql.connection.commit()

        cursor.close()
        flash("Başarıyla Kayıt Oldunuz...","success")

        return redirect(url_for("login")) #Eğer form doğruysa index sayfasına yönlendirir
    else:
        return render_template("register.html", form=form) #Formu register.html dosyasına gönderir

#Login işlemi
@app.route("/login",methods = ["GET" , "POST"]) #GET ve POST metotları ile çalışacak(request)
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "Select * from users where username = %s" #Kullanıcı adı veritabanında var mı kontrol eder
        result =cursor.execute(sorgu,(username,)) #Kullanıcı adı veritabanında var mı kontrol eder
        if result > 0:
            data = cursor.fetchone() #Veritabanından verileri çeker
            real_password = data["password"] #Veritabanındaki şifreyi alır
            if sha256_crypt.verify(password_entered,real_password): #Şifreler eşleşiyorsa
                flash("Başarıyla Giriş Yaptınız...","success")

                session["logged_in"] = True #Session açar ve giriş yapar
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz...","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))
    return render_template("login.html", form=form) #Formu login.html dosyasına gönderir

#Detay sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    
    sorgu = "Select * from articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article = article)
    else:
        return render_template("article.html")


#Logout işlemi
@app.route("/logout")
def logout():
    session.clear() #Sessionu temizler
    return redirect(url_for("index"))  #Index sayfasına yönlendirir  

#Makale (Dashboard) işlemi
@app.route("/dashboard")
@login_required #Login işlemi kontrolü
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s"
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

#Makale ekleme
@app.route("/addarticle", methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate(): #Eğer form doğru doldurulmuş ise işlem çalışır
        title = form.title.data #Formdan gelen verileri alır ve verileri sql e kaydetmeye yarayacak olan kısımdır
        content = form.content.data
        
        cursor = mysql.connection.cursor()
        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Eklendi...","success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form=form)

#Makale Güncelleme
@app.route("/edit/<string:id>",methods = ["GET","POST"])
@login_required #Login işlemi kontrol. Login olan adam güncelleyebilir
def update(id):
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"])) #Makaleyi sadece kendi yazdığı makale
        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok...","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form = form)
            
    else:
        #POST REQUEST KISMI
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        sorgu2 = "Update articles Set title = %s, content = %s where id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Makale Başarıyla Güncellendi...","success")
        return redirect(url_for("dashboard"))

#Makale Yorum Yapma
@app.route("/comment/<string:article_id>", methods=["GET", "POST"])
@login_required
def comment(article_id):
    if request.method == "POST":
        comment_content = request.form.get("comment")
        cursor = mysql.connection.cursor()
        sorgu = "Insert into comments(article_id, author, content) VALUES(%s, %s, %s)"
        cursor.execute(sorgu, (article_id, session["username"], comment_content))
        mysql.connection.commit()
        cursor.close()
        flash("Yorum başarıyla eklendi...", "success")
        return redirect(url_for("article", id=article_id))
    return render_template("comment.html")

    # Yorumları görüntüleme
    @app.route("/comments/<string:article_id>")
    def comments(article_id):
        cursor = mysql.connection.cursor()
        sorgu = "Select * from comments where article_id = %s"
        result = cursor.execute(sorgu, (article_id,))
        if result > 0:
            comments = cursor.fetchall()
            return render_template("comments.html", comments=comments, article_id=article_id)
        else:
            flash("Bu makaleye ait yorum bulunamadı...", "warning")
            return redirect(url_for("article", id=article_id))


#Makale Silme
@app.route("/delete/<string:id>")
@login_required #Login işlemi kontrol. Login olan adam silebilir
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author = %s and id = %s" #Makaleyi sadece kendi yazdığı makale
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2 = "Delete from articles where id = %s"
        cursor.execute(sorgu2,(id,)) #Sorguyu çalıştırır ve siler
        mysql.connection.commit()
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok...","danger")
        return redirect(url_for("index"))
    
#Arama URL
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET": #Eğer get request ise index sayfasına yönlendirir
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword") #Formdan gelen veriyi alır
        cursor = mysql.connection.cursor()
        sorgu = "Select * from articles where title like '%" + keyword + "%'"
        result = cursor.execute(sorgu)
        if result == 0:
            flash("Aranan kelimeye uygun makale bulunamadı...","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()
            return render_template("articles.html",articles = articles)

if __name__ == '__main__': #Bu dosya maini referans dönderir ve kodun terminalde çalıştırır
    app.run(debug=True) #Uygulamayı çalıştırır ve debug modunu açar(Debug modu= Kodu devamlı güncelleyerek hataları ayıklar)



