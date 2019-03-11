from flask import Flask, jsonify, render_template, request, redirect, url_for
from flask import flash, make_response
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker, exc
from sqlalchemy.exc import SQLAlchemyError
from database_setup import Category, Base, Item, User
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

import contextlib
import httplib2
import json
import random
import string
import requests

'''
Create an instance of the Flask class for our web app.
__name__ is a special variable that gets as value the string __main__ when
executing the script.
'''
app = Flask(__name__)


'''
Google Auth2 Credentials
'''
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog"


'''
Bind the engine to the metadata of the Base class so that
the declaratives can be accessed through a DBSession instance
'''
dburl = 'sqlite:///catalogwithusers.db'
engine = create_engine(dburl)


'''
A DBSession() instance establishes all conversations with the database
and represents a "staging zone" for all the objects loaded into the database
session object.  Any change made against the objects in the session won't
be persistent into the database until you call session.commit().
If you're not happy about the changes, you can revert all of them back to
the last commit by calling session.rollback().
'''
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/catalog/category/new', methods=['GET', 'POST'])
def createCategory():
    '''
    Create Categories
    '''

    # In order to create a category I need to be logged in,
    # If I'm not logged in, I need to be redirected to the Login page
    if 'username' not in login_session:
        return redirect('/login')

    # If this is a POST request
    if request.method == 'POST':

        # Get the Category object based on the logged in user_id
        category = Category(user_id=login_session['user_id'])

        # the 'name' field is non-empty
        if request.form['name']:
            # asssign the 'name' field to the Category object
            category.name = request.form['name']

            # add and commit the Category object to the database
            session.add(category)
            session.commit()

            # added flash message
            flash(
                "Catalog Category '%s' Successfully Added by %s"
                % (category.name, login_session['username'])
            )

            # redirect to the main Catalog page
            return redirect(url_for('showCatalog'))

        # if 'name' field is empty
        else:

            # add flash message
            flash("Category Name must not be blank")

            # re-display the new category page
            return render_template(
                'newcategory.html',
                username=login_session['username']
                if 'username' in login_session else ""
            )

    # if this is a GET request
    else:
        return render_template(
            'newcategory.html',
            username=login_session['username']
            if 'username' in login_session else ""
        )


@app.route(
    '/catalog/<string:category_name>/<int:category_id>/edit',
    methods=['GET', 'POST']
    )
def editCategory(category_name, category_id):
    '''
    Edit Existing Category
    '''
    # if user is not logged in, redirect to login page
    if 'username' not in login_session:
        return redirect('/login')

    # get the category data to edit from the database
    category = session.query(Category).filter_by(id=category_id).one()

    # if user is not the creator of this category, redirect to catalog page
    if category.user_id != login_session['user_id']:
        flash(
            'You are not authorized to edit this category: %s' % category.name)
        return redirect(url_for('showCatalog'))

    # if this is a POST request
    if request.method == 'POST':

        # if category 'name' field is non-blank
        if request.form['name']:
            # assign the 'name' field to the Category object
            category.name = request.form['name']

        # add the Category object to the database and commit it
        session.add(category)
        session.commit()

        # add a flash message
        flash("Catalog Category '%s' Successfully Edited" % category.name)

        # redirect the page to the main Catalog page
        return redirect(url_for('showCatalog'))

    # if this is a GET request
    else:

        # re-display the Edit Category page
        return render_template(
            'editcategory.html',
            category=category,
            category_name=category_name,
            category_id=category_id,
            username=login_session['username']
            if 'username' in login_session else "")


@app.route(
    '/catalog/<string:category_name>/<int:category_id>/delete',
    methods=['GET', 'POST'])
def deleteCategory(category_name, category_id):
    '''
    Delete a specific Category
    '''
    # if user is not logged in, redirect to login page
    if 'username' not in login_session:
        return redirect('/login')

    # get the category data to edit from the database
    category = session.query(Category).filter_by(id=category_id).one()

    # if user is not the creator of this category, redirect to catalog page
    if category.user_id != login_session['user_id']:
        flash(
            'You are not authorized to delete this category: %s'
            % category.name)
        return redirect(url_for('showCatalog'))

    # if this is a POST request
    if request.method == 'POST':
        # first delete all the items in the category
        items = session.query(Item).filter_by(category_id=category.id).all()
        for item in items:
            session.delete(item)
            session.commit()

        # delete the category itself
        session.delete(category)

        # commit actions in the database
        session.commit()

        # add flash message
        flash(
            "Catalog Category '%s' and all its Items Successfully Deleted"
            % category.name)

        # redirect page to main Catalog page
        return redirect(url_for('showCatalog'))

    # if this is a GET request
    else:
        # redisplay Delete Category page
        return render_template(
            'deletecategory.html',
            category_name=category_name,
            category=category,
            username=login_session['username']
            if 'username' in login_session else "")


