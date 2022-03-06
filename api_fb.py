from flask import Flask
from flask import request
from time import time
import psycopg2
from psycopg2 import Error
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess, sys


try:
    connection = psycopg2.connect(user="",
                                  password="",
                                  host="",
                                  port="5432",
                                  database="postgres")

    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)


except (Exception, Error) as error:
    print("Ошибка при работе с PostgreSQL", error)


app = Flask(__name__)

@app.route('/restart', methods = ['POST'])
def __index():
    if request.method == 'POST':
        data = request.form
        ID = data['taskid']
        ID = int(ID)
        mes = subprocess.Popen([sys.executable, "restart.py", str(ID)], 
                                        stdout=subprocess.PIPE, 
                                        stderr=subprocess.STDOUT)
        return

@app.route("/api/createTask", methods = ['POST'])
def index():
    print('Lets go...')
    if request.method == 'POST':
        try:
            data = request.form
            login = data['login']
            password = data['password']

            cursor = connection.cursor()
            create_row = '''INSERT INTO users(login, password, status, createdAt) VALUES (%s, %s, %s, %s)'''
            cursor.execute(create_row, [  login, password, 'created', int(time())  ])
            cursor.close()

            cursor = connection.cursor()
            view = '''SELECT id FROM users WHERE login = %s AND password = %s ORDER BY id'''
            cursor.execute(view, ([login, password]))
            get = cursor.fetchall()
            
            ID = get[-1][0]
            mes = subprocess.Popen([sys.executable, "scrapp.py", str(ID)], 
                                            stdout=subprocess.PIPE, 
                                            stderr=subprocess.STDOUT)
        except Exception as err:
            return {'status': 'error', 'errorText': err}
            
        return {'status': 'created', 'task': ID}

    else:
        return {'status': 'Error data'}


@app.route("/api/2faCode", methods = ['POST'])
def _index():
    if request.method == 'POST':
        try:
            data = request.form
            ID = data['taskid']
            ID = int(ID)
            code = data['code']
            code = int(code)
            
            cursor = connection.cursor()
            cursor.execute('''UPDATE users SET complete = %s WHERE id = %s''', [code, ID])
            cursor.close()
            return {'status': 'Check code'}

        except Exception as err:
            return {'status': 'error', 'errorText': err}



@app.route("/api/infoTask", methods = ['POST'])
def _index():
    if request.method == 'POST':
        try:
            data = request.form
            ID = data['taskid']
            ID = int(ID)
            
            cursor = connection.cursor()
            view = '''select status, createdAt, friendsCount, complete from users where id = %s'''
            cursor.execute(view, [ID])
            gets = cursor.fetchall()

            get = gets[0][0]
            unix = gets[0][1]
            count = gets[0][2]
            compl = gets[0][3]

            if get == 'complete':
                return {'status': 'completed', 'timestamp': unix}

            return {'info': {'state': get, 'count': count, 'completed': compl}}


        except Exception as err:
            return {'status': 'error', 'errorText': err}


if __name__ == '__main__':
    app.run(host="", port="")
