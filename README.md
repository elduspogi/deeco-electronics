# Deeco Electronics.

## Your One Stop Shop For Electronic Needs

### System Requirements:

- Install Python

- Install PIP

### Project Requirements

- Creating a **Virtual Environment**

  - On your terminal, run the command: **_pip install virtualenv_**

  - Navigate to your project directory(where the file **_manage.py_** is located)

  - Run the command: path-to-project/virtualenv **_your desired name_**

    - In this case we'll name it **_venv_**, for your reference.
      - path-to-project/virtualenv venv

  - Activate the virtual environment.
    - To activate, run the command: **_your venv name_**\Scripts\activate
    - To deactivate, just change the activate to **_deactivate_**

- Install packages using **PIP**

  - Open terminal, locate the path of the project.

  - Run the command: path-to-project/pip install requirements.txt

- Copying the .env.example

  - Run the command, again path to the project: path-to-project/cp .env.example .env

  - It will generate a .env file for you.

  - Change the variables in the .env to the configurations on your local machine.

- Generating **_SECRET_KEY_**

  - On path of the project run this command: path-to-project/python manage.py shell

  - You will enter the shell console.

  - Run this command: **_from django.core.management.utils import get_random_secret_key_**

  - Run this command: **_key = get_random_secret_key()_**

  - Run this command: **_print(key)_**

  - It will print out a fresh new secret key for you to paste in the .env file

- Create **Database**

  - Use your preffered MySQL GUI(phpmyadmin/workbench) here.

  - Create a Schema/Database. Name it whatever you want, in this case we'll name it **_deeco_ecommerce_** for your reference.

- Run **Migrations**

  - Still on the path of the project, run the command: path-to-project/**_python manage.py makemigrations_**

  - After that, run the command: path-to-project/**_python manage.py migrate_**

- Creating **superuser**

  - Navigate to the path of the project.

  - Run the command: path-to-project/**_python manage.py createsuperuser_**

  - Fill out the fields that are needed and you're good to go

- Running the Server

  - Navigate to the path of the project (where manage.py is located).

  - Run the command: path-to-project/**_python manage.py runserver_**

  - The server will run on port 8000.

  - Visit the site on 127.0.0.1:8000 or localhost:8000

- Access the **Django Admin Page**

  - The URL is 127.0.0.1:8000/deeco-admin
