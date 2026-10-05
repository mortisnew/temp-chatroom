# Temp Chatroom

A simple anonymous real-time chatroom built with Django.

Create a room, choose a nickname, share the room link, and start chatting. No account or registration is required.

Rooms are temporary and automatically expire after 30 minutes.

## Features

- Anonymous chat
- Real-time messaging with WebSockets
- Shareable room links
- Nickname-based identity
- Online member tracking
- Temporary rooms
- Automatic room cleanup
- Message rate limiting
- No registration required

## Built With

- Python
- Django
- Django REST Framework
- Django Channels
- Daphne
- Redis
- PostgreSQL
- Celery
- django-celery-beat

## How It Works

A user creates a room and gets a unique room link. Other users can join the room using that link and choose a nickname.

Messages are sent in real time using WebSockets. Redis handles the channel layer and temporary presence data, while PostgreSQL stores the application data.

Rooms expire after 30 minutes and Celery handles the automatic cleanup.

## Running Locally

Clone the repository:

    git clone git@github.com:mortisnew/temp-chatroom.git
    cd temp-chatroom

Create a virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate

Install the dependencies:

    pip install -r requirements.txt

Set up your PostgreSQL database and environment variables, then run:

    python manage.py migrate

Start Daphne:

    daphne config.asgi:application

In separate terminals, run Celery worker and beat:

    celery -A config worker -l info

    celery -A config beat -l info

Then open the local address in your browser.

## Why I Built This

This project was mainly built to learn how Django Channels, WebSockets, Redis, and Celery work together in a real-time application.
