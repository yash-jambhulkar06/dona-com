# Dona.Com — Location-Based Free Food Discovery Platform

[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-TiDB%20%7C%20MySQL-00758F?style=for-the-badge&logo=mysql&logoColor=white)](https://www.pingcap.com/tidb/)
[![Leaflet](https://img.shields.io/badge/Maps-Leaflet%20%7C%20OpenStreetMap-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![UI](https://img.shields.io/badge/Design-Red%20Theme%20%7C%20Emoji--Free-DC2626?style=for-the-badge)](https://github.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [What Does "Dona" Mean?](#2-what-does-dona-mean)
3. [How Dona.Com Works](#3-how-donacom-works)
4. [Features](#4-features)
5. [User Flow](#5-user-flow)
6. [Admin Flow](#6-admin-flow)
7. [Technology Stack](#7-technology-stack)
8. [Project Structure](#8-project-structure)
9. [Future Scope](#9-future-scope)
10. [Installation & Setup](#10-installation--setup)
11. [Screenshots](#11-screenshots)
12. [Contributing](#12-contributing)
13. [License](#13-license)

---

## 1. Project Overview

**Dona.Com** is a location-based free-food discovery platform designed to help people find and share places or events where free food is being served. From traditional community kitchens, langars, and temple mahaprasad to NGO distributions, open celebrations, weddings, birthdays, and public gatherings, Dona.Com bridges the gap between available food and people seeking meals.

Users can submit details about free-food events or venues in their area. Every submission undergoes an administrator review process prior to becoming publicly accessible, ensuring accuracy, safety, and reliability across all listings. By integrating geolocation and proximity-based recommendation algorithms, the platform highlights verified opportunities happening around users in real time.

---

## 2. What Does "Dona" Mean?

In local colloquial slang, the term **"Dona"** is an informal expression referring to the relatable social phenomenon of visiting an event, feast, or gathering to enjoy free food—sometimes without an explicit formal invitation. Whether it is an expansive wedding feast, a bustling community celebration, or a religious function, the expression captures the humorous, grassroots quest of finding a warm, free meal wherever it is being served.

The name **Dona.Com** embraces this informal cultural motif to symbolize the heart of the platform: **discovering places and events where free meals are accessible**.

### Respectful & Ethical Platform Purpose
> **Important Note on Platform Ethics:**  
> While the name draws inspiration from lighthearted slang, **Dona.Com strictly advocates for respectful, community-conscious discovery**. The platform is intended to connect people with **legitimately accessible, open community meals, charitable initiatives, public distributions, and open social celebrations**.  
> The platform **does not encourage or endorse trespassing, illegal entry, property intrusion, or disrupting private functions**. All listings are vetted by administrators to protect venue decorum and support community goodwill.

---

## 3. How Dona.Com Works

Dona.Com functions as a verified, crowd-sourced food discovery network:

```
[ Community Contributor / User ]
               │
               ▼
   Submits Event / Food Location
  (Venue, Serving Hours, Coordinates, Category)
               │
               ▼
    [ Admin Moderation Queue ]
  (Verification of Authenticity & Venue Type)
        │                       │
        ▼                       ▼
   [ Approved ]            [ Rejected ]
        │                       │
        ▼                       ▼
  Live on Public Feed     Feedback to Submitter
  & Near-Me Radius Map    (Reason Logged)
        │
        ▼
[ Public Users & Community Seekers ]
  - Filter by Category & Proximity
  - Turn-by-Turn Navigation
```

1. **Submission:** A registered contributor enters venue information, category, date, serving times, food details, and location coordinates.
2. **Review:** Submissions enter a secure moderation queue as `PENDING`. They remain hidden from public search until verified.
3. **Publishing:** Administrators approve legitimate entries, publishing them instantly to public search and distance-ranked feeds.
4. **Discovery:** Users access the platform, provide location permissions (or search manually), and discover nearby meals with exact directions.

---

## 4. Features

### Core Capabilities

| Feature Area | Description |
| :--- | :--- |
| **Authentication System** | Full user registration, secure credential sign-in, Google OAuth 2.0 integration, and mobile phone SMS OTP verification. |
| **Crowdsourced Event Submission** | Intuitive multi-field form capturing venue titles, category, full address, date, start/end serving times, food description, and map coordinates. |
| **Event Categories** | Clear classification into: `Wedding`, `Birthday`, `Religious Event`, `Community Meal`, and `Other`. |
| **Admin Moderation System** | Dedicated staff dashboard with one-click approval, rejection with logged reason feedback, and full moderation audit trails. |
| **Location-Based Discovery** | Proximity calculation via the Haversine formula, filtering listings by real-time distance from the user. |
| **Smart Recommendations** | Automated prioritization highlighting events that are "Available Now" (within serving hours) and "Starting Soon". |
| **Comprehensive Event Details** | Event information cards displaying exact venue location, serving hours, remaining time badges, and map navigation. |
| **Modern Red-Themed UI** | Clean, responsive design built with an energetic, modern red palette (`#dc2626`) optimized for both mobile and desktop. |
| **Emoji-Free Interface** | Strict professional design aesthetic utilizing clean SVG iconography and typography without unicode emojis. |
| **Production-Grade Functionality** | End-to-end working database persistence, live API endpoints, session handling, and zero mock/demo placeholders. |

---

## 5. User Flow

```
                      +-----------------------------+
                      |         Visitor / User      |
                      +-----------------------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
    +----------------------+                   +-----------------------+
    | Browse Public Feed   |                   | Authentication        |
    | - View Approved Food |                   | - Email & Password    |
    | - Filter by Category |                   | - Google Sign-In      |
    | - Nearby Search      |                   | - Mobile OTP Auth     |
    +----------------------+                   +-----------------------+
               |                                           |
               |                                           v
               |                               +-----------------------+
               |                               | Submit Free Food Event|
               |                               | - Venue & Category    |
               |                               | - Serving Times       |
               |                               | - Coordinates / Map   |
               |                               +-----------------------+
               |                                           |
               |                                           v
               |                               +-----------------------+
               +-----------------------------> | Track My Submissions  |
                                               | (Pending / Approved)  |
                                               +-----------------------+
```

1. **Visit & Explore:** Guests can browse verified listings, search by keyword, or explore events happening near their coordinates.
2. **Account Sign-Up / Login:** Users sign up or authenticate through standard registration, Google Sign-In, or mobile OTP.
3. **Submit Food Information:** Authenticated users fill in an event submission form detailing food type, event category, venue, and timings.
4. **Submission Tracking:** Users monitor their submitted listings under "My Submissions" to track review statuses in real time.

---

## 6. Admin Flow

```
+------------------------------------------------------------------------+
|                      Admin / Staff Moderator Queue                     |
+------------------------------------------------------------------------+
                                   |
                                   v
             [ View Pending Event Details & Location Coordinates ]
                                   |
            +----------------------+----------------------+
            |                                             |
            v                                             v
     [ Approve Event ]                            [ Reject Event ]
            |                                             |
            v                                             v
  • Status = APPROVED                           • Status = REJECTED
  • Instantly visible in search                 • Mandatory reason logged
  • Displayed on Near-Me map                    • Contributor notified
  • Audit log recorded                          • Audit log recorded
```

1. **Queue Inspection:** Authorized moderators access the Admin Panel to inspect pending entries.
2. **Verification:** Admins verify event authenticity, timing plausibility, and category accuracy.
3. **Resolution:**
   - **Approve:** Publishes the event to the public directory immediately.
   - **Reject:** Marks the event as rejected with a mandatory feedback note for transparency.
4. **Audit Trail:** Every moderation decision is logged with staff credentials, timestamps, and action metadata.

---

## 7. Technology Stack

### Backend
- **Framework:** Python 3.10+ & Django 6.1
- **Architecture:** Model-View-Template (MVT) with modular Django applications (`accounts`, `food`, `locations`, `moderation`, `notifications`)
- **Authentication:** Django Auth, Google OAuth 2.0 (OpenID Connect), and SMS OTP authentication

### Database
- **Database Engine:** TiDB Cloud / MySQL-compatible distributed relational database
- **Connection Driver:** `pymysql` with TLS/SSL encryption via `certifi`
- **ORM:** Django Object-Relational Mapping with indexing on status, date, and geolocation fields

### Frontend & UI
- **Structure:** Semantic HTML5 templates
- **Styling:** Vanilla CSS3 design system (modern red palette: Primary `#dc2626`, Dark Neutral `#0f172a`, Light Neutral `#f8fafc`)
- **Scripting:** Modular ES6+ JavaScript for geolocation, modal handling, and dynamic requests
- **Icons & Visuals:** Inline SVG iconography with zero unicode emojis

### Mapping & Geolocation
- **Map Engine:** Leaflet.js (OpenStreetMap tile provider)
- **Distance Computation:** Haversine great-circle distance algorithm for proximity ranking
- **Directions:** Direct navigation routing via Google Maps

---

## 8. Project Structure

```
Dona/
│
├── manage.py                   # Django management CLI
├── requirements.txt            # Python project dependencies
├── .env.example                # Template for environment configuration
│
├── config/                     # Core application configuration
│   ├── __init__.py             # Database driver initialization & version check
│   ├── settings.py             # Django settings (TiDB, Auth, Templates, Static)
│   ├── urls.py                 # Root URL routing
│   └── wsgi.py                 # Production WSGI application
│
├── accounts/                   # Authentication & User Management
│   ├── models.py               # Custom User & OTP verification models
│   ├── views.py                # Email login, register, profile, OTP & OAuth
│   └── urls.py                 # Account routes (/login, /register, /otp, etc.)
│
├── food/                       # Food Events & Community Directory
│   ├── models.py               # FreeFoodEvent, Favorite, and Report models
│   ├── forms.py                # Event submission and reporting forms
│   ├── views.py                # Directory search, event details, submission flow
│   └── urls.py                 # Event discovery routes
│
├── locations/                  # Spatial Discovery & Geolocation
│   ├── services.py             # Haversine distance & recommendation algorithms
│   ├── views.py                # Location search and map integration
│   └── urls.py                 # Geolocation endpoints
│
├── moderation/                 # Admin Verification & Audit Engine
│   ├── views.py                # Moderator dashboard, approval & rejection views
│   └── urls.py                 # Moderation workflow routes
│
├── notifications/              # Event Updates & System Notifications
│   ├── models.py               # Notification and read tracking models
│   ├── services.py             # Notification dispatch and query services
│   └── views.py                # Notification API endpoints
│
├── templates/                  # Presentation Templates
│   ├── base.html               # Master layout with responsive navbar & tray
│   ├── accounts/               # Login, register, profile, and OTP templates
│   ├── food/                   # Event list, detail, home, and submission views
│   ├── moderation/             # Admin review queue and dashboard
│   └── notifications/          # Full notification history template
│
└── static/                     # Static Assets
    ├── css/                    # Component, page, and notification stylesheets
    └── js/                     # Application scripts, geolocation, and notifications
```

---

## 9. Future Scope

- **Community Feedback & Status Updates:** Allow attendees to confirm when food service begins or when items have run out in real time.
- **Organizer Verification Badges:** Verified badges for registered NGOs, community kitchens, and verified religious trusts.
- **Push Notification Subscriptions:** Native web push notifications alerting users when an approved event is published within a 5 km radius.
- **Dietary Filter Expansion:** Filters for Pure Vegetarian, Vegan, Halal, Jain food options, and allergen alerts.
- **Volunteer & Food Rescue Coordination:** Collaboration tools for surplus food recovery volunteers to minimize food wastage at large functions.

---

## 10. Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Access to a TiDB cluster or MySQL 8.0+ database
- Virtual environment tool (`venv`)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/dona-com.git
cd dona-com
```

### 2. Create and Activate a Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```ini
# Core Configuration
SECRET_KEY=your-secure-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
PLATFORM_NAME=Dona.Com

# TiDB / MySQL Database Configuration
TIDB_HOST=your-cluster-host.tidbcloud.com
TIDB_PORT=4000
TIDB_DATABASE=dona_db
TIDB_USER=your_cluster_user
TIDB_PASSWORD=your_cluster_password

# Authentication (Optional for local testing)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
OTP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-phone-number
```

### 5. Apply Database Migrations
```bash
python manage.py migrate
```

### 6. Create an Administrator Superuser
```bash
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit the running platform at: `http://127.0.0.1:8000/`

---

## 11. Screenshots

| Home & Nearby Discovery | Event Details & Directions |
| :---: | :---: |
| *[Add Screenshot: Homepage with Near-Me Search]* | *[Add Screenshot: Event Detail Card with Map]* |

| Community Event Submission | Admin Moderation Panel |
| :---: | :---: |
| *[Add Screenshot: Submit Free Food Event Form]* | *[Add Screenshot: Admin Review Queue & Approval]* |

---

## 12. Contributing

Contributions are welcome to help improve the platform for community meals and hunger relief:

1. **Fork the Repository**
2. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit Your Changes:**
   ```bash
   git commit -m "Add: description of your feature"
   ```
4. **Push to Your Branch:**
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** explaining your enhancements and testing steps.

---

## 13. License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for full details.

---

*Dona.Com — Connecting communities through shared meals and open food discovery.*
#   d o n a - c o m  
 