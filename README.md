# CYO Backend API

A production-ready FastAPI application with JWT-based authentication.

## Features

- **JWT Authentication**: Stateless access tokens with refresh tokens
- **Secure Password Hashing**: Using bcrypt
- **Modular Architecture**: Clean separation of concerns
- **Database Persistence**: SQLAlchemy with SQLite (easily switchable to PostgreSQL)
- **Cookie-based Refresh Tokens**: HttpOnly, Secure, SameSite cookies
- **Production Settings**: Environment-based configuration

## Project Structure

```
app/
├── auth/           # Authentication utilities
├── config.py       # Application settings
├── database.py     # Database configuration
├── dependencies/   # FastAPI dependencies
├── models/         # SQLAlchemy models
├── routers/        # API endpoints
└── schemas/        # Pydantic schemas
main.py             # Application entry point
.env                # Environment variables
```

## Installation

1. Install dependencies:
```bash
uv sync
```

2. Place the GCP service account JSON file in the backend folder (e.g., `cyoproject-476108-ff9e7996bc22.json`).

3. Configure environment variables in `.env`:
```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DEBUG=false
DATABASE_URL=sqlite:///./app.db
GCP_SERVICE_ACCOUNT_FILE=/path/to/your/cyoproject-476108-ff9e7996bc22.json
GCP_BUCKET_NAME=your-gcp-bucket-name
```

## Running the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user (auto-login)
- `POST /auth/login` - Login user
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user

# File server
```bash
docker run -d -p 4443:4443 -v /tmp/gcs:/data fsouza/fake-gcs-server -scheme http
```
### Users
- `GET /users/profile` - Get user profile (protected)

## Production Deployment

1. Set strong `SECRET_KEY`
2. Use PostgreSQL for database
3. Enable HTTPS
4. Configure proper CORS if needed
5. Add rate limiting
6. Use environment variables for all sensitive data

## Development

- API documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`