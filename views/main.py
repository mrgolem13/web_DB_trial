from flask import Flask
import random
import sqlite3

app=Flask(__name__)
def init_db():
    conn = sqlite3.connect('course.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS course (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, body TEXT)''')
    cursor.execute("SELECT count() FROM course")
    count=cursor.fetchone()[0]

    if count==0:
        data = [
            ('flask','flask is...'),
            ('python','python is...'),
            ('webDB', 'webDB is...')
        ]
        for item in data:
            cursor.execute('INSERT INTO course(title, body) VALUES(?,?)', item)
    conn.commit()
    conn.close()

init_db()

courses=[
    {'id' :1, 'title':'flask', 'body':'flask is ...'},
    {'id' :2, 'title':'python', 'body':'python is ...'},
    {'id' :3, 'title':'webDB', 'body':'webDB is ...'}
]

@app.route('/') #길찾기
def index():
    courseList =''
    for course in courses:
        courseList = courseList + f'<li> <a herf = "/read/{course["id"]}/">{course["title"]}</a></li>'

    return '''<!DOCTYPE html>
    <html>
        <body>
        <h1><a href="/">WEB</a><h1>
        <ol>
            <li><a href="read/1">flask</a></li>
            <li><a href="read/2">python</a></li>
            <li><a href="read/3">webDB</a></li>
        </ol>
        </body>
    </html>              
    '''



@app.route('/create/')
def create():
    return 'Create'

@app.route('/read/<id>/')
def read(id):
    print(id)
    return 'Read' + id

@app.route('/hello/')
def hello():
    return '안녕하세요'

@app.route('/greet/<name>/')
def greet(name):
    print (name)
    return f'안녕하세요, {name}님'


@app.route('/multiply/<int:num>/')
def multiply(num):
    result = num * 2
    return f'{result}'



app.run(debug=True)
