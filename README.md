# Item Catalog
## Project Description

The Item Catalog is a database-driven project that manages the inventory of a catalog over the Web.  

My task is to provide both a front-end and back-end Web interface to create, display and update this catalog in a user-friendly manner. 


# Design

I design the solution for this project using the [http://flask.pocoo.org/]Flask Python framework and [https://docs.sqlalchemy.org] SQLAlchemy for the database management. The Web interface runs on a [http://localhost:8000] localhost on port 8000 as specified by the project requirements.

## Database Schema
The database schema is composed of 3 tables:

 - Catalog Item
 - Category
 - User 

## Web Interface
The Web interface supports the following endpoints:

 - /catalog.json - to view the entire catalog via the [https://www.json.org/] JSON serialized dictionary
 - / or /catalog or /catalog/ - to view the home page consisting of a the categories and the latest items added to the catalog
 - /catalog/<category_name>/<category_id>/items - to view the items in a category
 - /catalog/<category_name>/<item_name>/<item_id> - to view the item description
 - /login - enable a user to log in via Google SignIn in order to manage the catalog

The following endpoints are available only to the logged-in user:
 - /catalog/category/new - enable a logged-in user to create a new Category in the catalog from the home page
 - /catalog/<category_name>/<category_id>/edit - enable a logged-in user to edit the category they previously created
 - /catalog/<category_name>/<category_id>/delete - enable a logged-in user to delete the category they previously created
 - /catalog/item/new - enable a logged-in user to create a new Item in the catalog from the home page
 - /catalog/<category_name>/<category_id>/item/new - enable a logged-in user to create a new item to the category they previously created from the Category display page
 - /catalog/<category_name>/<item_name>/<item_id>/edit - enable a logged-in user to edit the item previously created
 - /catalog/<category_name>/<item_name>/<item_id>/delete - enable a logged-in user to delete the item previously created
 - /logout - enable a logged-in user to log out

# Installation

This project requires that the following files and modules be installed:

 - [https://www.python.org/download/releases/2.7/] Python version 2.7, 
 - + rename the Python executable to python2
 - [https://www.virtualbox.org/] Oracle VM VirtualBox
 - [https://www.vagrantup.com/] Vagrant
 - + Run Vagrant via this comand `vagrant up` followed by `vagrant ssh`
 - install the [Flask](http://flask.pocoo.org/) modules via `python2 -m pip install Flask`
 - install the [SQLAlchemy](https://docs.sqlalchemy.org) modules via `python2 -m pip install sqlalchemy`
 - install the [oauth2client package](https://pypi.org/project/oauth2client/) via `python2 -m pip install oauth2client`
 - install the requests package via `python2 -m pip install requests`
 - **client_secrets.json**, which is a downloadable JSON file created by setting up credentials for a  [Google SignIn OAuth2](%5Bhttps://console.developers.google.com/apis/credentials/oauthclient%5D) authentication
 - **static/catalog.css** contains the CSS styling for the frontend Web interface 
 - **templates/** directory containing HTML template files for rendering the catalog on the Web
 - **/database_setup.py** file contains the database schema Python objects
 - **/catalogtest.py** file contains Python instructions to populate the catalog database with sample data
 - **/catalog.py** file contains the Python catalog application

## Populate the database with sample data
Run the following commands to create and populate the database **catalogwithusers.db**

    python2 database_setup.py
    python2 catalogtest.py

The sample database contains data for a catalog of clothing categories and items.

## Run the Catalog application
Execute the following command in a terminal

    python2 catalog.py

Open up your web browser (tested on both Firefox and Chrome) at this location: http://localhost:8000

# Notes
Since Google deprecated the old Google Signin API on March 7, 2019, I requested help through Udacity's Knowledge Forum to implement a working version of the Google authentication code.  I would like to thank a fellow Udacity member, Shyam Gupta, who provided a link [https://gist.github.com/shyamgupta/d8ba035403e8165510585b805cf64ee6] to assist in replacing the old Google authentication module.  
