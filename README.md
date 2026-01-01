# Create Python Env.
python -m venv .venv

# Run venv
.venv\Scripts\Activate.ps1

# Download packages
pip install crewai crewai[tools] crewai[gemini] browserbase redis google.generativeai
pip install fastapi uvicorn crewai crewai-tools requests python-dotenv


# Download Fast API
pip install fastapi
pip install "fastapi[standard]"

# Run Fast API
fastapi dev main.py 

# This will run perfectly
uvicorn main:app --reload 