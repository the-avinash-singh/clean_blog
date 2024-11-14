from flask import Flask, render_template, request,session,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from flask_mail import Mail
from werkzeug.utils import secure_filename
import os
import math

local_server=True

with open('templates/config.json','r') as c:
    params=json.load(c)['params']
app=Flask(__name__)
app.secret_key=params['secret_key']

app.config["upload_location"]=params["upload_location"]
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'ssl': {'ssl_disabled': True}
    }
} 
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail=Mail(app)

db = SQLAlchemy(app)

class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=False, nullable=False)
    date = db.Column(db.String(12))
    mes = db.Column(db.String(120), nullable=False)

class Posts(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    author=db.Column(db.String(80), unique=False, nullable=False)
    title=db.Column(db.String(80), unique=False, nullable=False)
    subtitle=db.Column(db.String(80), unique=False, nullable=False)
    slug=db.Column(db.String(30), unique=True, nullable=False)
    content=db.Column(db.String(120), unique=False, nullable=False)
    date=db.Column(db.String(20), unique=False, nullable=True)
    img_url=db.Column(db.String(30), unique=False, nullable=True)

@app.route("/")
def home():
    posts=Posts.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_post']))
    print(last)
    page=request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_post']):(page-1)*int(params['no_of_post'])+int(params['no_of_post'])]

    if(page==1):
        prev="#"
        next="/?page="+str(page+1)
    elif(page==last):
        prev="/?page="+str(page-1)
        next="#"
    else:
        prev="/?page="+str(page-1)
        next="/?page="+str(page+1)
    
    return render_template('index.html',posts=posts,prev=prev,next=next)

@app.route('/post/<string:post_slug>',methods=["GET"])
def post_route(post_slug):
    post=Posts.query.filter_by(slug=post_slug).first()
    return render_template('post.html',post=post)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if 'uname' in session and session['uname'] == params['admin_user']:
        posts = Posts.query.all()
        return render_template('dashboard.html', posts=posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('pass')
        if username == params['admin_user'] and password == params['password']:
            session['uname'] = username
            posts = Posts.query.all()
            return render_template('dashboard.html', posts=posts)
        else:
            # Invalid credentials; return to login page
            return render_template('login.html', params=params)

    # If the request method is GET and user is not in session, show login page
    return render_template('login.html', params=params)

@app.route('/edit/<string:id>',methods=["GET","POST"])
def edit(id):
    if 'uname' in session and session['uname'] == params['admin_user']:
        if request.method=='POST':
            title=request.form.get('title')
            subtitle=request.form.get('subtitle')
            slug=request.form.get('slug')
            author=request.form.get('author')
            content=request.form.get('content')
            img_url=request.form.get('img_url')

            if id=='0':
                postData=Posts(title=title,subtitle=subtitle,slug=slug,author=author,content=content,img_url=img_url,date=datetime.now())
                db.session.add(postData)
                db.session.commit()
            else:
                post=Posts.query.filter_by(id=id).first()
                post.title=title
                post.subtitle=subtitle
                post.slug=slug
                post.author=author
                post.content=content
                post.img_url=img_url
                post.date=datetime.now()
                db.session.commit()
                return redirect('/edit/'+id)
        post=Posts.query.filter_by(id=id).first()
        return render_template('edit.html',post=post,id=id)

@app.route('/delete/<string:id>')
def delete(id):
    if 'uname' in session and session['uname'] == params['admin_user']:
        post=Posts.query.filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
        return redirect("/dashboard")

@app.route('/uploader',methods=["GET","POST"])
def uploader():
    if 'uname' in session and session['uname'] == params['admin_user']:
        if request.method=='POST':
            file=request.files['file1']
            file.save(os.path.join(app.config["upload_location"],secure_filename(file.filename)))
            return "Uploded Successfully"
        
@app.route('/logout')
def logout():
    session.pop("uname")
    return redirect("/dashboard")

@app.route("/contact",methods=['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        name=request.form.get('name')
        email=request.form.get('email')
        mes=request.form.get('mes')
        entry=Contacts(name=name,email=email,mes=mes, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('message from site',
                          sender=email,recipients=[params['gmail-user']],
                          body='name of user'+name+". \n"+mes
                          )
    return render_template('contact.html')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=True)