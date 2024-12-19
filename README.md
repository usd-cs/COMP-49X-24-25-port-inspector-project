# COMP-49X-24-25-port-inspector-project

# Photo Upload and History Application

This project is a web application built with Django that allows users to upload photos and view their upload history. It provides a simple interface for photo management, enabling users to track their uploads conveniently.

## Features
The application satisfies the following user stories:

- **Photo Upload:** As a user, I want to be able to upload photos so that I can store and track them for future reference.
- **View Upload History:** As a user, I want to view a history of all the photos I have uploaded so that I can easily access my past uploads.

## Technologies Used
- **Backend & Frontend Framework:** Django
- **Database:** Django’s default SQLite (or specify another database if applicable)

## Setup and Installation

### 1. Clone the Repository
```bash
git clone https://github.com/example/photo-upload-history-app.git
```

### 2. Navigate to the Project Directory
```bash
cd photo-upload-history-app
```

### 3. Install Dependencies
Ensure you have Django installed or install it via pip:
```bash
pip install django
```

### 4. Run Migrations
Set up the database tables by running:
```bash
python3 manage.py migrate
```

## Running the Server

### 1. Start the Server
Run the following command to start the development server:
```bash
python3 manage.py runserver
```

### 2. Access the Application
Open a web browser and go to the following link:
```
http://127.0.0.1:8000/
```

## Notes
- This application does not yet include login functionality. All uploads and history are visible without authentication.
- Future updates may introduce user accounts for better photo management and privacy.

