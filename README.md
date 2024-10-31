# Ancient Medical Texts Analysis App

A comprehensive application for analyzing ancient medical texts using modern NLP and LLM technologies.

## Features

- **Lexical Value Management**: Create, update, and analyze lexical values from ancient medical texts
- **LLM-Powered Analysis**: Analyze terms using AWS Bedrock (Claude-3) with contextual understanding
- **Redis Caching**: Efficient caching system for improved performance
- **Modern Frontend**: React-based UI with Tailwind CSS and DaisyUI

## Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+
- AWS Account with Bedrock access

## Setup

### 1. Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/Atlogit/atlomy_chat.git
cd atlomy_chat
```

2. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Node.js dependencies:
```bash
cd next-app
npm install
```

### 2. Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Configure your environment variables in `.env`:
   - Database settings
   - AWS Bedrock credentials
   - Redis connection details
   - LLM parameters

### 3. AWS Bedrock Setup

1. Ensure you have AWS credentials with Bedrock access
2. Configure your AWS credentials in `.env`:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

### 4. Database Setup

1. Create the PostgreSQL database:
```bash
createdb amta
```

2. Run database migrations:
```bash
alembic upgrade head
```

### 5. Redis Setup

1. Install Redis:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

2. Start Redis:
```bash
# Ubuntu/Debian
sudo systemctl start redis

# macOS
brew services start redis
```

## Running the Application

1. Start the FastAPI backend:
```bash
uvicorn app.run_server:app --reload
```

2. Start the Next.js frontend:
```bash
cd next-app
npm run dev
```

3. Access the application at `http://localhost:3000`

## Using the Components

### Lexical Value Management

1. Navigate to the Lexical Values section
2. Use the interface to:
   - Create new lexical values
   - Update existing entries
   - View and manage translations
   - Add categories and references

### LLM Analysis

1. Navigate to the Term Analysis section
2. Enter a term to analyze
3. Add relevant contexts:
   - Text passages
   - Author information
   - References
4. Choose analysis options:
   - Stream response (real-time updates)
   - Token count monitoring
5. View and save analysis results

## Testing

1. Run backend tests:
```bash
pytest tests/
```

2. Run frontend tests:
```bash
cd next-app
npm test
```

3. Run integration tests:
```bash
pytest tests/test_integration.py
```

## Caching Behavior

- Text data: 24-hour TTL
- Search results: 30-minute TTL
- Analysis results: 1-hour TTL

Cache invalidation occurs automatically when:
- Lexical values are updated
- New analyses are generated
- Token limits are exceeded

## Troubleshooting

### Common Issues

1. AWS Bedrock Connection:
   - Verify AWS credentials
   - Check region settings
   - Ensure Bedrock model access

2. Redis Connection:
   - Verify Redis is running
   - Check connection settings
   - Monitor memory usage

3. Database Issues:
   - Check connection string
   - Verify migrations
   - Monitor connection pool

### Logs

- Backend logs: `logs/app.log`
- Redis logs: System default location
- Frontend logs: Browser console

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

ISC License - See LICENSE file for details
