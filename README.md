# Prot Linestore

A small online store built as a personal project while learning Django and web development. 📚

## About the Project

Prot Linestore lets visitors browse products and categories, open product pages, and submit an order for a product. Registered users can add reviews and manage a basic profile.

The site interface is currently in Russian. This project is for learning and experimenting; it is not a finished or production-ready store.

## Features

- Browse active products and filter them by category.
- View product details, prices, images, and attached files.
- Create an account, sign in, and edit profile details and a profile photo.
- Leave a rating and written review while signed in.
- Submit an order with contact and delivery-address details.
- Manage products, categories, reviews, and orders through Django admin.
- Use a small REST API for product data and JSON account registration.

Orders are saved by the application, but the project does not process payments or arrange delivery.

## Technologies Used

- Python and Django
- Django REST Framework
- SQLite
- HTML, CSS, and JavaScript
- Pillow for image support
- Argon2 for password hashing
- `python-dotenv` for optional local environment settings

## Project Structure

```text
myproj/                 Django project settings and main URLs
onlinestore/            Store models, views, forms, API, and admin setup
onlinestore/templates/  HTML pages
onlinestore/static/     App CSS, JavaScript, and other static assets
templates/              Shared project-level templates
media/                  Uploaded product files and profile photos (local)
manage.py               Django command-line utility
requirements.txt        Python dependencies
.env.example            Example local environment settings
```

## Installation

You need Python 3.12 or newer for the Django version listed in `requirements.txt`.

Clone the repository and move into its folder:

```bash
git clone https://github.com/lasteclipse1425/prot-linestore.git
cd prot-linestore
```

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```bat
py -m venv .venv
.\.venv\Scripts\activate.bat
```

**Linux or macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## How to Run

The project uses SQLite by default, so no separate database server is needed for local development. From the repository root, apply migrations and create an admin account:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to view the store. The admin site is at [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

For local development, the project has default settings and can run without a `.env` file. Optional settings such as `DJANGO_SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS` can be set in a root-level `.env` file. Do not use the development defaults for a public deployment, and do not commit a real secret key.

## API Endpoints

These routes are defined in the project:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET`, `POST` | `/api/products/` | List products or create a product |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/products/<id>/` | Read, update, or delete one product |
| `POST` | `/api/register/` | Register an account using a JSON request |

The registration endpoint uses Django's CSRF protection. The API is a basic project feature and does not have a separate API guide yet.

## What I Learned

Building this project gave me practice with Django models, views, forms, templates, URL routing, user accounts, file uploads, and Django REST Framework.

## Future Improvements

- Add a shopping cart and a clearer multi-product checkout.
- Connect a payment provider.
- Improve the API documentation and tests.
- Polish the interface and add screenshots.

## Author

**lasteclipse1425** — a beginner Django developer sharing a project built while learning.
