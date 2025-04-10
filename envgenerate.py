# generate_env.py

env_content = """API_ID=
API_HASH=
OWNER_ID=
SUDO_USERS=  # space-separated user IDs like: 12345 67890
BOT_TOKEN=
MONGO_URI=
DB_NAME=Guardify
SPOILER_MODE=True
LOGGER=False
BOT_NAME=Guardify
SUPPORT_ID=-1002440907656
"""

with open(".env", "w") as f:
    f.write(env_content)

print(".env file created successfully with sample variables.")
