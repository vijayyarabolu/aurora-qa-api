# Aurora Question Answering API

## Purpose

This project implements a simple FastAPI-based question answering service for the Aurora member messages API. It exposes an `/ask` endpoint that accepts a natural-language question and attempts to infer an appropriate answer based on member messages fetched from the public Aurora API.

## Running Locally

1. Create and activate a virtual environment (optional but recommended).
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the API with uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at `http://localhost:8000`.

## Example Request

```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'
```

Example response:

```json
{ "answer": "..." }
```

You can also open `http://localhost:8000/ui` in a browser for a simple HTML interface.

## Deployed Service (GCP Cloud Run)

The service is deployed to Google Cloud Run and publicly accessible at:

- Base URL: `https://aurora-qa-api-942188892759.europe-west1.run.app`

Health check:

```bash
curl https://aurora-qa-api-942188892759.europe-west1.run.app/
```

Aurora API connectivity test:

```bash
curl https://aurora-qa-api-942188892759.europe-west1.run.app/test
```

Example question:

```bash
curl -X POST "https://aurora-qa-api-942188892759.europe-west1.run.app/ask" \
  -H "Content-Type: application/json" \
  -d '{"question": "When is Layla planning her trip to London?"}'
```

## Deployment Instructions

You can deploy this FastAPI service using any platform that supports Python web applications. Two common options are:

### Option 1: Docker + Cloud Run / Container Platform

1. Create a `Dockerfile` that runs `uvicorn main:app --host 0.0.0.0 --port 8080`.
2. Build and push the container image to a container registry.
3. Deploy the container image to your preferred platform (e.g., Google Cloud Run, AWS Fargate, Azure Container Apps), exposing port 8080 publicly.
4. Configure health checks on `/` and use `POST /ask` as the main API endpoint.

### Option 2: Managed Python Hosting (e.g., Railway, Render, Heroku)

1. Create the appropriate config files for your chosen provider (e.g., `Procfile` for Heroku).
2. Set the start command to:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

3. Deploy the code via GitHub integration or by pushing directly.
4. Once deployed, your public URL will expose the same endpoints (`/`, `/ask`, `/test`, `/ui`).

## Bonus: Design Notes

- **Rule-based matching:** The current implementation uses simple rule-based heuristics. It detects a likely member name from the question using a regular expression and filters messages for that user. It then searches for topic keywords (e.g., `trip`, `car`, `restaurant`, `booking`, `payment`) within those messages to find the most relevant answer.
- **Alternative 1 – Vector search / embeddings:** A more advanced approach would be to transform each message into an embedding vector (using an embedding model) and then compute similarity between the question and messages. This would allow more flexible semantic matching across topics and phrasing.
- **Alternative 2 – RAG with LLM:** Another option is to combine vector search with a large language model: retrieve the top-K relevant messages using a vector store and then prompt an LLM to infer a concise answer using only those messages as context.
- **Alternative 3 – Structured schema extraction:** We could preprocess messages to extract structured entities (e.g., trips, cars, restaurants) with associated attributes (dates, counts, locations). Questions would then be parsed into structured queries against this derived knowledge base, improving answer precision.

## Bonus: Data Insights / Anomalies

During analysis of the Aurora messages data, several potential anomalies or inconsistencies one might look for include:

- **Inconsistent user names:** The same member may appear with slightly different spellings or formats (e.g., `Vikram Desai` vs `Vikram S. Desai`), which can make simple name-based matching less reliable.
- **Conflicting details:** Separate messages for the same user may mention different dates or locations for what appears to be the same trip or event, suggesting that the latest message may be more accurate than earlier ones.
- **Ambiguous entities:** Some messages may refer to generic entities (e.g., "the car", "the trip") without clear references to counts or specific dates, making it harder to answer questions like "How many cars" or "When is the trip" precisely.
- **Missing or partial information:** Certain users may have very few messages or messages that never mention the requested topic at all. In such cases, the system falls back to returning the most recent message, but a production system might instead respond with a clarification or an explicit "I don't know".

These observations help motivate more robust approaches (like embeddings or structured extraction) to improve recall and precision beyond simple rule-based matching.
