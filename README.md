# Handyverse

Handyverse is a modern, interactive web platform that connects users with skilled artisans for various services. Users can post jobs, browse artisans, send messages, and manage their profiles, while artisans can showcase their skills, apply for jobs, and communicate with clients. The app features a beautiful, colorful UI and is built with Flask, SQLAlchemy, and modern frontend technologies.

---

## Features

- **User & Artisan Registration/Login:**  
  Secure authentication for both users and artisans.

- **User Dashboard:**  
  - Post jobs with location and budget.
  - Manage posted jobs and view applicants.
  - Favorite artisans for quick access.
  - Receive notifications when artisans apply.

- **Artisan Dashboard:**  
  - Create and manage artisan profiles.
  - List skills, location, and portfolio.
  - Browse and apply for jobs.
  - Receive notifications for job status.

- **Job Board:**  
  - Browse all posted jobs.
  - View job details and apply (if artisan).
  - Job status management.

- **Messaging System:**  
  - Secure, real-time messaging between users and artisans.
  - Chat interface with notifications.

- **Notifications:**  
  - In-app notifications for job applications, messages, and status updates.

- **Profile Management:**  
  - Upload profile pictures.
  - Edit personal and artisan details.

- **Beautiful, Responsive UI:**  
  - Colorful cards, badges, and buttons.
  - Toast notifications and interactive elements.
  - Mobile-friendly design.

---

## Tech Stack

<<<<<<< HEAD
- **Backend:** Flask (Python), Flask-Login, Flask-CORS, SQLAlchemy
=======
- **Backend:** Python, Flask, Flask-Login, Flask-WTF, SQLAlchemy
- **Frontend:** HTML5, CSS3 (custom, with gradients and animations), JavaScript, [FontAwesome](https://fontawesome.com/)
>>>>>>> 4bc484e (Initial commit: Handyverse app)
- **Database:** SQLite (default), easily switchable to PostgreSQL/MySQL
- **Other:** Flask-Migrate, Flask-CORS, WTForms

---

## Setup & Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/handyverse.git
    cd handyverse
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    venv\Scripts\activate   # On Windows
    # or
    source venv/bin/activate  # On Mac/Linux
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**
    - Copy `.env.example` to `.env` and set your secret key and database URI.

5. **Initialize the database:**
    ```bash
    flask db upgrade
    ```

<<<<<<< HEAD
=======
6. **Run the app:**
    ```bash
    python run.py
    ```
    The app will be available at [http://127.0.0.1:5000](http://127.0.0.1:5000)
>>>>>>> 4bc484e (Initial commit: Handyverse app)

---

## Usage

- **Register** as a user or artisan.
- **Users:** Post jobs, browse artisans, send messages, and manage favorites.
- **Artisans:** Create a profile, apply for jobs, and chat with users.
- **Admins:** (Optional) Manage users, jobs, and site content.

---

## Screenshots

> _Add screenshots of the dashboard, job board, messaging, and profile pages here for visual reference._

---

## Customization

- **Colors & Styles:**  
  Edit `app/static/styles.css` for branding and color changes.

- **Database:**  
  Default is SQLite. To use PostgreSQL or MySQL, update `SQLALCHEMY_DATABASE_URI` in `.env`.

- **Email/Notifications:**  
  Integrate Flask-Mail or other services for email notifications.

---

## Contributing

1. Fork the repository.
2. Create your feature branch: `git checkout -b feature/YourFeature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/YourFeature`
5. Open a pull request.

---

## License

This project is licensed under the MIT License.

---

## Credits

- [Flask](https://flask.palletsprojects.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [FontAwesome](https://fontawesome.com/)
- [WTForms](https://wtforms.readthedocs.io/)

---

## Contact

For support or inquiries, please open an issue or contact the maintainer at dev.richard.adesanya@gmail.com
