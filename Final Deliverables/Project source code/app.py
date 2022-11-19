from flask import Flask, render_template, request, redirect, url_for, session
import ibm_db
import re
from random import * 
from flask_mail import Mail, Message
app = Flask(__name__)
mail = Mail(app) # instantiate the mail class

# configuration of mail
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'nilavarasi2002@gmail.com'
app.config['MAIL_PASSWORD'] = 'ipergvvhzblqfnpd'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
otp = randint(000000,999999)

def test_predict_image_url():
    stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())

    req = service_pb2.PostModelOutputsRequest(
        model_id=GENERAL_MODEL_ID,
        inputs=[
            resources_pb2.Input(
                data=resources_pb2.Data(image=resources_pb2.Image(url=DOG_IMAGE_URL))
            )
        ],
    )

    response = post_model_outputs_and_maybe_allow_retries(stub, req, metadata=metadata())
    print(response)
    raise_on_failure(response)

    assert len(response.outputs[0].data.concepts) > 0
app.secret_key = 'a'
conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=ba99a9e6-d59e-4883-8fc0-d6a8c9f7a08f.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud;PORT=31321;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=pvw86690;PWD=zJNTZLGkY3yuoy3X",'','')
@app.route("/")
@app.route('/home')
def home():
   return render_template('index.html')
@app.route('/login', methods =['GET', 'POST'])
def login():
    global userid
    msg = ''
    if request.method == 'POST'and 'email' in request.form and 'password1' in request.form:
        email = request.form['email']
        password1 = request.form['password1']
        stmt = ibm_db.prepare(conn,'SELECT * FROM regi WHERE email = ? AND password1 = ?')
        ibm_db.bind_param(stmt,1,email)
        ibm_db.bind_param(stmt,2,password1)        
        ibm_db.execute(stmt)
        account = ibm_db.fetch_tuple(stmt)
        if account:
            session['id'] = account[0]
            userid =  account[0]
            session['email'] = account[1]
            msg = 'Logged in successfully !'
            return redirect(url_for('button'))
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg = msg)
@app.route('/button')
def button():
    return render_template('button.html')

@app.route('/limit', methods=["POST", "GET"])
def limit():

    if 'id' in session and 'email' in session:
        uid = session['id']
        exist = ibm_db.prepare(conn, 'SELECT uid, limit FROM limit WHERE uid = ?')
        ibm_db.bind_param(exist,1, session['id'])
        ibm_db.execute(exist)
        exist = ibm_db.fetch_tuple(exist)
        if request.method == "POST":
              print("Executing INSERT into LIMIT")
              uid = session['id']
              stmt = ""
              if exist == False:
                 print("Creating New")
                 stmt = ibm_db.prepare(conn, 'INSERT INTO limit (limit, uid) VALUES (?, ?)')
              else:
                print("Updating")
                stmt = ibm_db.prepare(conn, 'UPDATE limit SET \
                limit = ? \
                WHERE uid = ?')

                
              ibm_db.bind_param(stmt, 1,  request.form['limit'])    
              ibm_db.bind_param(stmt, 2,  uid)    
              ibm_db.execute(stmt)    
        
              return render_template('limit.html', status="Success", limit=int(request.form['limit']))
        else:
              if exist == False:
                return render_template('limit.html', limit=limit)
              else:
                return render_template('limit.html', limit=int(exist[1]))

    return 'Not Authed'

@app.route('/stat')
def stat():
    if 'id' in session:
        stmt = ibm_db.prepare(conn, 'SELECT expense, expensedate FROM expense WHERE uid = ?')
        ibm_db.bind_param(stmt,1,session['id'])
        ibm_db.execute(stmt)
        tb = ibm_db.fetch_tuple(stmt)

        months = {}
        while tb != False:
            sliced = tb[1].strftime("%b")
            if sliced in months:
                months[sliced] += tb[0]
            else:
                months[sliced] = tb[0]
            tb = ibm_db.fetch_tuple(stmt)

        return render_template('stat.html', data=months)
    return 'Not Authed Please Login'       
@app.route('/display')
def display():
    if 'id' in session :
        stmt = ibm_db.prepare(conn, 'SELECT amount, income, expense, expensedate, category FROM expense WHERE uid = ?')
        ibm_db.bind_param(stmt,1,session['id'])
        ibm_db.execute(stmt)

        tb = ibm_db.fetch_assoc(stmt)
        data = []
        while tb != False:
            data.append(tb)
            tb = ibm_db.fetch_assoc(stmt)
        print(data)
        return render_template('display.html',data=data)

    return 'Not Authed'    

@app.route('/wallet')
def wallet():
    return render_template('design.html')
