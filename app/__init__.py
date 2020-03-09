from flask import Flask

app = Flask(__name__)

from app import views

app.static_folder = 'static'
