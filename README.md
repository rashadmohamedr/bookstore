# Django Bookstore

A Django web application for browsing books, viewing book details and reviews, and managing user accounts.

## Tech Stack

- Python
- Django
- PostgreSQL (for Docker Compose environments)
- Gunicorn (production server)
- Docker and Docker Compose

## Project Structure

- `accounts/`: user account logic, auth-related forms/views, and management commands
- `books/`: book models, views, urls, and review features
- `pages/`: static/simple pages like home and about
- `templates/`: shared and app templates
- `static/`: project static assets (CSS/JS/images)
- `django_project/`: Django project settings and root URL config

## Prerequisites

- Python 3.10+ (or compatible with your installed dependencies)
- `pip`
- Docker and Docker Compose (optional, for containerized runs)

## Local Development Setup (Without Docker)

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Apply migrations:

```bash
python manage.py migrate
```

4. Create a superuser (optional):

```bash
python manage.py createsuperuser
```

5. Start the development server:

```bash
python manage.py runserver
```

The app should be available at `http://127.0.0.1:8000/`.

## Running with Docker Compose

Development:

```bash
docker compose up --build
```

Production-style compose file:

```bash
docker compose -f docker-compose-prod.yml up --build
```

## Running Tests

App tests:

```bash
python manage.py test
```

Integration tests:

```bash
python tests_integration.py
```

## Useful Management Commands

This project includes custom commands in `accounts/management/commands/`, such as:

- `createsuperuser_if_none_exists`
- `setup_google_auth`

Run with:

```bash
python manage.py <command_name>
```

## Notes

- Uploaded media files are stored under `media/`.
- Collected static files are available under `staticfiles/` for deployment workflows.
