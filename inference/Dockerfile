FROM python:3.10-slim

WORKDIR /app

# Copy the requirements file from the inference folder
COPY inference/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the python code into an 'inference' folder inside the container
COPY inference/ ./inference/

# Open the port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "inference.infer_server:app", "--host", "0.0.0.0", "--port", "8000"]
