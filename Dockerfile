# Use the official Streamlit image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy your app code
COPY . .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the Streamlit port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "Inserimento.py", "--server.port=8501", "--server.address=0.0.0.0"]
