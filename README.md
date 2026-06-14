#  Community Recovery Portal

A high-end, decoupled **Lost & Found Management System** tailored for the KG College campus. This portal transitions from the basic "form-submission" model to a state-of-the-art **Interactive Dashboard** experience, ensuring students and staff can recover items with maximum efficiency and minimal friction.

---

## Project Vision
Built as a solo high-speed MVP to demonstrate technical excellence. The portal focuses on high-readability (Clean White Theme), strict data integrity (Django REST), and a snappy, reactive user interface (React.js).

### Key Architectural Pillars
- **Decoupled Symmetry**: React frontend communicates with Django REST Framework via stateless JWT.
- **Hierarchical Governance**: 3-tier Role-Based Access Control (Admin, Staff, User).
- **Automated Hygiene**: Image compression at the source and automated 30-day data purging.

---

##  Features & Logic

###  Role-Based Access Control (RBAC)
| Role | Landing Page | Key Permissions |
| :--- | :--- | :--- |
| **Admin** | `/dashboard` | System Analytics, User Promotion, Global Data Access |
| **Staff** | `/dashboard` | Security Handover Authority, Resolution Management |
| **User** | `/report-center` | Personal Reporting, Public Feed Access, Self-Resolution |

###  Smart Handover & Resolution
- **Multi-State Handover**: Reports track if an item is `Left at Location`, `With Finder`, or `Handed to Security`.
- **The Security Gate**: Once marked as "Handed to Security", the item becomes **locked** for regular users. Only **Staff** can verify the identity and mark it as `RESOLVED`.
- **Dynamic Forms**: UI intelligently reveals security details only when the "Security Handover" status is selected.

###  High-Performance Media Pipeline
- **Auto-Compression**: Every image is intercepted on upload, resized to **1024px**, and re-encoded at **70% quality** to save server bandwidth.
- **Auto-Purge**: A background management command clears physical files older than 30 days while keeping DB records for archival history.

---

##  UI/UX Specifications
- **Palette**: `Pure White (#ffffff)` / `Slate Light (#f8fafc)` / `Electric Blue (#3b82f6)`.
- **Components**: Glass-morphism sidebar, crisp metric cards, dual-stream vertical feeds.
- **Icons**: Lucide-React & FontAwesome 6.

---

##  System Architecture

```bash
Lost-Found-Portal/
├── backend/                  # Django REST Framework Engine
│   ├── core/                 # JWT Auth & Security Configuration
│   ├── users/                # Identity & RBAC Logic
│   ├── items/                # Business Logic & Image Processing
│   └── media/                # Managed Storage (Compressed Images)
├── frontend/                 # React + Vite Cockpit
│   ├── src/pages/            # Dashboard, ReportCenter, Feed
│   ├── src/components/       # ProtectedRoute, Sidebar, CustomCards
│   └── src/api/              # Axios Interceptors (JWT Handling)
└── venv/                     # Python 3.11 Environment
```

---

##  Quick Start

### 1. Engine Setup (Backend)
```bash
# Enter project root
cd Lost-Found-Portal

# Setup Environment
python -m venv venv
# Windows:
venv\Scripts\activate

# Install & Migrate
pip install -r backend/requirements.txt
cd backend
python manage.py migrate
```

### 2. Cockpit Setup (Frontend)
```bash
cd ../frontend
npm install
npm run dev
```

### 3. Identity Setup (Admin)
The portal comes with a pre-configured Master Admin:
- **URL**: `http://localhost:8000/admin`
- **Username**: `admin`
- **Password**: `admin123`

---

##  Maintenance Commands
Keep your server lean by running the daily purge:
```bash
python backend/manage.py purge_images
```

---

##  Developer Context
- **Lead Architect**: Jeremiah (Solo Project)
- **Target Audience**: KG College Campus
- **Mentorship**: For Sathish Sir's Review

---
> [!IMPORTANT]
> This portal is configured for local development. For production deployment, ensure `DEBUG=False` and update `CORS_ALLOWED_ORIGINS` in `settings.py`.

---
