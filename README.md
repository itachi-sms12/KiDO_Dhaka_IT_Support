## 🧾 **Support Ticket System**

A streamlined, full-stack web application for managing internal and external support requests.  
It allows users to raise, track, and resolve tickets with role-based access and real-time updates — optimized for enterprise helpdesk operations.

---

### 🚀 **Features**
- 🎫 Create, assign, and resolve support tickets  
- 🧑‍💼 Role-based authentication (Admin, Agent, User)  
- 📎 File attachments for each ticket  
- 💬 Commenting and status updates  
- 🔔 Email or in-app notifications (optional integration)  
- 📊 Dashboard for analytics and KPIs  

---

### 🏗️ **Tech Stack**
| Layer | Technology |
|-------|-------------|
| Backend | **Django / Python 3.x** |
| Frontend | **HTML5, Bootstrap, JavaScript** |
| Database | **SQLite / PostgreSQL (configurable)** |
| Version Control | **Git + GitHub** |
| Deployment | **Gunicorn / Nginx / Docker (optional)** |

---

### ⚙️ **Setup Instructions**

1. **Clone the repository**
   ```bash
   git clone https://github.com/Senthil-vsk/support-ticket-system.git
   cd support-ticket-system
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   source venv/bin/activate   # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   python manage.py runserver
   ```

6. Open in your browser:  
   👉 `http://127.0.0.1:8000/`

---

### 👥 **User Roles**
| Role | Permissions |
|------|--------------|
| **Admin** | Full control over users, tickets, and categories |
| **Agent** | Can view and resolve assigned tickets |
| **User** | Can create and track personal tickets |

---

### 🧩 **Project Structure**
```
support_ticket_system/
├── manage.py
├── requirements.txt
├── .gitignore
├── tickets/              # Core ticket management app
├── users/                # Authentication and role management
├── templates/            # HTML templates
├── dashboard/            # Dashboard setup
└── media/                # Uploaded files
```

---

### 🔐 **Environment Variables**
Create a `.env` file in the root directory:
```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_password
```

---

### 📦 **Deployment**
For production-grade deployment:
- Configure `ALLOWED_HOSTS`  
- Use Gunicorn + Nginx or deploy via Docker  
- Set `DEBUG=False`

---

### 🧠 **Future Enhancements**
- API endpoints (REST with DRF)  
- Ticket SLA tracking  
- Reporting and analytics dashboard  
- Integration with Slack / Microsoft Teams  

---

### 📜 **License**
This project is proprietary software and not open source.
All rights are reserved by Senthil Kumar.
Unauthorized copying, modification, or distribution of this software,
in whole or in part, is strictly prohibited.

Access is granted only to licensed clients who have obtained
explicit permission or a valid commercial agreement from Senthil Kumar.

For business inquiries or licensing requests, contact:
📧 via GitHub → https://github.com/Senthil-vsk
🌐 via Email  → senthilsk8716@gmail.com

---

### 👨‍💻 **Author**
**Senthil Kumar**  
Software Developer | Automation & Backend Engineering  
📧 *Reach me on GitHub → [Senthil-vsk](https://github.com/Senthil-vsk),*
🌐 Email → senthilsk8716@gmail.com

