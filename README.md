# SnitchTracker
## Purpose
Welcome to Snitch Tracker!

The purpose of this repository is to create a website that allows you to have more control over your snitches.
## Installation
This repository will only help you in setting up dev mode for django. We will not provide support on properly hosting this website yourself as it verys between operating systems and how you choose to do it.

First things first if you are running on windows or linus/macos setting up will be a little different.

First you want to make sure that both python3.6+ and pip are installed on your system.

Then you are going to want to git clone it to a location of your choice on your computer and then you will navigate to it.

Then you are going to install a virtual environment for this python project.
Note:
> This tutorial assumes you are running all commands inside the top level of this git repository.

You will run
> python -m pip install virtualenv

If you are on windows you will also run
> python -m pip install VirtualEnvWrapper-win

Then run
> mkvirtualenv env

Then if on Linux/macos
> source env/Scripts/activate

If windows run
> cd env/Scripts

> activate.bat

Navigate back to the main directory. If you do not see (env) before your path in terminal then most likely something is wrong with the program you are using maybe. I recommend using either cmd for windows or terminal for linux.

Then run:
> python -m pip install -r requirements.txt

> cd snitchtracker

> python manage.py makemigrations

> python manage.py migrate

If you would like to create an admin user run:

> python manage.py createsuperuser

and follow the prompts.

Next:
> cd snitchtracker

and you will want to rename secretstemplate.py to secrets.py and then update the config options to your preferences.

Thats it, you should now have successfully installed everything this project needs to run. If you are having any issues feel free to make an issue.

## Starting the server
From the top level directory of the project navigate into snitchtracker and run

> python manage.py startserver

and if you navigate your browser to localhost:8000 it should be up.
