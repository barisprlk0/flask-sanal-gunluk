from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,PasswordField,validators,TextAreaField
from passlib.hash import sha256_crypt
import time
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu İşlem İçin Giriş Yapmalısın","warning")
            return redirect(url_for("login"))
    return decorated_function




def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_Login" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu İşlem İçin Giriş Yapmalısın","warning")
            return redirect(url_for("login"))
    return decorated_function


class DayForm(Form):                                                            
    title=StringField("Başlık",validators=[validators.DataRequired(),validators.Length(min=5,max=10,message="SREA")])
    content=TextAreaField("İçerik",validators=[validators.DataRequired()])


class RegisterForm(Form):
    name=StringField("İsim",validators=[validators.DataRequired(message="Bu Alan Zorunludur")])
    username=StringField("Kullanıcı Adı",validators=[validators.DataRequired(message="Bu Alan Zorunludur")])
    email=StringField("E-Posta",validators=[validators.Email(message="Bu Bir E-Posta Değil")])
    password=PasswordField("Şifre",validators=[validators.DataRequired(message="Bu Alan Zorunludur"),validators.EqualTo(fieldname="confirm",message="Şifreler Uyuşmuyor")])
    confirm=PasswordField("Yeniden",validators=[validators.DataRequired(message="Bu Alan Zorunludur")])




class LoginForm(Form):
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Şifre")

class AdminForm(Form):
    username=StringField("Kullanıcı Adı")
    email=StringField("Email")
    password=StringField("Şifre")






app=Flask(__name__) 

app.secret_key="dayblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"] = "diary"
app.config["MYSQL_CURSORCLASS"]="DictCursor"

myqsql=MySQL(app)




#ana sayfa
@app.route("/")
def index():
    
    return render_template("index.html")
    
#kayıt ol
@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method=="POST" and form.validate():
        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)   
        
        cursor=myqsql.connection.cursor()
        sorgu="insert into users (name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        myqsql.connection.commit()
        cursor.close()
        flash("Başarıyla Kayıt Oldunuz","success")
        return redirect(url_for("login"))

    else:   
        return render_template("register.html",form=form)

#Giriş Yap
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    
    if request.method == "POST":
        username=form.username.data
        entered_password=form.password.data


        cursor=myqsql.connection.cursor()
        sorgu="select * from users where username = %s"
        result=cursor.execute(sorgu,(username,))
        if result > 0:
            data=cursor.fetchone()
            real_password=data["password"]
            if sha256_crypt.verify(entered_password,real_password):
                flash("Başarıyla giriş yaptınız","success")

                session["logged_in"] = True
                session ["username"] = username

                return redirect(url_for("index"))
            else:
                flash("Şifreyi Yanlış Girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle Bir Kullanıcı Yok","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form=form)



#Admin 
@app.route("/admin",methods=["GET","POST"])
def adminLogin():
    form=AdminForm(request.form)
    if request.method == "POST":
        username=form.username.data
        entered_password=form.password.data

        cursor=myqsql.connection.cursor()
        sorgu="select * from admin_panel where username = %s"
        result=cursor.execute(sorgu,(username,))
        if result > 0:
            data=cursor.fetchone()
            real_password=data["password"]
            if entered_password==real_password:
                flash("Başarıyla Giriş Yaptınız","success")
                
                session["admin_Login"] = True
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Şifre Yanlış","danger")
                return redirect(url_for("adminLogin"))
        else:
            flash("Böyle Bir Kullanıcı Yok","danger")
            return redirect(url_for("adminLogin"))
    return render_template("adminlogin.html",form=form)



#Gün Ekle
@app.route("/adday",methods=["GET","POST"])
def adday():
    form=DayForm(request.form)
    if request.method == "POST" and form.validate:
        title=form.title.data
        content=form.content.data

        cursor=myqsql.connection.cursor()
        sorgu="insert into days (title,author,content) Values(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        myqsql.connection.commit()

        flash("Gün Başarıyla Kaydedildi","success")
        return redirect(url_for("dashboard"))
    return render_template("adday.html",form=form)









#Çıkış Yap
@app.route("/logout")
def logout():
    session.clear()
    time.sleep(0.5)
    return redirect(url_for("index"))

#Kontrol Paneli
@app.route("/dashboard")
def dashboard():
    cursor=myqsql.connection.cursor()
    sorgu="select * from days where author=%s"
    result=cursor.execute(sorgu,(session["username"],))

    if result > 0:
        days=cursor.fetchall()
        return render_template("dashboard.html",days=days)
    else:
        return render_template("dashboard.html")

@app.route("/dashboard/admin")
@admin_required
def admin_dashboard():
    cursor=myqsql.connection.cursor()
    sorgu="select * from days"
    result=cursor.execute(sorgu)

    if result>0:
        days=cursor.fetchall()
        return render_template("dashboard.html",days=days)
    else:
        return render_template("dashboard.html")  
#detay
@app.route("/days/<string:id>")
def detail(id):
    cursor=myqsql.connection.cursor()
    sorgu = "select * from days where id = %s"
    result=cursor.execute(sorgu,(id,))
    if result > 0:
        day=cursor.fetchone()
        return render_template("detail.html",day=day)

    else:

        return render_template("detail.html")

#silme
@app.route("/delete/<string:id>")
@login_required

def delete(id):
    cursor=myqsql.connection.cursor()
    sorgu="select * from days where author = %s and id = %s"
    result=cursor.execute(sorgu,(session["username"],id))
    if result > 0 :
        sorgu2="delete from days where id = %s"
        cursor.execute(sorgu2,(id,))
        myqsql.connection.commit()

        return redirect(url_for("dashboard"))
    elif admin_required:
        sorgu2="delete from days where id = %s"
        cursor.execute(sorgu2,(id,))
        myqsql.connection.commit()

        return redirect(url_for("admin_dashboard"))
    else:
        flash("Bu İşlem İçin Yetkiniz Yok","danger")
        return redirect(url_for("dashboard"))


#Amaç
@app.route("/about")
def about():

    return render_template("about.html")   

#Günler
@app.route("/days")
def days():
    cursor=myqsql.connection.cursor()
    sorgu="select * from days"
    result=cursor.execute(sorgu)
    if result > 0:
        
        days=cursor.fetchall()
        return render_template("days.html",days=days)
    else:
        return render_template("days.html")


if __name__ == "__main__":
    app.run(debug=True)
