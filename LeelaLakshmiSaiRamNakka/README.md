NAKKA LEELA LAKSHMI SAI RAM 

# AI Support Desk 

An AI-powered IT Support Ticket Management System that helps users raise, manage, track, and resolve support tickets. The system uses **Google Gemini AI** to automatically analyze newly raised tickets and provide category, priority, summary, and recommended actions.

## Features

* User Sign In and Sign Up
* Dashboard with live ticket statistics
* Raise new support tickets
* AI-powered ticket analysis using Gemini
* Automatic ticket category detection
* Automatic priority detection
* AI-generated ticket summary
* AI-generated recommended solution
* Open Tickets management
* Search and filter tickets
* Update ticket status
* Resolve or escalate tickets
* AI Support Agent
* User profile and password settings
* Notification preferences
* Persistent dark mode
* SQLite database
* Responsive web interface

## Main Pages

### 1. Dashboard

Displays real-time information about:

* Total tickets
* Open tickets
* In-progress tickets
* Resolved tickets
* Recent support tickets
* Current support queue status

### 2. Raise Ticket

Users can create a new IT support ticket by providing the required issue information.

After submission, Gemini AI analyzes the ticket and generates:

* Category
* Priority
* Summary
* Recommended action

The ticket is then stored in the SQLite database.

### 3. Open Tickets

Displays tickets stored in the database.

Users can:

* Search tickets
* Filter by department
* Filter by status
* View ticket details
* Mark tickets as In Progress
* Resolve tickets
* Escalate tickets

### 4. AI Agent

Provides an AI-powered support interface for assisting users with IT-related issues.

The AI Agent can help users understand problems and provide suitable troubleshooting guidance.

### 5. About

Provides information about the application, its purpose, technologies, and current support queue.

### 6. Settings

Users can manage:

* Display name
* Password
* Notification preferences
* Application theme

## AI Ticket Processing

The main AI workflow is:

```text
User Raises Ticket
        ↓
Ticket Information Submitted
        ↓
Gemini AI Analysis
        ↓
Category + Priority
        ↓
AI Summary
        ↓
Recommended Action
        ↓
Ticket Stored in SQLite
        ↓
Ticket Appears in Open Tickets
```

## Technology Stack

### Backend

* Python
* Flask
* SQLite
* REST APIs

### Frontend

* HTML
* CSS
* JavaScript

### AI

* Google Gemini API

### Database

* SQLite

## Project Structure

```text
AI-Support-Desk/
│
├── main.py
├── database.db
├── requirements.txt
├── .env.example
├── .gitignore
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── raise_ticket.html
│   ├── open_tickets.html
│   ├── ai_agent.html
│   ├── about.html
│   └── settings.html
│
└── static/
    ├── css/
    │   └── style.css
    │
    └── js/
        └── app.js
```

## API Endpoints

### Authentication

```text
POST /api/auth/login
POST /api/auth/register
```

### Tickets

```text
GET    /api/tickets
POST   /api/tickets
GET    /api/tickets/<id>
PUT    /api/tickets/<id>
DELETE /api/tickets/<id>
```

### Dashboard

```text
GET /api/dashboard/stats
```

### Settings

```text
GET  /api/settings
PUT  /api/settings/profile
PUT  /api/settings/password
```

## Database

The application uses SQLite for storing application data.

The database and required tables are automatically created when the application is started for the first time.

The main ticket information includes:

```text
Ticket ID
User
Title
Description
Category
Priority
Department
AI Summary
AI Recommendation
Status
Created Date
Updated Date
```

## Installation

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd AI-Support-Desk
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Environment File

Create a `.env` file based on `.env.example`.

```bash
cp .env.example .env
```

Add your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
```

Do not upload your actual API key to GitHub.

### 4. Run the Application

```bash
python main.py
```

### 5. Open the Application

Open:

```text
http://localhost:5000
```

## Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key
```

The API key should be stored only in the `.env` file.

Make sure `.env` is included in `.gitignore`.

## What Was Improved

The application was developed to replace static and simulated functionality with real backend functionality.

### Removed

* Static dashboard statistics
* Fake ticket records
* Fake AI responses
* Unused document-upload functionality
* Duplicate page layouts
* Incorrect AI model comments
* Hardcoded ticket information
* Fake AI efficiency statistics
* Broken relative asset paths
* Unused `documents` database table

### Added

* Shared `base.html` layout
* Real SQLite ticket database
* Ticket CRUD operations
* Gemini AI ticket analysis
* Real ticket search and filtering
* Working ticket status updates
* Dashboard live statistics
* Authentication APIs
* Registration and login functionality
* Persistent user settings
* Password update functionality
* Notification preferences
* Persistent dark mode
* AI Support Agent
* Real-time support queue information

## AI Agent Workflow

```text
User
 │
 ▼
Raise Support Ticket
 │
 ▼
Flask Backend
 │
 ▼
Gemini API
 │
 ├── Category
 ├── Priority
 ├── Summary
 └── Recommendation
 │
 ▼
SQLite Database
 │
 ▼
Dashboard / Open Tickets
 │
 ▼
Support Team
 │
 ├── In Progress
 ├── Resolved
 └── Escalated
```

## Security

The project follows basic security practices:

* API keys are stored in environment variables.
* `.env` should not be committed to GitHub.
* Authentication is handled through backend APIs.
* User settings are stored through backend endpoints.
* Sensitive configuration is separated from source code.

## Future Improvements

The project can be extended with:

* Email notifications
* Admin dashboard
* Role-based access control
* Ticket assignment to support agents
* Ticket comments and conversation history
* File attachments
* Knowledge-base integration
* AI-powered ticket resolution
* Automatic ticket escalation
* Vector database and RAG
* Advanced analytics
* Deployment using Render, Railway, or AWS
* Production-grade authentication and security

## Project Objective

The main objective of this project is to build a practical **AI-powered IT Support Ticket Management Agent** that reduces manual ticket classification and helps support teams manage issues more efficiently.

Instead of manually analyzing every ticket, the AI automatically understands the reported problem, determines its priority and category, summarizes the issue, and recommends an appropriate action.

## Conclusion

**AI Support Desk** combines a traditional IT ticket management system with AI-powered assistance to create a simple and practical support automation platform.

The project demonstrates the integration of:

```text
Python + Flask + SQLite + JavaScript + REST APIs + Google Gemini AI
```

into a complete AI-enabled web application.
