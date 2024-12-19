# COMP-49X-24-25-port-inspector-project

# Photo Upload and History Application

This project is a web application built with Django that allows users to upload photos and view their upload history. It provides a simple interface for photo management, enabling users to track their uploads conveniently.

## Features
The application satisfies the following user stories:

- As a Port Inspector I want to upload a photo of the beetles and be told the likely species’ of the specimen so I can soundly determine if the shipment can be let through
- As a user I want to be able to look back at my previous identifications and the results I received to guide myself going forward, and to have a record in case clarification or data is needed.

## Technologies Used
- **Backend & Frontend Framework:** Django
- **Database:** Django’s default SQLite 

## Setup and Installation

### 1. Clone the Repository
```bash
git clone https://github.com/usd-cs/COMP-49X-24-25-port-inspector-project.git)
```

### 2. Navigate to the Project Directory
```bash
cd port_inspector
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
Open a web browser and go to the following link to upload a photo:
```
http://127.0.0.1:8000/upload
```
To view history, go to the following link:
```
http://127.0.0.1:8000/history
```


