import pandas as pd
import random

# Load the pickle file
df = pd.read_pickle('popular.pkl')

# Group the 50 titles into some basic genres. For simplicity, we assign specific genres to known books,
# and random ones to the rest, or just use a simple string matching.

def categorize(title):
    t = title.lower()
    if 'harry potter' in t or 'hobbit' in t or 'magic' in t or 'lotr' in t or 'tolkien' in t:
        return 'Fantasy'
    elif 'vampire' in t or 'twilight' in t or 'dracula' in t:
        return 'Fantasy'
    elif 'murder' in t or 'mystery' in t or 'detective' in t or 'firm' in t or 'pelican' in t or 'time' in t:
        return 'Mystery/Thriller'
    elif 'love' in t or 'notebook' in t or 'romance' in t or 'wedding' in t:
        return 'Romance'
    elif 'mockingbird' in t or 'gatsby' in t or '1984' in t or 'catcher' in t or 'animal farm' in t:
        return 'Classic Fiction'
    else:
        # Assign deterministically based on string hash for the others
        genres = ['Contemporary Fiction', 'Mystery/Thriller', 'Sci-Fi', 'Romance', 'Young Adult']
        return genres[hash(title) % len(genres)]

df['category'] = df['Book-Title'].apply(categorize)

# Save back to popular.pkl
df.to_pickle('popular.pkl')
print(f"Added 'category' column with values: {df['category'].unique()}")
