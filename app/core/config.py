import os
from dotenv import load_dotenv  # type: ignore[import-not-found]

load_dotenv()  # Load environment variables from .env file


DATABASE_URL = os.getenv("DATABASE_URL")

# RabbitMQ configuration
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
