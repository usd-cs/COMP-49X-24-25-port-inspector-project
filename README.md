# COMP-49X-24-25-port-inspector-project

# Photo Upload and History Application

This project is a web application built with Django that allows users to upload photos of seed beetles, receive results as to their likely species and genus, and view their upload history. It provides a simple interface for photo management, enabling users to track their uploads conveniently.

## Features
The application satisfies the following user stories:

- As a Port Inspector I want to upload a photo of the beetles and be told the likely species’ of the specimen so I can soundly determine if the shipment can be let through
- As a user I want to be able to look back at my previous identifications and the results I received to guide myself going forward, and to have a record in case clarification or data is needed.

## Technologies Used
- **Backend & Frontend Framework:** Django
- **Database:** Django’s default SQLite 
- **Email API:** MailerSend

## API setup
If planning to host the application on a server, using an email API for account management (email verification, etc.) is required. Our application uses MailerSend but similar API's can be used.  

### 1. Open account with MailerSend
Make an account with [MailerSend](https://www.mailersend.com/), verify the domain you   
would like to host the server on, and generate credentials for SMTP sending.

### 2. Put Credentials in Config File
With the MailerSend credentials, fill out the `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` variables

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
Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)  
With Docker Desktop open, run the following command in the project directory.
```bash
docker compose build
```

## Running the Server

### 1. Start the Server
Use docker to run migrations and start up the server by running the following:
```bash
docker compose up
```

### 2. Access the Application Locally
Open a web browser and go to the following link:
```
http://localhost:8000/
```


