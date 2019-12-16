from flask import Flask , render_template,flash,request,redirect,url_for,session,jsonify
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,SelectField
from passlib.hash import sha256_crypt

from flask_pymongo import PyMongo
from functools import wraps
from datetime import datetime,timedelta






app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/PsMonitor"
mongo = PyMongo(app)

# decorator to check login session
def is_loged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized Please login','danger')
            return  redirect(url_for('login'))
    return wrap

# Registration Form creation
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password',[
        validators.data_required(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm= PasswordField('Confirm Password')



#Route to Registration form

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method=='POST' and form.validate():
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(str(form.password.data))
        userexist=mongo.db.users.find_one({'ID':name})
        if userexist:
            flash(' User ' + name+' already existed  ', 'danger')

        else:
            mongo.db.users.insert({'ID':name,'Email':email,'Name':username,'Password':password})


            flash(' You are now registered .Your Username is: '+name,'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username_login=request.form['username']
        password_candidate=request.form['password']


        results=mongo.db.users.find_one({'ID':username_login})
        if results :
            password=results['Password']
            if sha256_crypt.verify(password_candidate,password):
                session['logged_in']=True
                session['username']=username_login

                flash('You are successfully logged in', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error)
        else:
            error='User is not registered'
            return render_template('login.html',error=error)

    return render_template('login.html')

@app.route('/',methods=['GET','POST'])
def startpage():
    if request.method == 'POST':
        username_login = request.form['username']
        password_candidate = request.form['password']

        results = mongo.db.users.find_one({'ID': username_login})
        if results:
            password = results['Password']
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username_login

                flash('You are successfully logged in', 'success')
                return redirect(url_for('index'))
            else:
                error = 'Invalid password'
                return render_template('login.html', error=error)
        else:
            error = 'User is not registered'
            return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out','success')
    return redirect(url_for('login'))

@app.route('/index')
@ is_loged_in
def index():
    try:
        data = mongo.db.Agents.find()

    except:
        data={'Hostname':'No DB Connection','UpTime':'','CPU':''}
   # print(type(data))
   # data=[]
   # for result in results:
     #   data.append({'id':str(result['_id']),'HostName':result['HostName'],'UpTime':result['UpTime'],'CPU':result['CPU']})
    #data=jsonify(data)


    return render_template('index.html',data=data)

@app.route('/ServerGroup')
@ is_loged_in
def ServerGroup():
    data=mongo.db.ServerGroup.find()
    return render_template('ServerGroup.html',data=data)

@app.route('/addsrvpool')
@ is_loged_in
def addsrvpool():
    myhosts=[]
    hosts=mongo.db.Agents.find()
    for host in hosts:
        host=host['HostName']
        myhosts.append(host)

    return render_template('addsrvpool.html',hosts=myhosts)

@app.route('/agents')
@ is_loged_in
def agents():
    agents = []
    all_agents = mongo.db.Agents.find()
    now = datetime.now()
    for agent in all_agents:
        agentname = agent['HostName']

        agent_enabled = agent["Enabled"]

        agent_eff_date=agent["Effective_date"]
        agent_eff_time=agent["Effective_time"]
        datetime_str=agent_eff_date+ " "+agent_eff_time
        last_updt_time=datetime.strptime(datetime_str,"%m/%d/%Y %H:%M:%S")

        #if agent_eff_date==now.strftime("%m/%d/%Y") and agent_eff_time >=now.strftime("%H:%M:%S")-timedelta(minutes=2):

        if last_updt_time >= now - timedelta(seconds=15):
             agentstatus="Running"
        else:
            agentstatus = "Not Running"

        agentinfo=[agentname,agentstatus,agent_enabled]

        agents.append(agentinfo)
    return render_template('agents.html',agents=agents)

class AgentsForm(Form):
    AgentName = StringField('Name', [validators.Length(min=1, max=50)])
    LastUpdate = StringField('Last Update', [validators.Length(min=4, max=25)])
    Enabled= SelectField('Enabled', choices = [('YES','Enable'),('NO','Disable')])

@app.route('/editagents/<string:id>',methods=['GET','POST'])
@ is_loged_in
def editagents(id):
    result = mongo.db.Agents.find_one({'HostName': id})
    print(result)
    form=AgentsForm(request.form)

    form.AgentName.data=result['HostName']
    form.LastUpdate.data=result['Effective_date']+" "+result['Effective_time']
    form.Enabled.data=result['Enabled']
    if request.method=='POST':
        upd_enabled = request.form['Enabled']


        print("Value of Enabled is "+upd_enabled)
        searchquery={"HostName":id}
        updatequery={"$set": {"Enabled": upd_enabled}}
        x= mongo.db.Agents.update_one(searchquery,updatequery)
        print('updated data is ', x)
        flash(' Agent has been updated ' , 'success')



        return redirect(url_for('agents'))
    return render_template('editagents.html',form=form)







if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)