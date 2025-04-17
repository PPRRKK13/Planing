
import os

def clean_file(file_path):
    with open(file_path, "rb") as file:
        content = file.read()

    # Remove non-printable characters
    clean_content = content.decode("utf-8", errors="ignore")

    clean_file_path = os.path.splitext(file_path)[0] + "_cleaned.py"
    with open(clean_file_path, "w", encoding="utf-8") as file:
        file.write(clean_content)

    print(f"Script cleaned and saved as '{clean_file_path}'")
