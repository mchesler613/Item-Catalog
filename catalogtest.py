from flask import Flask, jsonify
import contextlib
import json
import datetime
import time
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Item, User

'''
'''
app = Flask(__name__)

'''
Bind the engine to the metadata of the Base class so that
the declaratives can be accessed through a DBSession instance
'''
dburl = 'sqlite:///catalogwithusers.db'
engine = create_engine(dburl)


'''
A DBSession() instance establishes all conversations with the database
and represents a "staging zone" for all the objects loaded into the
database session object.  Any change made against the objects in the
session won't be persistent into the database until you call
session.commit().  If you're not happy about the changes, you can
revert all of them back to the last commit by calling session.rollback().
'''
DBSession = sessionmaker(bind=engine)
session = DBSession()


def emptydb(session):
    '''
    Empty Database
    '''
    try:
        session.query(Item).delete()
        session.query(Category).delete()
        session.query(User).delete()
        session.commit()
        print "Emptying database"
    except SQLAlchemyError:
        session.rollback()


def createCategory(name, user_id):
    '''
    Create Categories
    '''
    category = Category(name=name, user_id=user_id)
    session.add(category)
    session.commit()
    return category


def createItem(name, description, category_id, user_id):
    '''
    Create an Item for Category
    '''
    item = Item(
        name=name, description=description,
        category_id=category_id, user_id=user_id)
    session.add(item)
    session.commit()

    print "Item %s Added" % name
    return item


def editItem(name, description, item_id, category_id):
    '''
    Edit an existing Item for Category
    '''
    user = session.query(User).filter_by(name='Admin').one()
    item = session.query(Item).filter_by(
        id=item_id, category_id=category_id, user_id=user.id).one()
    item.name = name
    item.description = description
    session.add(item)
    session.commit()
    return item


def deleteItem(item_id, category_id):
    '''
    Delete an existing Item for Category
    '''
    user = session.query(User).filter_by(name='Admin').one()
    item = session.query(Item).filter_by(
        id=item_id, category_id=category_id, user_id=user.id).one()
    session.delete(item)
    session.commit()
    return True


def showItem(item_id):
    '''
    Show Item based on its id
    '''
    user = session.query(User).filter_by(name='Admin').one()
    item = session.query(Item).filter_by(id=item_id, user_id=user.id).one()
    print "   ITEM ID: %d, NAME: %s, DESCRIPTION: %s, "\
        "CREATED: %s, CREATED_BY: %d CATEGORY: %s" \
        % (item.id, item.name, item.description, item.created,
            item.user_id, item.category_id)


def showLatestItems(limit):
    '''
    Show only the latest X Items
    '''
    print "\nShow latest items "
    items = session.query(Item).order_by(Item.created.desc()).limit(limit)

    for item in items:
        showItem(item.id)


def showCatalog():
    '''
    Show content of Catalog Categories and their corresponding items
    '''
    print "\n***** Show Catalog *****"
    categories = session.query(Category).all()
    for cat in categories:
        print "CATEGORY ID %d %s CREATED_BY %d"\
            % (cat.id, cat.name, cat.user_id)
        items = session.query(Item).filter_by(category_id=cat.id).all()
        for item in items:
            showItem(item.id)


def showCatalogJson():
    '''
    Show Catalog in JSON format
    '''
    catalog = {}
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])
    '''
    for cat in categories :
        #print "CATEGORY ID %d %s" % (cat.id,cat.name)
        print cat.serialize
        items = session.query(Item).filter_by(category_id=cat.id).all()
        #return jsonify(Items=[i.serialize for i in items])
        Items=[i.serialize for i in items]
        print Items
    '''


def showCategory(category_id):
    '''
    Show content of Catalog Category and their corresponding items
    '''
    category = session.query(Category).filter_by(id=category_id).one()
    print "CATEGORY ID %d %s " % (category.id, category.name)
    items = session.query(Item).filter_by(category_id=category_id).all()
    for item in items:
        showItem(item.id)


def createUser(name, email):
    newUser = User(name=name, email=email)
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=email).one()
    return user.id


if __name__ == '__main__':
    app.debug = True
    emptydb(session)

    ''' Create New User '''
    admin_id = createUser(name='Admin', email='admin@catalog.py')

    ''' Create New Items '''
    print "\n****** Adding Items ****** "
    dress = createCategory(name='Dress', user_id=admin_id)
    skirt = createCategory(name='Skirt', user_id=admin_id)
    top = createCategory(name='Top', user_id=admin_id)

    gown = createItem(
        name='Modest Gown',
        description='Modest gown for women and girls', category_id=dress.id,
        user_id=admin_id)
    time.sleep(5)

    tshirt = createItem(
        name='T-Shirt',
        description='Comfy t-shirt for women and girls', category_id=top.id,
        user_id=admin_id)
    time.sleep(5)

    culotte = createItem(
        name='Modest Culotte',
        description='Modest Culotte for women and girls',
        category_id=skirt.id, user_id=admin_id)
    time.sleep(5)

    alineskirt = createItem(
        name='A-line Skirt',
        description='A-line Skirt for women and girls',
        category_id=skirt.id, user_id=admin_id)
    time.sleep(5)

    jumper = createItem(
        name='Modest Jumper',
        description='Made-to-order modest jumper for women and girls',
        category_id=dress.id, user_id=admin_id)
    time.sleep(5)

    sweater = createItem(
        name='Modest Sweater',
        description='Made-to-order modest Sweater for women and girls',
        category_id=top.id, user_id=admin_id)

    ''' Show Latest Items '''
    showLatestItems(3)

    showCatalog()
