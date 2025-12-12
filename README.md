# Reddit Real-time AI Analyzer

A Python application that streams Reddit comments in real-time and classifies them as "Human" or "AI" using a Hugging Face transformer model (DeBERTa Zero-Shot).

## Features
- **Real-time Streaming**: Connects to Reddit API via PRAW.
- **AI Classification**: Uses `cross-encoder/nli-deberta-v3-small` (or similar) to detect AI-generated content.
- **Live Dashboard**: Streamlit UI with running statistics and charts.
- **Dockerized**: Easy to deploy.

## Setup

### Prerequisites
- Python 3.9+ or Docker
- Reddit API Credentials ([Create here](https://www.reddit.com/prefs/apps))

### Installation

1. Clone the repository.
2. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your REDDIT_CLIENT_ID, REDDIT_SECRET, and USER_AGENT
   ```

### Enabling GPU Support (Optional but Recommended)
Standard `pip install torch` often installs the CPU-only version. To use your NVIDIA GPU:

1. Uninstall current torch:
   ```bash
   pip uninstall torch torchvision torchaudio
   ```
2. Install CUDA-enabled version (adjust `cu121` to your CUDA version):
   ```bash
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

### Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   streamlit run main.py
   ```

### Running with Docker

1. Build the image:
   ```bash
   docker build -t reddit-ai-analyzer .
   ```
2. Run the container (pass env vars):
   ```bash
   docker run --env-file .env -p 8501:8501 reddit-ai-analyzer
   ```
3. Open [http://localhost:8501](http://localhost:8501).

## Usage
1. Enter a subreddit name (e.g., `askreddit`, `technology`) in the sidebar.
2. Click **Start Streaming**.
3. Watch the latest comments appearing with their classification!

## License
MIT
