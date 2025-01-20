# Property Scraper API Documentation

This API provides endpoints for scraping property data from various real estate websites including Rightmove, Zoopla, and OnTheMarket.

## Endpoints

### Single Property Scraping

#### Rightmove Property

```http
GET /rightmove/
```

Query Parameters:

- `url` (required): URL of the Rightmove property listing

Response:

- `200 OK`: Successfully scraped property data
- `400 Bad Request`: Missing URL parameter

#### Zoopla Property

```http
GET /zoopla/
```

Query Parameters:

- `url` (required): URL of the Zoopla property listing

Response:

- `200 OK`: Successfully scraped property data
- `400 Bad Request`: Missing URL parameter

#### OnTheMarket Property

```http
GET /onthemarket/
```

Query Parameters:

- `url` (required): URL of the OnTheMarket property listing

Response:

- `200 OK`: Successfully scraped property data
- `400 Bad Request`: Missing URL parameter

### Asynchronous Scraping Job

#### Start Scraping Job

```http
POST /start-scraping/
```

Request Body:

```json
{
  "url": "string",
  "source": "string",
  "callback_url": "string",
  "property_id": "string",
  "task_id": "string",
  "phone_number": "string"
}
```

Required Fields:

- `url`: Property listing URL
- `source`: Source website (rightmove/zoopla/onthemarket)
- `callback_url`: URL to receive scraping results
- `phone_number`: Contact phone number

Optional Fields:

- `property_id`: Identifier for the property
- `task_id`: Identifier for the task

Response:

- `202 Accepted`: Job started successfully
  ```json
  {
    "job_id": "string"
  }
  ```
- `400 Bad Request`: Missing required fields

#### Get Scraping Job Data

```http
GET /scraping-job/{job_id}/
```

Path Parameters:

- `job_id`: ID of the scraping job

Response:

- `200 OK`: Scraping completed successfully
  ```json
  {
    "data": {
      "address": "string",
      "price": "string",
      "bedrooms": "integer",
      "bathrooms": "integer",
      "size": "string",
      "house_type": "string",
      "agent": "string",
      "description": "string",
      "time_on_market": "string",
      "features": "array",
      "listing_type": "string",
      "images": "array",
      "floorplans": "array"
    }
  }
  ```
- `202 Accepted`: Scraping still in progress
- `404 Not Found`: Job or property not found

### Standalone Scraping

#### One-Time Scrape

```http
POST /scrape-once/
```

Request Body:

```json
{
  "url": "string",
  "source": "string" // Optional, defaults to "rightmove"
}
```

Required Fields:

- `url`: Property listing URL

Optional Fields:

- `source`: Source website (rightmove/zoopla/onthemarket)

Response:

- `200 OK`: Successfully scraped property data
  ```json
  {
    "message": "Scrape successful.",
    "scraped_data": {
      // Property data object
    }
  }
  ```
- `400 Bad Request`: Missing URL
- `500 Internal Server Error`: Scraping failed

## Error Responses

All endpoints may return the following error responses:

- `400 Bad Request`: When required parameters are missing or invalid
- `404 Not Found`: When requested resources don't exist
- `500 Internal Server Error`: When server-side errors occur

Error response format:

```json
{
  "error": "Error message description"
}
```