@app.route(
    '/catalog/<string:category_name>/<int:category_id>/item/new',
    methods=['GET', 'POST'])
def addItemToCategory(category_name, category_id):
    '''
    Add an Item to a Category based on the selected category
    This function is called when a logged-in user already selected a category
    to display its items
    '''
    # if user is not logged in, redirect to login page
    if 'username' not in login_session:
        return redirect('/login')

    # get the category creator
    category = session.query(Category).filter_by(id=category_id).one()

    # if logged-in user is not the creator of this category,
    # redirect to catalog page
    if category.user_id != login_session['user_id']:
        flash(
            'You did not create this category,"\
            " hence you are not authorized to add an item to it')
        return redirect(url_for('showCatalog'))

    # create an Item instance
    item = Item(user_id=login_session['user_id'])

    # get all the categories from database
    categories = session.query(Category).all()

    # if this is a POST request
    if request.method == 'POST':

        # if the 'name' field is non-blank
        if request.form['name']:
            item.name = request.form['name']

        # if the 'description' field is non-blank
        if request.form['description']:
            item.description = request.form['description']

        # get the selected category from the list of options
        if request.form.get('categories'):
            # assign the category id to the Item object
            item.category_id = request.form.get('categories')

            # query the database for the creator of this category
            category_user = session.query(Category).filter_by(
                id=item.category_id).one().user_id

        # if user is not the creator of this category, redirect to catalog page
        if category_user != login_session['user_id']:
            flash(
                "You did not create this category, hence,"
                " you are not authorized to add this item: '%s'" % item.name)
            return redirect(url_for('showCatalog'))
        else:
            # add and commit Item to the database
            session.add(item)
            session.commit()

            # add a flash message
            flash("Catalog Item '%s' Successfully Added" % item.name)

            # redirect page to the Item details page
            return redirect(url_for(
                'showItem',
                category_name=category_name,
                item_name=item.name,
                item_id=item.id))

    # if this is a GET request
    else:
        # redisplay the New Item creation page
        return render_template(
            'newitem.html',
            item=item,
            categories=categories,
            category_id=category_id,
            username=login_session['username']
            if 'username' in login_session else "")


@app.route('/catalog/item/new', methods=['GET', 'POST'])
def createItem():
    '''
    Create a new Catalog Item from the main catalog page
    and no category is selected
    '''
    # if user is not logged in, redirect to login page
    if 'username' not in login_session:
        return redirect('/login')

    # get all the categories from database to populate the newitem.html page
    categories = session.query(Category).all()

    # create an Item instance
    item = Item(user_id=login_session['user_id'])

    # if this is a POST request
    if request.method == 'POST':
        # if 'name' field is non-blank, assign it to the Item object
        if request.form['name']:
            item.name = request.form['name']

        # if 'description' field is non-blank, assign it to the Item object
        if request.form['description']:
            item.description = request.form['description']

        # get the selected category id from the list of options and
        # query the database for category name and user who created it
        if request.form.get('categories'):
            category_id = request.form.get('categories')
            category_name = session.query(Category).filter_by(
                id=category_id).one().name
            category_user = session.query(Category).filter_by(
                id=category_id).one().user_id

        # if user is not the creator of this category, redirect to catalog page
        if category_user != login_session['user_id']:
            flash(
                "You did not create category %s, hence, "
                "hence you are not authorized to add this item: '%s'"
                % (category_name, item.name))
            return redirect(url_for('showCatalog'))
        else:
            # assign the category id to item
            item.category_id = category_id

            # add and commit Item to database
            session.add(item)
            session.commit()

            # add flash message
            flash("Catalog Item '%s' Successfully Added" % item.name)

            # redirect function to show the item details just committed
            return redirect(url_for(
                'showItem',
                category_name=category_name,
                item_name=item.name,
                item_id=item.id))

    # if this is a GET request
    else:
        # redisplay the newitem.html page to create a new catalog item
        return render_template(
            'newitem.html',
            item=item,
            categories=categories,
            username=login_session['username']
            if 'username' in login_session else "")


