# LuxeWin Web App - Backend

The backend service for LuxeWin, a luxury raffle platform.

## Features
- User authentication
- Raffle management
- Purchase tracking
- Database migrations

## Setup

1. Clone the repository
2. Create and activate virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```
5. Initialize database:
   ```bash
   python scripts/init_db.py
   ```

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Access the interactive API docs at:
- Swagger UI: http://localhost:8000/docs
- Redoc: http://localhost:8000/redoc

## Testing

Run tests with:
```bash
pytest
```

## Deployment

The application is containerized using Docker. To deploy:

```bash
docker-compose up -d
```

## Contributing

1. Create a new branch
2. Make your changes
3. Run migrations if needed
4. Submit a pull request
