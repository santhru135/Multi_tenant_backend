# Multi-Tenant Backend Service

## 📋 Overview
A high-performance, scalable backend service built with FastAPI that implements multi-tenancy using MongoDB. This service provides isolated data storage per tenant while maintaining a single application instance. It features JWT-based authentication, role-based access control, and optional Redis caching for enhanced performance.

## ✨ Features
- **Multi-tenancy**
  - Database-per-tenant architecture
  - Automatic tenant isolation
  - Dynamic database routing

- **User Management**
  - User registration and authentication
  - Role-based access control (Superadmin, Tenant Admin, User)
  - JWT token authentication with refresh tokens

- **Tenant Management**
  - Create, retrieve, update, and delete tenants
  - Tenant-specific database creation
  - Tenant-specific admin user creation

- **Security**
  - Password hashing with bcrypt
  - Secure JWT token handling
  - CORS protection
  - Environment-based configuration

- **Performance**
  - Asynchronous database operations
  - Optional Redis caching
  - Efficient request handling

## 🛠 Tech Stack
- **Backend Framework**: FastAPI (Python 3.9+)
- **Database**: MongoDB 5.0+ with Motor (async driver)
- **Authentication**: JWT with OAuth2
- **Caching**: Redis 6.0+ (optional)
- **Data Validation**: Pydantic v2
- **API Documentation**: Swagger UI, ReDoc
- **Environment Management**: python-dotenv
- **Testing**: pytest (recommended)

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- MongoDB 5.0+ (running locally or remotely)
- Redis 6.0+ (optional, for caching)
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/santhru135/Multi_tenant_backend.git
   cd Multi_tenant_backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # Linux/MacOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```env
   # Application
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   
   # MongoDB
   MONGODB_URL=mongodb://localhost:27017
   MASTER_DB_NAME=master_tenant
   
   # Redis (optional)
   REDIS_URL=redis://localhost:6379/0
   
   # CORS (comma-separated origins, or * for all)
   BACKEND_CORS_ORIGINS=*
   ```

   Generate a secure secret key:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

## 🏃‍♂️ Running the Application

1. **Start the development server**
   ```bash
   uvicorn main:app --reload
   ```

2. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🔧 API Usage

### Authentication

#### Register a new user
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "SecurePassword123!",
  "org_name": "Example Organization",
  "is_superadmin": true
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

grant_type=&username=admin%40example.com&password=SecurePassword123%21
```

#### Refresh Token
```http
POST /api/v1/auth/refresh-token
Content-Type: application/json

{
  "refresh_token": "your-refresh-token"
}
```

### Tenant Management (Superadmin Only)

#### Create a new tenant
```http
POST /api/v1/tenants/
Authorization: Bearer your-access-token
Content-Type: application/json

{
  "name": "New Tenant",
  "domain": "new-tenant",
  "email": "tenant-admin@example.com",
  "admin_name": "Tenant Admin",
  "admin_password": "Admin@123"
}
```

#### Get tenant details
```http
GET /api/v1/tenants/{tenant_id}
Authorization: Bearer your-access-token
```

## 🧪 Testing

Run the test suite with:
```bash
pytest tests/
```

## 🚀 Deployment

### Production Setup
1. Set `DEBUG=False` in `.env`
2. Configure a production-ready WSGI server (e.g., Gunicorn with Uvicorn workers)
3. Set up a reverse proxy (Nginx, Apache)
4. Configure SSL/TLS

### Docker (Optional)
```bash
docker-compose up -d
```

## 📚 Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)
- [JWT Introduction](https://jwt.io/introduction/)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👏 Acknowledgments

- FastAPI for the amazing async framework
- MongoDB for the flexible NoSQL database
- All contributors who helped improve this project