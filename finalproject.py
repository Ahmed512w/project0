from flask import (
    Flask,
    render_template,
    request, redirect,
    jsonify,
    url_for,
    flash,
    session as login_session
)

import random
import string

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, MenuItem, Users

# imports FOR OAuth with GOOGLE API
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

engine = create_engine('postgresql://postgres:sql@localhost/postgres')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read()
    )['web']['client_id']
APPLICATION_NAME = "catalog Application"


def validate(form):
    name = form['name'].strip()
    description = form['description'].strip()
    if len(name) > 3 and len(description) > 9:
        return True
    flash("Name field and Description field are required")
    return False


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = 'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token='
    url += access_token
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended users.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's users ID doesn't match given users ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current users is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get users info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if users exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += '" style = "width: 300px;height: 300px;border-radius: 150px;">'
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/disconnect')
def disconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current users not connected.'),
            401
        )
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token='
    url += login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given users.'),
            400
            )
        response.headers['Content-Type'] = 'application/json'
        return response


# Users Helper Functions
def createUser(login_session):
    newUser = Users(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    users = session.query(Users).filter_by(email=login_session['email']).one()
    return users.id


def getUserInfo(user_id):
    users = session.query(Users).filter_by(id=user_id).one()
    return users


def getUserID(email):
    try:
        users = session.query(Users).filter_by(email=email).one()
        return users.id
    except:
        return None


# JSON APIs to view Categories Information
@app.route('/categories/<int:category_id>/menu/JSON')
def categoryMenuJSON(category_id):
    items = session.query(MenuItem).filter_by(category_id=category_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/categories/<int:category_id>/item/<int:menu_id>/JSON')
def menuItemJSON(category_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/categories/JSON')
def catalogJSON():
    catalog = session.query(Categories).all()
    return jsonify(catalog=[r.serialize for r in catalog])


# Show catalog
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    catalog = session.query(Categories).order_by(asc(Categories.name))
    items = session.query(MenuItem).order_by(MenuItem.time_in.desc()) \
        .limit(catalog.count())
    if 'username' not in login_session:
        return render_template(
          'publiccatalog.html',
          catalog=catalog,
          items=items
          )
    else:
        return render_template('catalog.html', catalog=catalog, items=items)


# Show a Categories Items
@app.route('/categories/<int:category_id>/items/')
def showMenu(category_id):
    catalog = session.query(Categories).order_by(asc(Categories.name))
    categories = session.query(Categories).filter_by(id=category_id).one()

    items = session.query(MenuItem).filter_by(category_id=category_id).all()
    if 'username' not in login_session:
        return render_template(
          'publicmenu.html',
          items=items,
          categories=categories,
          catalog=catalog
          )
    else:
        return render_template(
          'menu.html', items=items,
          categories=categories,
          catalog=catalog
          )


# Show an item description
@app.route('/categories/<int:category_id>/item/<int:menuitem_id>/')
def showMenuItem(category_id, menuitem_id):

    categories = session.query(Categories).filter_by(id=category_id).one()
    item = session.query(MenuItem).filter_by(id=menuitem_id).one()
    creator = getUserInfo(item.user_id)
    if ('username' not in login_session or
            creator.id != login_session['user_id']):
        return render_template(
          'publicmenuitem.html',
          item=item, categories=categories,
          creator=creator
          )
    else:
        return render_template(
          'menuitem.html',
          item=item,
          categories=categories,
          creator=creator
          )


# Create a new menu item from the page of latest items
@app.route('/categories/item/new/', methods=['GET', 'POST'])
def newMenuItem():
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Categories).order_by(asc(Categories.name))
    category_id = 1
    if request.method == 'POST' and validate(request.form):
        newItem = MenuItem(
          name=request.form['name'],
          description=request.form['description'],
          category_id=request.form['categories'],
          user_id=login_session['user_id']
          )
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showMenu', category_id=category_id))
    else:
        return render_template(
          'newmenuitem.html',
          category_id=category_id,
          catalog=catalog
          )


# Create a new menu item from the page of specified categories
@app.route('/categories/<int:category_id>/item/new/', methods=['GET', 'POST'])
def newMenuItemWithCat(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Categories).order_by(asc(Categories.name))
    if request.method == 'POST' and validate(request.form):
        newItem = MenuItem(
          name=request.form['name'],
          description=request.form['description'],
          category_id=request.form['categories'],
          user_id=login_session['user_id']
          )
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showMenu', category_id=category_id))
    else:
        return render_template(
          'newmenuitem.html',
          category_id=category_id,
          catalog=catalog
          )


# Edit a menu item
@app.route('/categories/menu/<int:menuitem_id>/edit', methods=['GET', 'POST'])
def editMenuItem(menuitem_id):
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Categories).order_by(asc(Categories.name))
    editedItem = session.query(MenuItem).filter_by(id=menuitem_id).one()

    if request.method == 'POST' and validate(request.form):
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['categories']:
            editedItem.category_id = request.form['categories']
        session.add(editedItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(
          url_for(
            'showMenu',
            category_id=editedItem.category_id
            )
        )
    else:
        return render_template(
          'editmenuitem.html',
          item=editedItem,
          catalog=catalog
        )


# Delete a menu item
@app.route('/categories/item/<int:menuitem_id>/delete', methods=['GET', 'POST'])
def deleteMenuItem(menuitem_id):
    if 'username' not in login_session:
        return redirect('/login')

    itemToDelete = session.query(MenuItem).filter_by(id=menuitem_id).one()

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(
          url_for('showMenu', category_id=itemToDelete.category_id))
    else:
        return render_template('deleteMenuItem.html', item=itemToDelete)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
