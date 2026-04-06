import os

if __name__ == '__main__':
    with open(".env", "w") as f:
        f.write("GROQ_API_KEY=dummy_key_please_replace\n")
        f.write("FLASK_SECRET_KEY=cosmic_librarian_secret\n")