@app.route(
    '/catalog/<string:category_name>/<string:item_name>/<int:item_id>/edit',
    methods=['GET', 'POST'])
def editItem(category_name, item_name, item_id):
    '''
    Edit an existing Item for displayed Category
    '''
    # if user is not logged in, redirect to login page
    if 'username' not in login_session:
        return redirect('/login')

    # get the Item data from database
    item = session.query(Item).filter_by(id=item_id).one()

    # if user is not the creator of this item, redirect to catalog page
    if item.user_id != login_session['user_id']:
        flash('You are not authorized to edit this item: %s' % item.name)
        return redirect(url_for('showCatalog'))

    # get all the Categories from database to populate the HTML form
    categories = session.query(Category).all()

    # if this is a POST request
    if request.method == 'POST':

        # if the 'name' field is non-blank
        if request.form['name']:
            # assign it to Item
            item.name = request.form['name']

        # if the 'description' field is non-blank
        if request.form['description']:
            # assign it to Item
            item.description = request.form['description']

        if request.form.get('categories'):
            # get the selected category id from the list of options
            category_id = request.form.get('categories')

            # query the database for the name and creator of category
            category_name = session.query(Category).filter_by(
                id=category_id).one().name
            category_user = session.query(Category).filter_by(
                id=category_id).one().user_id

        print "I am %d: Category %s created by %d" \
            % (login_session['user_id'], category_name, category_user)

        # if user is not the creator of this category, redirect to catalog page
        if category_user != login_session['user_id']:
            flash(
                "You did not create category '%s', hence,"
                " you are not authorized to edit this item: '%s'"
                % (category_name, item.name))
            return redirect(url_for('showCatalog'))
        else:
            # assign category_id to item
            item.category_id = category_id

            # add and commit Item to database
            session.add(item)
            session.commit()

            # add flash message
            flash("Catalog Item '%s' Successfully Edited" % item.name)

            # redirect user to the show Item details page
            return redirect(url_for(
                'showItem',
                category_name=category_name,
                item_name=item.name,
                item_id=item.id))

    # if it is a GET request
    else:
        # redisplay the edititem.html page
        return render_template(
            'edititem.html',
            category_name=category_name,
            item=item,
            categories=categories,
            username=login_session['username']
            if 'username' in login_session else "")


@app.route(
    '/catalog/<string:category_name>/<string:item_name>/<int:item_id>/delete',
    methods=['GET', 'POST'])
def deleteItem(category_name, item_name, item_id):
    '''
    Delete an existing Item for Category
    '''
    # if user is not logged in, redirect to login page
    if 'username' not in login_session:
        return redirect('/login')

    # get the Item data from database based on its id
    item = session.query(Item).filter_by(id=item_id).one()

    # if user is not the creator of this item, add flash message
    # and redirect to catalog page
    if item.user_id != login_session['user_id']:
        flash('You are not authorized to delete this item: %s' % item.name)
        return redirect(url_for('showCatalog'))

    # query the database for the creator of this category
    category_user = session.query(Category).filter_by(
        id=item.category_id).one().user_id

    # if user is not the creator of this category, add flash message
    # and redirect to catalog page
    if category_user != login_session['user_id']:
        flash(
            "You did not create this category '%s', hence,"
            " you are not authorized to delete this item: '%s'"
            % (category_name, item.name))
        return redirect(url_for('showCatalog'))

    # if this is a POST request
    if request.method == 'POST':
        # delete and commit Item in database
        session.delete(item)
        session.commit()

        # add flash message
        flash("Catalog Item '%s' Successfully deleted" % item.name)

        # redirect user to the main catalog page
        return redirect(url_for('showCatalog'))

    # if this is a GET request
    else:
        # redisplay the deleteitem.html page
        return render_template(
            'deleteitem.html',
            category_name=category_name,
            item=item,
            username=login_session['username']
            if 'username' in login_session else "")


@app.route('/catalog/<string:category_name>/<string:item_name>/<int:item_id>')
def showItem(category_name, item_name, item_id):
    '''
    Show Item details based on its id
    '''

    # get Item based on its id
    item = session.query(Item).filter_by(id=item_id).one()

    # get Category based on item id
    category = session.query(Category).filter_by(id=item.category_id).one()

    '''
    print "   ITEM ID: %d, NAME: %s, DESCRIPTION: %s, CATEGORY: %s" \
        %(item.id, item.name, item.description, category_name)

    print " login user %d, item created by %d, category created by %d" \
        %(login_session['user_id'], item.user_id, category.user_id)
    '''

    # display itemdetail.html page
    return render_template(
        'itemdetail.html',
        user_id=login_session['user_id'] if 'user_id' in login_session else "",
        item=item,
        category=category,
        category_name=category_name,
        username=login_session['username']
        if 'username' in login_session else "")


