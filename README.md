# Finance Data Processing & Access Control Backend

## Overview

This project is a backend system for a finance dashboard that manages users, financial records, and analytics with role-based access control.

It is designed to demonstrate backend architecture, API design, data modeling, access control, and data processing logic in a clean and maintainable way.

---

## Features

### User & Role Management

* User registration and login
* Role assignment: **Admin, Analyst, Viewer**
* User status management (active/inactive)
* Role-based access restrictions

### Financial Records

* Create income/expense records
* Update and delete records (soft delete)
* Filter records by:

  * Type (income/expense)
  * Category
  * Date range
* Pagination support

### Dashboard & Analytics

* Total income
* Total expenses
* Net balance
* Category-wise breakdown
* Recent transactions
* Monthly and weekly trends

### Access Control

* Viewer → Read-only access
* Analyst → Read + analytics
* Admin → Full access (users + records)

### Validation & Error Handling

* Input validation using Pydantic
* Meaningful error responses
* Proper HTTP status codes
* Global exception handling

---

## Architecture

The project follows a modular and scalable structure:

* **Routes** → Handle HTTP requests and responses
* **Services** → Contain business logic and processing
* **Models / Schemas** → Define data structure and validation
* **Database Layer** → Handles persistence (SQLite)
* **Middleware / Dependencies** → Authentication and role-based authorization

### Request Flow

1. User logs in and receives a JWT token
2. Token is sent in request headers:

   ```
   Authorization: Bearer <token>
   ```
3. Token is validated for authenticity
4. User role is extracted
5. Role is checked before executing protected actions

This ensures secure and controlled access to all resources.

---

## Tech Stack

* **Language**: Python 3.12
* **Framework**: FastAPI
* **Database**: SQLite (file-based, zero setup)
* **Authentication**: JWT (`python-jose`) + `bcrypt`
* **Validation**: Pydantic v2
* **Server**: Uvicorn
* **API Docs**: Swagger UI (`/docs`)

---

## Access Control Design

Role-based access control is implemented using FastAPI dependencies.

* JWT token is decoded to identify the user
* Each route enforces minimum role requirements
* Unauthorized access returns `403 Forbidden`

### Permission Matrix

| Action                           | Viewer | Analyst | Admin |
| -------------------------------- | ------ | ------- | ----- |
| View financial records           | ✅      | ✅       | ✅     |
| Access dashboard summaries       | ❌      | ✅       | ✅     |
| Create / update / delete records | ❌      | ❌       | ✅     |
| Manage users                     | ❌      | ❌       | ✅     |

---

## API Reference

### Auth

| Method | Endpoint       | Description           |
| ------ | -------------- | --------------------- |
| POST   | /auth/register | Register a new user   |
| POST   | /auth/login    | Login and receive JWT |

**Register Example**

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "password": "secret123",
  "role": "admin"
}
```

---

### Users (Admin Only)

| Method | Endpoint    | Description        |
| ------ | ----------- | ------------------ |
| GET    | /users      | List all users     |
| GET    | /users/{id} | Get user by ID     |
| PATCH  | /users/{id} | Update role/status |

---

### Financial Records

| Method | Endpoint      | Description                         | Min Role |
| ------ | ------------- | ----------------------------------- | -------- |
| GET    | /records      | List records (filters + pagination) | Viewer   |
| GET    | /records/{id} | Get single record                   | Viewer   |
| POST   | /records      | Create record                       | Admin    |
| PATCH  | /records/{id} | Update record                       | Admin    |
| DELETE | /records/{id} | Soft delete record                  | Admin    |

**Query Parameters**

* `page`, `limit`
* `type` (income/expense)
* `category`
* `date_from`, `date_to`

---

### Dashboard (Analyst + Admin)

| Method | Endpoint                  | Description                   |
| ------ | ------------------------- | ----------------------------- |
| GET    | /dashboard/summary        | Income, expenses, net balance |
| GET    | /dashboard/categories     | Category-wise totals          |
| GET    | /dashboard/recent         | Recent activity               |
| GET    | /dashboard/trends/monthly | Monthly trends                |
| GET    | /dashboard/trends/weekly  | Weekly trends                 |

---

## Setup Instructions

```bash
git clone https://github.com/shubhampatilsp11/finance-backend.git
cd finance-backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run server
python -m uvicorn main:app --host 0.0.0.0 --port 3000 --reload
```

---

## Environment Variables

Create a `.env` file:

```env
JWT_SECRET=your_secret_key
```

---

## Testing the API

* Open Swagger UI:

  ```
  http://localhost:3000/docs
  ```
* Use built-in interface to test endpoints

---

## Assumptions & Tradeoffs

* SQLite chosen for simplicity and zero setup
* Role assignment during registration is allowed for testing
* Soft deletes used for auditability
* Dashboard endpoints return aggregated data without pagination
* All timestamps stored in UTC

---

## Future Improvements

* Refresh tokens & advanced authentication
* Role hierarchy & fine-grained permissions
* Full-text search
* Unit & integration tests
* API rate limiting
* Deployment (Docker + cloud hosting)

---

## Author

**Shubham Patil**

---

## Conclusion

This project demonstrates a structured backend system with:

* Clean API design
* Proper separation of concerns
* Secure role-based access control
* Efficient data processing

It is designed to reflect real-world backend development practices while keeping the implementation clear and maintainable.
