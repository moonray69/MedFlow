MedFlow

Overview

MedFlow is a healthcare management system developed to simplify interaction between patients and doctors. The platform allows patients to register, choose a family doctor, book appointments, and receive medical recommendations, while doctors can manage appointments, review patient complaints, and use ICPC-2-based clinical support tools.

The project was developed using FastAPI, PostgreSQL, SQLAlchemy, HTML, CSS, JavaScript, and Docker.

⸻

Features

Patient Module

* Patient registration and authentication
* Personal patient dashboard
* Family doctor selection
* Medical declaration simulation
* Appointment booking system
* Viewing assigned family doctor
* Appointment history
* Receiving doctor recommendations

Doctor Module

* Doctor registration and authentication
* Personal doctor dashboard
* Appointment management
* Viewing patient complaints and contact information
* Creating medical recommendations
* Saving treatment notes and prescriptions
* Profile management with doctor information

Clinical Decision Support

* Automatic analysis of patient symptoms
* ICPC-2 complaint classification
* Detection of multiple complaint categories from a single description
* Clinical reference information for doctors
* Recommendations on what to assess during examination
* Warning messages for potentially serious symptoms

Example:

Patient complaint:

“I have abdominal pain, ear pain, heart pain and fever.”

The system automatically identifies several ICPC-2 categories and provides relevant clinical guidance for each symptom.

⸻

Technologies

Backend

* Python 3
* FastAPI
* SQLAlchemy
* Pydantic
* PostgreSQL

Frontend

* HTML5
* CSS3
* JavaScript

Infrastructure

* Docker
* Docker Compose

Medical Standards

* ICPC-2 (International Classification of Primary Care)

⸻

## Project Structure

```text
medflow_api/
│
├── app/
│   ├── static/
│   ├── templates/
│   ├── config.py
│   ├── crud.py
│   ├── database.py
│   ├── database_utils.py
│   ├── main.py
│   ├── models.py
│   └── schemas.py
│
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

⸻

Installation

Clone repository

git clone https://github.com/your-username/MedFlow.git
cd MedFlow

Create virtual environment

python -m venv .venv

Activate environment

Windows:

.venv\Scripts\activate

macOS/Linux:

source .venv/bin/activate

Install dependencies

pip install -r requirements.txt

Run application

uvicorn app.main:app --reload

Application will be available at:

http://127.0.0.1:8000

Swagger documentation:

http://127.0.0.1:8000/docs

⸻

Docker Deployment

Build and start containers:

docker-compose up --build

Stop containers:

docker-compose down

⸻

Future Improvements

* Integration with DEC clinical protocols
* Electronic medical records
* Laboratory results management
* Referral system
* Notification system
* Online consultations
* AI-assisted symptom analysis
* Expanded ICPC-2 knowledge base
* Role-based access control
* JWT authentication

⸻

Educational Purpose

This project was developed as part of academic and practical training to demonstrate the use of modern web technologies in healthcare information systems.

⸻

Author

Oleksandr Kravets

Taras Shevchenko National University of Kyiv

IoT Programming Technologies