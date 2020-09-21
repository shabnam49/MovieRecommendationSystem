from flask import Flask, redirect, url_for, request, render_template
import flask
from neo4j import GraphDatabase
import flask_login

app = Flask(__name__)
app.secret_key = 'super secret string'
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

class DriverClass:
   def __init__(self, uri, user, password):
      self._driver = GraphDatabase.driver(uri, auth=(user, password))

   def close(self):
      self._driver.close()

   def suggestion(self,tx,name):
      l = []
      for record in tx.run('''match (suggested:User{username:$n})-[:FRIEND_OF*1..4]->(m)-[:FOLLOWS]->(a)-[:ACTED_IN]->(movie) with collect({title:movie.title,photo:movie.photo}) as rows
      match (suggested:User{username:$n})-[:FRIEND_OF*1..4]->(m)-[:LIKES]->(movie) with rows+collect({title:movie.title,photo:movie.photo}) as allrows unwind allrows as row  with row.title as title, row.photo as photo
      return title,photo,count(*) as c order by c desc''', n=name):
         movie={'title':record["title"],'img':record["photo"]}
         l.append(movie)
      return l

   def marketBasketAnalysis(self,tx,name):
      l = []
      for record in tx.run('''match(u:User{username:$n})-[:LIKES]->(m)<-[:LIKES]-(v) where u.username<>v.username
                            with m,count(*) as c
                            match (n)<-[:LIKES]-(v)-[:LIKES]->(m) where v.username<>$n
                            with n,m,count(*)*1.0/c as c2
                            where c2 >= 0.5
                            return distinct n.title as title,n.photo as photo''', n=name):
         movie={'title':record["title"],'img':record["photo"]}
         l.append(movie)
      return l

   def getAllMovies(self,tx):
      l = []
      for record in tx.run('match(m:Movie) return m.title'):
         l.append(record['m.title'])
      return l

   def coldStart(self,tx):
      l = []
      for record in tx.run('match(m:Movie) return m.title,m.photo'):
         movie={'title':record["m.title"],'img':record["m.photo"]}
         l.append(movie)
      return l

   def getAllActors(self,tx):
      l = []
      for record in tx.run('match(m:Person) return m.name'):
         l.append(record['m.name'])
      return l

   def create(self,tx,name,age,username,password):
      l = []
      for record in tx.run("create (harshal:User{name:$n,age:$a,username:$u,password:$p}) ", n=name,a=age,u=username,p=password):
         print(record)
         name="<p>"+str(record["name"])+"<span style='color:red'>"+str(record["title"])+"</p>"+"<img src='"+str(record["photo"])+"' alt='"+str(record["title"])+"' style='width:200px;'/>"
         l.append(name)
      return l

   def likemovie(self,tx,name,movie):
      l = []
      for record in tx.run("match (u:User{username:$n}) match(n:Movie{title:$m}) merge (u)-[:LIKES]->(n) return u,n", n=name,m=movie):
         print(record)
         #name="<p>"+str(record["name"])+"<span style='color:red'>"+str(record["title"])+"</p>"+"<img src='"+str(record["photo"])+"' alt='"+str(record["title"])+"' style='width:200px;'/>"
         #l.append(name)
      return l

   def followactor(self,tx,name,actor):
      l = []
      for record in tx.run("match (u:User{username:$n}) match(n:Person{name:$m}) merge (u)-[:FOLLOWS]->(n)", n=name,m=actor):
         print(record)
         #name="<p>"+str(record["name"])+"<span style='color:red'>"+str(record["title"])+"</p>"+"<img src='"+str(record["photo"])+"' alt='"+str(record["title"])+"' style='width:200px;'/>"
         #l.append(name)
      return l

   def getAllUsers(self, tx):
      l = {}
      for record in tx.run("match (u:User)return u.username, u.password"):
         l[record['u.username']] = {'password':record['u.password']}
      return l

   def getAllUsers2(self, tx):
      l = []
      for record in tx.run("match (u:User)return u.username"):
         l.append(record['u.username'])
      return l

   def getAllGenre(self, tx):
      l = []
      for record in tx.run('match(m:Movie) unwind m.genre as g return distinct g'):
         l.append(record['g'])
      return l
   def getGenre(self, tx,genre):
      l = []
      for record in tx.run('match(m:Movie) where $g in m.genre return m.title,m.photo',g=genre):
         movie={'title':record["m.title"],'img':record["m.photo"]}
         l.append(movie)
      return l

   def make_friend(self,tx,name,friend):
      l = []
      for record in tx.run("match (a:User{username:$n}) match(b:User{username:$f}) merge (a)-[:FRIEND_OF]->(b)", n=name,f=friend):
         print(record)
         name="<p>"+str(record["name"])+"<span style='color:red'>"+str(record["title"])+"</p>"+"<img src='"+str(record["photo"])+"' alt='"+str(record["title"])+"' style='width:200px;'/>"
         l.append(name)
      for record in tx.run("match (a:User{username:$n}) match(b:User{username:$f}) merge (a)<-[:FRIEND_OF]-(b)", n=name,f=friend):
         print(record)
         name="<p>"+str(record["name"])+"<span style='color:red'>"+str(record["title"])+"</p>"+"<img src='"+str(record["photo"])+"' alt='"+str(record["title"])+"' style='width:200px;'/>"
         l.append(name)
      return l

   def call_suggestion(self,n):
      with self._driver.session() as session:
         return session.read_transaction(self.suggestion,n)

   def call_marketBasketAnalysis(self,n):
      with self._driver.session() as session:
         return session.read_transaction(self.marketBasketAnalysis,n)

   def call_getAllUsers(self):
      with self._driver.session() as session:
         return session.read_transaction(self.getAllUsers)

   def call_followactor(self,n,a):
      with self._driver.session() as session:
         return session.read_transaction(self.followactor,n,a)

   def call_create(self,n,a,u,p):
      with self._driver.session() as session:
         return session.read_transaction(self.create,n,a,u,p)

   def call_friend(self,n,a):
      with self._driver.session() as session:
         return session.read_transaction(self.make_friend,n,a)

   def call_coldStart(self):
    with self._driver.session() as session:
      return session.read_transaction(self.coldStart)

   def call_likemovie(self,n,a):
      with self._driver.session() as session:
         return session.read_transaction(self.likemovie,n,a)
   def call_getAllMovies(self):
    with self._driver.session() as session:
      return session.read_transaction(self.getAllMovies)
   def call_getAllActors(self):
    with self._driver.session() as session:
      return session.read_transaction(self.getAllActors)
   def call_getAllUsers2(self):
    with self._driver.session() as session:
      return session.read_transaction(self.getAllUsers2)
   def call_getAllGenre(self):
    with self._driver.session() as session:
      return session.read_transaction(self.getAllGenre)
   def call_getGenre(self,genre):
    with self._driver.session() as session:
      return session.read_transaction(self.getGenre,genre)