@app.route(
    '/catalog/<string:category_name>/<string:item_name>/<int:item_id>/JSON')
def showItemJson(category_name, item_name, item_id):
    '''
    Show Item details based on its id in JSON format
    '''
    # get Item based on its id
    item = session.query(Item).filter_by(id=item_id).one()

    return jsonify(item.serialize)


def showLatestItems(limit):
    '''
    Show only the latest [limit] Items
    '''
    # get a limited number of items from database that are created last
    items = session.query(Item).order_by(Item.created.desc()).limit(limit)

    # create a dictionary list
    latest_items = []

    # traverse each item in items
    for item in items:
        # showItem(item.id)

        # query the database for the category associated with item
        category = session.query(Category).filter_by(id=item.category_id).one()

        # append a dictionary to list
        latest_items.append(
            {'id': item.id, 'name': item.name, 'category': category.name})

    # return the dictionary list
    return latest_items


@app.route('/catalog/<string:category_name>/<int:category_id>/items')
def showCategory(category_name, category_id):
    '''
    Show content of Category and its corresponding items
    No Login required
    '''

    # get categories from database ordered by name
    categories = session.query(Category).order_by(asc(Category.name))

    # get category by its id
    category = session.query(Category).filter_by(id=category_id).one()

    # get catalog items for this category
    items = session.query(Item).filter_by(category_id=category_id).all()

    # get the count of items
    rows = session.query(Item).filter_by(category_id=category_id).count()

    # display the catalogitem.html page
    return render_template(
        'catalogitem.html',
        categories=categories,
        items=items,
        rows=rows,
        category=category,
        user_id=login_session['user_id']
        if 'user_id' in login_session else "",
        username=login_session['username']
        if 'username' in login_session else "")


@app.route('/')
@app.route('/catalog')
@app.route('/catalog/')
def showCatalog():
    '''
    Show content of Catalog Categories and their corresponding items
    '''
    # get categories from database ordered by name
    categories = session.query(Category).order_by(asc(Category.name))

    # get count of categories
    rows = session.query(Category).count()

    # get the latest items based on the number of existing categories
    latest_items = showLatestItems(rows)

    # display the catalog.html page
    return render_template(
        'catalog.html',
        categories=categories,
        latest_items=latest_items,
        username=login_session['username']
        if 'username' in login_session else "")


@app.route('/catalog.json')
def showCatalogJson():
    '''
    Show Catalog in JSON format
    '''
    catalog = {}
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def showLogin():
    '''
    Create anti-forgery state token
    '''
    # print "showLogin"

    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state

    print "The current session state is %s" % login_session['state']

    # display the login.html page
    return render_template('login.html', STATE=state)


def createUser(login_session):
    '''
    User Helper Functions
    '''

    # create a User object containing username, email and picture link
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])

    # add and commit user to database
    session.add(newUser)
    session.commit()

    # query the User object from database and get its unique ID
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):

    '''
    Query the database for a User based on its unique ID and return it
    '''
    try:
        user = session.query(User).filter_by(id=user_id).one()
        return user
    except SQLAlchemyError:
        return None


def getUserID(email):
    '''
    Query the database for a User based on its email address and return its ID
    '''
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except SQLAlchemyError:
        return None


def getUsername():
    '''
    Return the unique username of a logged in user
    '''
    return login_session['username']


@app.route('/glogin', methods=['POST'])
def glogin():
    '''
    Google Login Session code taken from Udacity's repository gconnect
    '''

    print "glogin"

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
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None \
            and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' style = "width: 300px; height: 300px;'\
        'border-radius: 150px; -webkit-border-radius: 150px;'\
        '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/glogout')
def glogout():
    '''
    Google Logout function taken from Udacity's repository name gdisconnect
    '''
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    '''
    Generic Logout function taken from Udacity's connect function
    '''
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            glogout()
            del login_session['gplus_id']
            del login_session['access_token']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCatalog'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalog'))


if __name__ == '__main__':
    app.secret_key = "specialsecretkey"
    app.debug = True
    app.run(host='0.0.0.0', port=8000, threaded=False)
