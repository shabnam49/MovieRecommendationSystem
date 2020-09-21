import flask_login,flask
import flaskforminput as f
app = flask.Flask(__name__)
app.secret_key = 'super secret string'
login_manager = flask_login.LoginManager()

login_manager.init_app(app)
# users = {'foo@bar.tld': {'password': 'secret'},'abc':{'password':'1234'}}
# users['xyz']={'password':'222'}
D = f.DriverClass("bolt://localhost:7687","neo4j","harshal12")
users = D.call_getAllUsers()
class User(flask_login.UserMixin):
    pass

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




@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
               <form action='login' method='POST'>
                <input type='text' name='email' id='email' placeholder='email'/>
                <input type='password' name='password' id='password' placeholder='password'/>
                <input type='submit' name='submit'/>
               </form>
               '''

    email = flask.request.form['email']
    if flask.request.form['password'] == users[email]['password']:
        user = User()
        user.id = email
        flask_login.login_user(user)
        return flask.redirect(flask.url_for('protected'))

    return 'Bad login'


@app.route('/protected')
@flask_login.login_required
def protected():
    return 'Logged in as: ' + flask_login.current_user.id




@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'



@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'



if __name__ == "__main__":
    app.run(debug=True)