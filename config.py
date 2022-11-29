import os

from dotenv import dotenv_values


project_path = os.path.join(os.path.dirname(__file__), '.env')
config = dotenv_values(project_path)
