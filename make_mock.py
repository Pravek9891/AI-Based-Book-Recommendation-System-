import pandas as pd
import numpy as np

print("Generating mock books.pkl and popular.pkl...")

try:
    pt = pd.read_pickle('pt.pkl')
    titles = list(pt.index)
except Exception as e:
    print(f"Error reading pt.pkl: {e}")
    titles = [f"Book Number {i}" for i in range(1000)]

# mock books.pkl
books_data = {
    'Book-Title': titles,
    'Book-Author': ['Anonymous' for _ in titles],
    'Image-URL-M': ['https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=150&auto=format&fit=crop' for _ in titles]
}
books_df = pd.DataFrame(books_data)
books_df.to_pickle('books.pkl')
print(f"Created books.pkl with {len(titles)} titles.")

# mock popular.pkl
popular_titles = titles[:50] if len(titles) >= 50 else titles
popular_data = {
    'Book-Title': popular_titles,
    'Book-Author': ['Anonymous' for _ in popular_titles],
    'Image-URL-M': ['https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=150&auto=format&fit=crop' for _ in popular_titles],
    'num_ratings': [500 - i for i in range(len(popular_titles))],
    'avg_rating': [4.5 for _ in range(len(popular_titles))]
}
popular_df = pd.DataFrame(popular_data)
popular_df.to_pickle('popular.pkl')
print("Created popular.pkl.")
