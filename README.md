# Multi-Tenant Backend Service

## Overview
A high-performance, scalable backend service built with FastAPI that implements multi-tenancy using MongoDB. This service allows for isolated data storage per organization while maintaining a single application instance. It includes JWT-based authentication and optional Redis caching for improved performance.

## Features
- **Organization Management**
  - Create, retrieve, update, and delete organizations
  - Dynamic MongoDB collection creation per organization
  - Isolated data storage for each tenant

- **Authentication & Authorization**
  - Secure admin login with JWT
  - Role-based access control
  - Token refresh mechanism

- **Performance**
  - Optional Redis caching layer
  - Asynchronous database operations
  - Request rate limiting

## Tech Stack
- **Backend**: Python 3.9+, FastAPI
- **Database**: MongoDB 5.0+, Motor (async MongoDB driver)
- **Authentication**: JWT (JSON Web Tokens)
- **Caching**: Redis (optional)
- **Validation**: Pydantic v2
- **API Documentation**: Swagger UI, ReDoc

## Installation

### Prerequisites
- Python 3.9 or higher
- MongoDB 5.0+
- Redis 6.0+ (optional, for caching)
- pip (Python package manager)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone [https://github.com/yourusername/multi_tenant_backend.git](https://github.com/santhru135/Multi_tenant_backend.git)
   cd multi_tenant_backend