@app.route('/income', methods =['GET', 'POST'])
def income():
    if 'id' in session and request.method == 'POST' and ('amount' in request.form) and ('income' in request.form) and ('expense' in request.form) and ('expensedate' in request.form )and ('category' in request.form):
            msg = ''
            uid = session['id']
            amount = request.form['amount']
            income = request.form['income']
            expense = request.form['expense']
            expensedate = request.form['expensedate']
            category = request.form['category']

            limit = ibm_db.prepare(conn, "SELECT limit from limit WHERE uid = ?")
            ibm_db.bind_param(limit, 1, session['id'])
            ibm_db.execute(limit)

            data = ibm_db.fetch_tuple(limit)
            sum = 0
            if data != False:
                data = data[0]
               
                all_expenses = ibm_db.prepare(conn, "SELECT expense from expense WHERE uid = ?")
                ibm_db.bind_param(all_expenses, 1, session['id'])
                ibm_db.execute(all_expenses)
                expense_data = ibm_db.fetch_tuple(all_expenses)

                while expense_data != False:
                    sum += int(expense_data[0])
                    expense_data = ibm_db.fetch_tuple(all_expenses)

            sum += int(expense)
            email = (session['email'] + '@gmail.com').lower()
            if sum >= data:
                #Limit Exceeded
                msg = Message('Limit Exceeded', sender='nilavarasi2002@gmail.com', recipients=[email])
                msg.body = "You Have Exceeded Your Expense Limit"
                mail.send(msg)
                msg = "Exceeded Limit"
                return render_template('add.html', a = msg)
                
            prep_stmt = ibm_db.prepare(conn, "INSERT INTO expense(uid,amount,income,expense,expensedate,category) VALUES (?, ?, ?, ?, ?, ?)")
            ibm_db.bind_param(prep_stmt, 1, uid)
            ibm_db.bind_param(prep_stmt, 2, amount)
            ibm_db.bind_param(prep_stmt, 3, income)
            ibm_db.bind_param(prep_stmt, 4, expense)
            ibm_db.bind_param(prep_stmt, 5, expensedate)
            ibm_db.bind_param(prep_stmt, 6, category)
            ibm_db.execute(prep_stmt)
            msg = 'You have successfully added !'
            return render_template('add.html', a = msg) 
    return render_template('add.html')
 
@app.route('/register', methods =['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST':
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password1 = request.form['password1']
        cpassword = request.form['cpassword']
        birthdate = request.form['birthdate']
        phonenumber = request.form['phonenumber']
        job = request.form['job']
        income = request.form['income']
        sql = "SELECT * FROM regi WHERE email = ? "
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,email)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            msg = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
        elif not re.match(r'[A-Za-z0-9]+', firstname):
            msg = 'firstname must contain only characters and numbers !'
        elif not email or not firstname or not password1:
            msg = 'Please fill out the form !'
        else:
            insert_sql = "INSERT INTO regi(firstname,lastname,email,password1,cpassword,birthdate,phonenumber,job,income) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            stmt = ibm_db.prepare(conn,insert_sql)
            ibm_db.bind_param(stmt, 1, firstname)
            ibm_db.bind_param(stmt, 2, lastname)
            ibm_db.bind_param(stmt, 3, email)
            ibm_db.bind_param(stmt, 4, password1)
            ibm_db.bind_param(stmt, 5, cpassword)
            ibm_db.bind_param(stmt, 6, birthdate)
            ibm_db.bind_param(stmt, 7, phonenumber)
            ibm_db.bind_param(stmt, 8, job)
            ibm_db.bind_param(stmt, 9, income)
            ibm_db.execute(stmt)
            msg = 'You have successfully registered !'
            return render_template('email.html')
    elif request.method == 'POST':
        msg = 'Please fill out the form !'
        
    return render_template('register.html', msg = msg)
@app.route('/userprofile', methods =['GET', 'POST'])
def userprofile():
    if 'id' in session:
        stmt = ibm_db.prepare(conn, 'SELECT firstname,email,income FROM regi WHERE id = ?')
        ibm_db.bind_param(stmt,1,session['id'])
        ibm_db.execute(stmt)
        tb = ibm_db.fetch_assoc(stmt)
        data = []
        while tb != False:
            data.append(tb)
            tb = ibm_db.fetch_assoc(stmt)
        print(data)     
        return render_template('userprofile.html',data=data)
    return render_template('userprofile.html')
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email1 = request.form['email1'] 
        sql = "SELECT * FROM validate WHERE email1 = ? "
        stmt = ibm_db.prepare(conn,sql)
        ibm_db.bind_param(stmt,1,email1)
        ibm_db.execute(stmt)
        account = ibm_db.fetch_assoc(stmt)
        print(account)
        if account:
            msg = 'Account already exists !'
        else:
           insert_sql = "INSERT INTO validate VALUES (?)"
           stmt = ibm_db.prepare(conn,insert_sql)
           ibm_db.bind_param(stmt, 1, email1)
           ibm_db.execute(stmt)
           msg = Message('Hello',sender ='nilavarasi2002@gmail.com',recipients = [email1])
           msg.body = str(otp)
           mail.send(msg)
           return render_template('verify.html')
    return render_template('verify.html')  
@app.route('/validate',methods=['GET', 'POST'])   
def validate():  
 user_otp = request.form['otp']  
 if otp == int(user_otp):  
    return render_template('index.html')
 return render_template('index.html') 

@app.route('/logout', methods=['GET'])
def logout():
    if 'email' in session:
        del session['email']
        del session['id']
        return redirect('/')
    return redirect('/')


if __name__ == '__main__':
    app.run(debug = True)


