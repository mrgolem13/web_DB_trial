from flask import Flask, request, redirect, render_template, session
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.secret_key = '12345'

def get_db():
    conn = sqlite3.connect('board.db')
    cursor = conn.cursor()
    return conn, cursor

def init_db():
    conn, cursor = get_db()
    cursor.execute('''create table if not exists posts (
        id integer primary key autoincrement,
        title text,
        content text,
        author text,
        date text,
        views integer default 0
    )''')

    cursor.execute('''create table if not exists users (
        id integer primary key autoincrement,
        username text, 
        password text,
        role text default 'user'
    )''')

    cursor.execute('select count(*) from users')
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute(
            "insert into users (username, password, role) values (?,?,?)",
            ('admin', '1234', 'admin')
        )
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():

    if 'username' not in session:
        return redirect('/login/')

    conn, cursor = get_db()
    cursor.execute('select count(*) from posts')
    count = cursor.fetchone()[0]

    keyword = request.args.get('keyword', '')

    if keyword:
        cursor.execute('select * from posts where title like ? order by  id desc', ('%' + keyword + '%',))
    else:
        cursor.execute('select * from posts order by id desc')

    posts = cursor.fetchall()
    conn.close()

    if keyword and len(posts) == 0:
        searchResult = f'<p>"{keyword}" 검색 결과가 없습니다.</p>'
    elif not keyword:
        searchResult = '검색어를 입력해주세요.'
    else:
        searchResult = f'<p>"{keyword}" 검색 결과: {len(posts)}건</p>'

    postList = ''
    for post in posts:
        postList += f'''
        <tr>
            <td>{post[0]}</td>
            <td><a href="/detail/{post[0]}/">{post[1]}</a></td>
            <td>{post[3]}</td>
            <td>{post[4]}</td>
            <td>{post[5]}</td>
        </tr>
        '''
    return render_template('index.html',
                           count=count,
                           keyword=keyword,
                           searchResult=searchResult,
                           postList=postList
                           )


@app.route('/detail/<id>/')
def detail(id):
    conn, cursor = get_db()

    cursor.execute('update posts set views = views + 1 where id = ?',(id,))
    conn.commit()

    cursor.execute('select * from posts where id = ?',(id,))
    post = cursor.fetchone()
    conn.close()

    return render_template('detail.html',
                           post=post)

@app.route('/create/', methods=['GET', 'POST'])
def create():
    if 'username' not in session:
        return redirect('/login/')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        date = datetime.now().strftime('%Y-%m-%d')

        conn, cursor = get_db()
        cursor.execute(
            'insert into posts (title, content, author, date) values (?, ?, ?, ?)',
            (title, content, author, date)
        )
        conn.commit()
        conn.close()
        return redirect('/')

    return render_template('create.html')

@app.route('/update/<id>/', methods=['GET', 'POST'])
def update(id):
    conn, cursor = get_db()
    if 'username' not in session:
        return redirect('/login/')

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']

        cursor.execute(
            'update posts set title=?, content=?, author=? where id =?', (title, content, author, id)
        )
        conn.commit()
        conn.close()
        return redirect(f'/detail/{id}/')

    cursor.execute('select * from posts where id=?', (id,))
    post = cursor.fetchone()
    conn.close()

    return render_template('update.html',
                           post=post,
                           id=id)

@app.route('/delete/<id>/')
def delete(id):
    if 'username' not in session:
        return redirect('/login/')

    conn, cursor = get_db()
    cursor.execute('delete from posts where id=?', (id,))
    conn.commit()


    cursor.execute('select id from posts order by id LIMIT 1')
    first = cursor.fetchone()
    conn.close()

    if first:
        return redirect(f'/detail/{first[0]}/')
    else:
        return redirect('/empty/')


@app.route('/empty/')
def empty():
    return render_template('empty.html')

@app.route('/register/', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn, cursor = get_db()
        cursor.execute('select * from users where username = ?', (username,))
        user = cursor.fetchone()
        if user:
            conn.close()
            return render_template('register.html', error='이미 존재하는 아이디입니다.', success='')
        cursor.execute(
            'insert into users (username, password) values (?, ?)',
            (username, password)
        )
        conn.commit()
        conn.close()

        session['username'] = username
        return render_template('register.html', error='', success='회원가입에 성공했습니다.')
    return render_template('register.html',error='', success='')

@app.route('/login/', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn, cursor = get_db()
        cursor.execute('select * from users where username = ? and password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['username'] = user[1]
            session['role'] = user[3]

            if user[3] == 'admin':
                return redirect('/admin/')
            else:
                return redirect('/')
        else:
            return render_template('login.html', error='아이디 혹은 비밀번호가 일치하지 않습니다.')

    return render_template('login.html', error='')

@app.route('/logout/')
def logout():
    session.pop('username', None)
    return redirect('/')

@app.route('/admin/')
def admin():
    if 'username' not in session:
        return redirect('/login/')
    if session.get('role') != 'admin':
        return redirect('/')

    conn, cursor = get_db()
    cursor.execute('select * from users')
    users = cursor.fetchall()
    cursor.execute('select * from posts order by id desc')
    posts = cursor.fetchall()
    cursor.execute('select count(*) from users')
    userCount = cursor.fetchone()[0]
    cursor.execute('select count(*) from posts')
    postCount = cursor.fetchone()[0]
    conn.close()

    return render_template('admin.html',
                       users = users,
                       posts = posts,
                       userCount = userCount,
                       postCount = postCount)

@app.route('/admin/delete/<id>/')
def admin_delete(id):
    if session.get('role') != 'admin':
        return redirect('/')
    conn, cursor = get_db()
    cursor.execute('delete from users where id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/')

@app.route('/admin/role/<id>/')
def admin_role(id):
    if session.get('role') != 'admin':
        return redirect('/')
    conn, cursor = get_db()
    cursor.execute('select role from users where id = ?', (id,))
    user = cursor.fetchone()
    if user[0] == 'user':
        newRole = 'admin'
    else:
        newRole = 'user'
    cursor.execute('update users set role = ? where id=?', (newRole, id))
    conn.commit()
    conn.close()
    return redirect('/admin/')

@app.route('/admin/post/delete/<id>/')
def admin_post_delete(id):
    if session.get('role') != 'admin':
        return redirect('/')
    conn, cursor = get_db()
    cursor.execute('delete from posts where id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect('/admin/')


#app.run(debug=True)