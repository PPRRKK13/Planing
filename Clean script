
import re

# Read the original script
with open("app.py", "r", encoding="utf-8") as file:
    content = file.read()

# Remove non-printable characters
clean_content = re.sub(r'[^\x20-\x7E]', '', content)

# Write the cleaned content back to the file
with open("app_cleaned.py", "w", encoding="utf-8") as file:
    file.write(clean_content)

print("Script cleaned and saved as 'app_cleaned.py'")
