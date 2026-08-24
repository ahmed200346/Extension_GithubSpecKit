# Data Model: Article Management System

**Date**: 2026-08-11
**Feature**: Article Management System

## Entities

### 1. Category
Represents a grouping for articles.
- **Fields**:
  - `id`: UUID / Integer (Primary Key)
  - `name`: String (Unique, Required)
- **Validation**:
  - Name must not be empty.

### 2. Article
Represents a product for sale.
- **Fields**:
  - `id`: UUID / Integer (Primary Key)
  - `title`: String (Required)
  - `description`: Text (Optional)
  - `price`: Decimal (Required, Must be > 0)
  - `category_id`: Integer (Foreign Key $\rightarrow$ Category.id, Required)
  - `created_at`: Timestamp (Default: now())
- **Validation**:
  - Title must be between 3 and 255 characters.
  - Price must be a positive number.
  - `category_id` must reference an existing category.

## Relationships
- **Category $\rightarrow$ Article**: One-to-Many (One category can contain multiple articles).
- **Article $\rightarrow$ Category**: Many-to-One (Each article must belong to exactly one category).

## State Transitions
- **Article Creation**: `Pending` $\rightarrow$ `Published` (upon successful validation and DB insertion).
- **Article Deletion**: `Published` $\rightarrow$ `Deleted` (Physical deletion from DB).
