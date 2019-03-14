from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

import os
import sqlite3

app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'wishlist.db'),
    SECRET_KEY='the secret key',
    USERNAME='admin',
    PASSWORD='passwd'
))

def connect_db():
    """connect to the database"""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    if not hasattr(g, 'wishlist.db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'wishlist.db'):
        g.sqlite_db.close()

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized the database.')

@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select id, title, url, description from entries order by id asc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, url, description) values (?, ?, ?)',
                [request.form['title'],
                request.form['url'],
                request.form['description']])
    db.commit()
    flash('Nouveau souhait à exhausser !')
    return redirect(url_for('show_entries'))

@app.route('/del', methods=['POST'])
def delete_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('delete from entries where id = ?',
        [request.form['id']])
    db.commit()
    flash('souhait enfin exhaussé !')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid User'
        elif request.form['password'] != app.config['PASSWORD']:
            error = "Invalid Password"
        else:
            session['logged_in'] = True
            flash('Tu es connecté !')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Tu es maintenant déconnecté !')
    return redirect(url_for('show_entries'))


