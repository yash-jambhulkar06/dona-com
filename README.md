# Dona.Com — Location-Based Free Food Discovery Platform

[![Django](https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Database](https://img.shields.io/badge/Database-TiDB%20%7C%20MySQL-00758F?style=for-the-badge&logo=mysql&logoColor=white)](https://www.pingcap.com/tidb/)
[![Leaflet](https://img.shields.io/badge/Maps-Leaflet%20%7C%20OpenStreetMap-199900?style=for-the-badge&logo=leaflet&logoColor=white)](https://leafletjs.com/)
[![UI](https://img.shields.io/badge/Design-Red%20Theme%20%7C%20Emoji--Free-DC2626?style=for-the-badge)](https://github.com/yash-jambhulkar06/dona-com)
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

**Dona.Com** is a location-based free-food discovery platform. It allows users to discover and share places or events where free food is being served, such as weddings, religious/community meals, langar, mahaprasad, birthdays, public events, and other occasions.

Users can submit information about a free-food event or place. The submitted information goes through an admin review process before it becomes publicly visible. This helps maintain the quality and reliability of listings.

The platform uses location-based functionality to help users find nearby free-food opportunities and provides recommendations based on their current location.

---

## 2. What Does "Dona" Mean?

**"Dona"** is a local slang word used to describe the act of going somewhere to eat free food without being invited or without permission. For example, someone may hear about a wedding, community meal, religious event, birthday, or other function where food is being served and go there to eat even though they were not invited.

The name is intentionally informal and represents the core idea of the platform: **discovering places and events where free food is available**.

### Respectful & Ethical Platform Purpose
> **Important Note on Ethical Discovery:**  
> While the name draws its inspiration from local slang, **Dona.Com does not encourage or endorse trespassing, illegal entry, property intrusion, or disrupting private gatherings**.  
> The platform is strictly intended for discovering **publicly accessible, community-shared, or otherwise legitimately available free-food opportunities**—including religious community kitchens, langars, mahaprasad, charitable food drives, and open celebration feasts. All submissions are vetted by platform administrators to ensure community respect and event appropriateness.

---

## 3. How Dona.Com Works

Dona.Com connects community members and people seeking meals through a verified, multi-step discovery process:

```
[ User / Contributor ]
          │
          ▼
 Submits Free-Food Event Details
 (Title, Category, Venue Address, Serving Hours, Coordinates)
          │
          ▼
 [ Admin Review Queue ]
 (Verification of Event Authenticity, Timings & Location)
   │                           │
   ▼                           ▼
[ Approved ]              [ Rejected ]
   │                           │
   ▼                           ▼
Live on Public Directory   Feedback Reason Logged
& Location-Based Search    (Sent to Contributor)
   │
   ▼
[ Community Seekers & Nearby Users ]
 - Nearby Recommendations
 - Distance & Category Filtering
 - Real-Time Directions & Timings
```

1. **Submission:** An authenticated user submits an event or venue offering free food, specifying serving hours, venue coordinates, and event category.
2. **Admin Verification:** The entry is placed into a secure review queue with a `PENDING` status, invisible to public visitors until reviewed.
3. **Approval & Publication:** Once verified by administrators, the event status changes to `APPROVED` and appears instantly on the live discovery directory and location-based recommendation engine.
4. **Discovery & Navigation:** Nearby users discover the active event, check remaining serving hours, and navigate to the venue.

---

## 4. Features

Dona.Com delivers a complete set of production-grade features built for reliability and real-world utility:

- **User Registration and Authentication:** Secure email/password account creation, session management, and profile controls.
- **Google Sign-In:** One-click OAuth 2.0 / OpenID Connect authentication via Google Cloud.
- **Mobile OTP Authentication:** Passwordless phone number verification powered by production SMS providers (Twilio / Fast2SMS) with rate limits and SHA-256 token hashing.
- **Submit Free-Food Events/Places:** Intuitive submission forms capturing venue names, full addresses, event dates, start/end serving times, food details, coordinates, dietary preferences, and surplus rescue flags.
- **Structured Event Categories:** Clear event categorization:
  - `Wedding`
  - `Birthday`
  - `Religious Event` (Mahaprasad, Langar, Bhandara)
  - `Community Meal` (NGO relief, charitable kitchens)
  - `Other` (Public gatherings, cultural feasts)
- **Community Live Status:** Real-time confirmation system allowing visitors and attendees to confirm serving status ("Food is currently serving" or "Food finished") with live counters and immediate status updates without page reload.
- **Verified Organizer Badges:** Official verification marks with distinctive badges for registered NGOs, community kitchens, religious trusts (Temples, Gurudwaras, Mosques), and verified community contributors.
- **5 km Proximity Push Alerts:** Native browser Web Notification API push alerts notifying nearby users when a verified free-food event is published within 5 km of their location.
- **Dietary Preference Filtering & Allergen Indicators:** Dedicated multi-dietary filters and badges for Pure Vegetarian, Vegan, Jain Food (no onion/garlic/root veg), Halal, and allergen notices (nut-free, gluten-free, dairy-free).
- **Surplus Food Recovery Network:** Dedicated portal for celebration feasts, banquet halls, and weddings to connect with volunteer food rescue networks (like Robin Hood Army, Roti Bank) for urgent pickup, preventing food waste.
- **Admin Approval/Rejection System:** Dedicated moderator dashboard allowing staff to review submissions, inspect coordinates, verify organizer badges, approve live listings, or reject with explanatory feedback.
- **Location-Based Food Discovery:** Live spatial queries calculating distance between the user's location and event venues using the Haversine formula.
- **Nearby Free-Food Recommendations:** Intelligent sorting that prioritizes events that are currently serving food ("Available Now") and starting soon.
- **Event Details and Location:** Full event profile pages displaying verified addresses, serving windows, menu notes, dietary tags, live status confirmations, and direct turn-by-turn navigation links.
- **User-Friendly Interface:** Clean, intuitive navigation ensuring fast access across both mobile and desktop screens.
- **Red-Themed Modern UI:** Custom-tailored design system using a modern, warm red palette (`#dc2626`) for strong visual clarity and brand identity.
- **No Emojis in Application UI:** Consistent, professional aesthetic utilizing clean SVG iconography and modern typography without unicode emojis.
- **Proper Working Production Functionality:** Real database persistence on TiDB Cloud, working REST endpoints, and zero test/mock shortcuts.

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

1. **Discover:** Users explore verified meals nearby, filtering by category or sorting by closest distance.
2. **Authenticate:** Users register or log in via email, Google Sign-In, or mobile OTP.
3. **Contribute:** Users submit details about open free-food venues or occasions.
4. **Track:** Contributors view the status of their submitted events in real time.

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
  • Visible in public search                    • Mandatory reason logged
  • Featured on Near-Me recommendations         • Contributor notified
  • Full audit log recorded                     • Full audit log recorded
```

1. **Queue Review:** Moderators access the Admin Panel to review newly submitted free-food listings.
2. **Quality Check:** Admins verify location accuracy, venue legitimacy, and serving schedules.
3. **Decision:**
   - **Approve:** The listing goes live on the platform instantly.
   - **Reject:** The listing is rejected with a recorded explanation.
4. **Audit Logging:** Every administrative action is permanently recorded in moderation audit logs.

---

## 7. Technology Stack

### Backend
- **Language & Framework:** Python 3.10+ / Django 6.1
- **Architecture:** Model-View-Template (MVT) with isolated apps (`accounts`, `food`, `locations`, `moderation`, `notifications`)
- **Authentication:** Django Authentication, Google OAuth 2.0 (OpenID Connect), and SMS OTP (Twilio / Fast2SMS)

### Database
- **Database Engine:** TiDB Cloud / MySQL-compatible distributed relational database
- **Connection & Security:** `pymysql` with TLS/SSL encryption via `certifi`
- **ORM:** Django ORM with indexes on status, category, date, and spatial coordinates

### Frontend & Styling
- **Structure:** Semantic HTML5 templates
- **Design System:** Custom Vanilla CSS3 with a modern red color scheme (Primary `#dc2626`, Dark `#0f172a`, Light `#f8fafc`)
- **Interactive Scripting:** Vanilla ES6+ JavaScript for geolocation, modals, and dynamic interactions
- **Iconography:** Inline SVG icons with zero unicode emojis

### Mapping & Geolocation
- **Map Library:** Leaflet.js with OpenStreetMap tiles
- **Proximity Calculations:** Haversine formula implemented in Python for fast distance filtering
- **Directions:** Google Maps navigation integration

---

## 8. Project Structure

```
Dona/
│
├── manage.py                   # Django CLI management script
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables template
│
├── config/                     # Project configuration
│   ├── __init__.py             # Database wrapper initialization & version patches
│   ├── settings.py             # Settings (TiDB, Auth, Templates, Static)
│   ├── urls.py                 # Primary URL router
│   └── wsgi.py                 # WSGI application entrypoint
│
├── accounts/                   # Authentication & User Management
│   ├── models.py               # Custom User with Verified Organizer Badges and profiles
│   ├── views.py                # Login, registration, profile, Google & OTP views
│   └── urls.py                 # Authentication routes
│
├── food/                       # Food Events, Directory & Recovery
│   ├── models.py               # FreeFoodEvent, Favorite, Report, CommunityLiveStatus, FoodRescueClaim
│   ├── forms.py                # Event submission, issue reports, and FoodRescueClaimForm
│   ├── views.py                # Directory, detail, submission, live status voting, surplus recovery
│   └── urls.py                 # Event directory and surplus recovery routes
│
├── locations/                  # Spatial Discovery & Geolocation
│   ├── services.py             # Haversine distance, dietary filters, and recommendation engine
│   ├── views.py                # Location search and map endpoints
│   └── urls.py                 # Location routes
│
├── moderation/                 # Admin Verification & Moderation
│   ├── views.py                # Staff dashboard, approve/reject, organizer verification, audit logs
│   └── urls.py                 # Moderation workflow routes
│
├── notifications/              # Real-Time Notification System & Proximity Alerts
│   ├── models.py               # Notification, NotificationRead, and ProximitySubscriber models
│   ├── services.py             # Dispatch engine, 5 km proximity push matcher, device location services
│   └── views.py                # Notification API, read state, and proximity registration endpoints
│
├── templates/                  # Presentation Templates
│   ├── base.html               # Master layout with clean navbar, proximity alert banner, mobile drawer
│   ├── accounts/               # Login, register, profile with verified badges, and OTP templates
│   ├── food/                   # Event list, detail with live voting, form, surplus recovery portal
│   ├── moderation/             # Admin review queues, organizer verification, and dashboards
│   └── notifications/          # Notification history template
│
└── static/                     # Static Assets
    ├── css/                    # Modern red theme, component badges, and notification styles
    └── js/                     # Application scripts, geolocation, and Web Notification proximity push
```

---

## 9. Implemented Scope & Future Roadmap

All 5 core enhancements identified in the project scope have been **fully implemented in production**:

### 1. Community Live Status (Implemented)
- **Real-Time Serving Verification:** Visitors and attendees at event venues can confirm whether food is actively serving or finished in real time.
- **Dynamic Vote Metrics:** Calculates serving confirmations vs. finished alerts over an active 4-hour window, displaying real-time badges ("Community Verified: Serving Food" or "Community Alert: Food Finished").
- **AJAX Live Interaction:** Users can cast confirmation votes with instant feedback without page reloads, backed by session-based rate limiting to prevent spam.

### 2. Verified Organizer Badges (Implemented)
- **Official Verification Marks:** Dedicated verification system distinguishing registered NGOs, community kitchens, religious trusts (Temples, Gurudwaras, Mosques, Churches), and verified volunteers.
- **Visual Shield Badging:** Verified badges with organization names prominently displayed across event cards, event profiles, directory filters, and user account profiles.
- **Admin Verification Controls:** Moderators can inspect and grant official organizer credentials during event reviews or from staff moderation queues.

### 3. Proximity Push Notifications (Implemented)
- **5 km Geolocation Matching:** Automatic distance calculation comparing newly published events against registered subscriber coordinates using the Haversine formula.
- **Native Web Notification API:** Browser push alerts notifying nearby users when a verified free-food event is published within 5 km of their location.
- **Proximity Device Registration:** Dedicated API (`/notifications/api/register-proximity/`) registering user GPS coordinates with customizable alert radii.

### 4. Dietary Preferences & Allergen Indicators (Implemented)
- **Multi-Dietary Categorization:** Support for Pure Vegetarian, Vegan (100% plant-based), Jain Food (no root vegetables, onion, or garlic), Halal prepared meals, and mixed diets.
- **Allergen Indicators:** Dedicated fields capturing notices for nut-free, gluten-free, and dairy-free options.
- **Enhanced Directory Filters:** One-click filter pills on the home page and event directory enabling seekers to instantly find meals tailored to their dietary requirements.

### 5. Surplus Food Recovery Network (Implemented)
- **Celebration Waste Prevention:** Dedicated Surplus Food Rescue hub (`/food/surplus-recovery/`) connecting weddings, banquet halls, and large functions with excess food to volunteer food rescue networks.
- **Volunteer Rescue Claims:** Volunteers and NGOs (e.g. Robin Hood Army, Roti Bank) can claim excess food batches for urgent pickup via interactive claim modals.
- **Organizer Notification Loop:** Organizers receive immediate real-time notifications with volunteer contact information and estimated arrival times.

---

### Next-Generation Roadmap
- **WhatsApp & Telegram Broadcasts:** Direct messaging bot integrations for receiving 5 km radius food alerts via WhatsApp and Telegram.
- **Native Mobile Apps:** Cross-platform iOS and Android applications with background GPS geofencing.
- **Machine Learning Demand Prediction:** Predictive analysis matching historical attendance to forecast meal shortages or surpluses.
- **Offline-First PWA:** Progressive Web App service worker caching for seamless offline viewing during network drops.

---

## 10. Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Access to a TiDB Cloud cluster or MySQL 8.0+ database
- Git and virtual environment tool (`venv`)

### 1. Clone the Repository
```bash
git clone https://github.com/yash-jambhulkar06/dona-com.git
cd dona-com
```

### 2. Set Up a Virtual Environment
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

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```ini
# Application Settings
SECRET_KEY=your-secure-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
PLATFORM_NAME=Dona.Com

# TiDB Database Configuration
TIDB_HOST=gateway01.ap-northeast-1.prod.aws.tidbcloud.com
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

### 6. Create an Admin Superuser
```bash
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Open your browser at: `http://127.0.0.1:8000/`

---

## 11. Screenshots

| Home & Location Discovery | Event Details & Venue Location |
| :---: | :---: |
| *[Add Screenshot: Homepage with Proximity Search]* | *[Add Screenshot: Event Detail Card with Map View]* |

| Submit Free-Food Event | Admin Moderation Panel |
| :---: | :---: |
| *[Add Screenshot: Event Submission Form]* | *[Add Screenshot: Staff Approval Queue & Actions]* |

---

## 12. Contributing

Contributions are welcome to make free-food discovery more accessible:

1. **Fork the Repository**
2. **Create a Feature Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit Your Changes:**
   ```bash
   git commit -m "Add: descriptive summary of feature"
   ```
4. **Push to Your Branch:**
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** with a detailed explanation of changes.

---

## 13. License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

*Dona.Com — Connecting communities through shared meals and open food discovery.*