class User(flask_login.UserMixin):
   pass

F = DriverClass("bolt://localhost:7687","neo4j","harshal12")
users = F.call_getAllUsers()
print(users)
@login_manager.user_loader
def user_loader(email):
    # users = call_getuser('harshal patel')
    if email not in users:
        return

    user = User()
    user.id = email
    return user
@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')
    # users = call_getuser('harshal patel')
    if email not in users:
        return

    user = User()
    user.id = email

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[email]['password']

    return user

@app.route('/')
@flask_login.login_required
def index():
   D = DriverClass('bolt://localhost:7687',"neo4j",'harshal12')
   m = D.call_getAllMovies()
   a = D.call_getAllActors()
   u = D.call_getAllUsers2()
   g = D.call_getAllGenre()
   return render_template('form.html',name=flask_login.current_user.get_id(),movies = m,actors = a,users=u,genre=g)

@app.route('/genre',methods=['POST'])
def genre():
   D = DriverClass("bolt://localhost:7687","neo4j","harshal12")
   if flask.request.method =="POST":
     genre = request.form['Genre']
     x = D.call_getGenre(genre)
     return render_template('suggestion_page.html',movies=x,al=x)

@app.route('/suggested',methods = ['POST', 'GET'])
@flask_login.login_required
def suggestMovies():
   D = DriverClass("bolt://localhost:7687","neo4j","harshal12")
   user = flask_login.current_user.get_id()
   alsolike = D.call_marketBasketAnalysis(user)
   x = D.call_suggestion(user)
   if len(x) < 1:
     x = D.call_coldStart()
   print(x)
   return render_template('suggestion_page.html',movies=x,al=alsolike)

@app.route('/create',methods = ['POST','GET'])
def createUser():
   global users
   D = DriverClass("bolt://localhost:7687","neo4j","harshal12")
   if flask.request.method == 'POST':
      firstname = request.form['firstname']
      age = request.form['Age']
      password = request.form['password']
      username = request.form['username']
      x = D.call_create(firstname,age,username,password)
      users = D.call_getAllUsers()
      return redirect("/")
   else:
      return render_template('signup.html')

@app.route('/likemovie',methods = ['POST'])
@flask_login.login_required
def likeMovie():
   D = DriverClass("bolt://localhost:7687","neo4j","harshal12")
   if request.method == 'POST':
      firstname = flask_login.current_user.get_id()
      movie = request.form['LikeMovie']
      x = D.call_likemovie(firstname,movie)
      return redirect("/")

@app.route('/followactor',methods = ['POST'])
@flask_login.login_required
def followActor():
   D = DriverClass("bolt://localhost:7687","neo4j","harshal12")
   if request.method == 'POST':
      firstname = flask_login.current_user.get_id()
      an = request.form['actorName']
      x = D.call_followactor(firstname,an)
      return redirect("/")

@app.route('/friend',methods = ['POST'])
@flask_login.login_required
def makeFriend():
   D = DriverClass("bolt://localhost:7687","neo4j","harshal12")
   if request.method == 'POST':
      firstname = flask_login.current_user.get_id()
      friend = request.form['friend']
      x = D.call_friend(firstname,friend)
      return redirect("/")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return render_template('login.html')

    email = flask.request.form['email']
    if flask.request.form['password'] == users[email]['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return redirect("/")

    return redirect("/")

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return redirect("/")

@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect("/login")

if __name__ == '__main__':
   app.run(debug = True)