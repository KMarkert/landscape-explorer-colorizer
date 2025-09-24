# Landscape Explorer Colorizer

This web application allows users to select a location on a map and view black and white aerial imagery from the 1950s. When a user clicks on the map, the application will fetch the image and send a request to a generative AI model to colorize it.

## Features

*   Interactive map with historical aerial imagery.
*   Click on the map to select a location and view the black and white image.
*   AI-powered colorization of the historical imagery.
*   Side-by-side comparison of the original and colorized images.
*   Download and share the colorized image.
*   Toggle the visibility and opacity of the historical imagery layer.

## Getting Started

### Prerequisites

*   Python 3.11+
*   `uv` package manager
*   Google Cloud project with the Earth Engine API enabled.
*   Google Maps API key.
*   Gemini API key.

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/landscape-explorer-colorizer.git
    cd landscape-explorer-colorizer
    ```

2.  Create a virtual environment and install the dependencies:
    ```bash
    uv sync
    ```

3.  Create a `.env` file in the root of the project and add your API keys:
    ```
    GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY"
    GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
    ```

4.  Run the application:
    ```bash
    uv run uvicorn main:app --reload
    ```

5.  Open your browser and navigate to `http://127.0.0.1:8000`.

## Deployment to Google Cloud Run

### Prerequisites

*   Google Cloud SDK installed and configured.
*   A Google Cloud project with the Cloud Run and Cloud Build APIs enabled.
*   Docker installed locally.

### Steps

1.  ** Create Artifact Registry repository **:
    ```bash
    gcloud artifacts repositories create landscape-explorer \
        --repository-format=docker \
        --location=us-central1
    ```
   

2.  **Build the Docker image** using Cloud Build:
    Update `cloudbuild.yaml` with the correct cloud project. Replace `YOUR_PROJECT_ID` with your Google Cloud project ID.

    ```bash
    gcloud builds submit --config cloudbuild.yaml 
    ```
    

2.  **Deploy the image** to Cloud Run:
    ```bash
    gcloud run deploy landscape-explorer \
        --image us-central1-docker.pkg.dev/YOUR-PROJECT-ID/landscape-explorer-colorizer/lce-image \
        --platform managed \
        --region us-central1 \
        --allow-unauthenticated \
        --set-env-vars GOOGLE_MAPS_API_KEY="YOUR_GOOGLE_MAPS_API_KEY" \
        --set-env-vars GOOGLE_API_KEY="YOUR_GEMINI_API_KEY" \
        --session-affinity
    ```
    Replace `YOUR_PROJECT_ID`, `YOUR_GOOGLE_MAPS_API_KEY`, and `YOUR_GEMINI_API_KEY` with your actual values.

3.  Once the deployment is complete, you will be provided with a URL to access your application.
