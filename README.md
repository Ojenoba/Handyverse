# handyverse

# Handyverse

Handyverse is a modern platform connecting users with skilled artisans for various services.  
It features user and artisan registration, authentication, profile management, and a real-time chat system.

## Features

- User and Artisan registration & login
- Profile management
- Artisan discovery and contact
- Real-time messaging/chat between users and artisans
- Responsive, modern UI

## Tech Stack

- **Backend:** Flask (Python), Flask-Login, Flask-CORS, SQLAlchemy
- **Frontend:** React + Vite (recommended for SPA)
- **Database:** SQLite (default), easily switchable to PostgreSQL/MySQL
- **Authentication:** JWT or Flask-Login sessions

## Getting Started

### Backend (Flask API)

1. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
2. Set up your `.env` file and database.
3. Run the backend:
    ```sh
    flask run
    ```

### Frontend (React + Vite)

1. Install dependencies:
    ```sh
    npm install
    ```
2. Start the frontend:
    ```sh
    npm run dev
    ```

## API Endpoints

- `POST /api/register` — Register a new user/artisan
- `POST /api/login` — Login and receive a JWT token
- `GET /api/messages?partner_id=USER_ID` — Get chat messages with a user
- `POST /api/send_message/<partner_id>` — Send a message

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](LICENSE)
