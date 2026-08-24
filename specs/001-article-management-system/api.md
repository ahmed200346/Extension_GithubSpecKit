# API Contract: Article Management System

**Version**: 1.0.0
**Base URL**: `/api`

## Endpoints

### 1. Articles
#### GET `/api/articles`
Retrieve a list of articles.
- **Query Parameters**:
  - `search` (optional): String to filter articles by title.
  - `category` (optional): Category ID to filter articles.
- **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "title": "Article Title",
      "price": 19.99,
      "category_name": "Electronics"
    }
  ]
  ```

#### GET `/api/articles/{id}`
Retrieve detailed information for a specific article.
- **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "title": "Article Title",
    "description": "Detailed description...",
    "price": 19.99,
    "category": { "id": 10, "name": "Electronics" },
    "created_at": "2026-08-11T10:00:00Z"
  }
  ```

#### POST `/api/articles`
Create a new article.
- **Request Body**:
  ```json
  {
    "title": "New Article",
    "description": "Description",
    "price": 25.00,
    "category_id": 10
  }
  ```
- **Response (201 Created)**: The created article object.
- **Response (400 Bad Request)**: Validation error message.

#### PUT `/api/articles/{id}`
Update an existing article.
- **Request Body**: Same as POST (partial updates allowed).
- **Response (200 OK)**: The updated article object.

#### DELETE `/api/articles/{id}`
Remove an article.
- **Response (204 No Content)**: Successfully deleted.

### 2. Categories
#### GET `/api/categories`
Retrieve all available categories for the filter dropdown.
- **Response (200 OK)**:
  ```json
  [
    { "id": 10, "name": "Electronics" },
    { "id": 11, "name": "Books" }
  ]
  ```
