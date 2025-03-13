### ⚡ Setup & Installation

1️⃣ Replace SOURCE_DIR in .env to your store
```bash
touch .env
```

2️⃣ Create & Activate Virtual Environment

```bash
python3 -m venv venv        # Create a virtual environment
source venv/bin/activate    # Activate (MacOS/Linux)
```

3️⃣ Install Dependencies
```bash
pip install "fastapi[standard]" uvicorn
```

🚀 Run the FastAPI Server
```bash
uvicorn app.main:app --reload
```

### Deployment
### Use with pm2
```bash
pm2 start start.sh --name fastapi-app
```
### Use with docker
```bash
docker build -t fastapi-app .
```
```bash
docker run -d -p 8003:8003 fastapi-app
```