import os
import sys
import pymysql
from flask import Flask

# db=SQLALchemy()

# #console bug solver
if sys.platform.lower()=="win32":
	os.system('color')

def create_app():
	#Initialize core application
	app=Flask(__name__)
	
	# db.init_app(app)
	with app.app_context(): #main context of the app

		#importing routes from routes.py
		from . import routes
		#registering blueprint from routes 
		app.register_blueprint(routes.freshbasket_blueprint)

		return app
