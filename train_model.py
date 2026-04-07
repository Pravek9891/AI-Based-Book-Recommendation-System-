import pandas as pd
import numpy as np
import pickle
import os
from sklearn.neighbors import NearestNeighbors

print("Loading data...")
# Try to figure out where the user placed the CSV files
if os.path.exists('archive/Ratings.csv'):
    ratings_path = 'archive/Ratings.csv'
    books_path = 'archive/Books.csv'
elif os.path.exists('../archive/Ratings.csv'):
    ratings_path = '../archive/Ratings.csv'
    books_path = '../archive/Books.csv'
elif os.path.exists('../../archive/Ratings.csv'):
    ratings_path = '../../archive/Ratings.csv'
    books_path = '../../archive/Books.csv'
else:
    print("ERROR: Could not find 'archive/Ratings.csv' or 'archive/Books.csv'.")
    print("Please download the Kaggle Book Recommendation dataset and place the CSVs in an 'archive' folder.")
    exit()

ratings = pd.read_csv(ratings_path)
books = pd.read_csv(books_path, low_memory=False)

print("Merging...")
ratings_with_name = ratings.merge(books, on='ISBN')

print("Filtering users (min 150 interactions to save memory)...")
x = ratings_with_name.groupby('User-ID').count()['Book-Rating']
padhe_likhe_users = x[x > 150].index
filtered_rating = ratings_with_name[ratings_with_name['User-ID'].isin(padhe_likhe_users)]

print("Filtering books (min 30 interactions to save memory)...")
y = filtered_rating.groupby('Book-Title').count()['Book-Rating']
famous_books = y[y >= 30].index
final_ratings = filtered_rating[filtered_rating['Book-Title'].isin(famous_books)]

print("Creating pivot table 'pt'...")
pt = final_ratings.pivot_table(index='Book-Title', columns='User-ID', values='Book-Rating')
pt.fillna(0, inplace=True)
pt = pt.astype(np.float32) # Instantly halves matrix RAM footprint
print("Shape of pt:", pt.shape)

print("Training Machine Learning Model (NearestNeighbors)...")
# Using Scikit-Learn's NearestNeighbors for item-based collaborative filtering
model = NearestNeighbors(n_neighbors=6, algorithm='brute', metric='cosine')
model.fit(pt.values)

print("Generating popular books...")
num_rating_df = ratings_with_name.groupby('Book-Title').count()['Book-Rating'].reset_index()
num_rating_df.rename(columns={'Book-Rating':'num_ratings'}, inplace=True)

avg_rating_df = ratings_with_name.groupby('Book-Title').mean(numeric_only=True)['Book-Rating'].reset_index()
avg_rating_df.rename(columns={'Book-Rating':'avg_rating'}, inplace=True)

popular_df = num_rating_df.merge(avg_rating_df, on='Book-Title')
popular_df = popular_df[popular_df['num_ratings'] >= 250].sort_values('avg_rating', ascending=False).head(50)
popular_df = popular_df.merge(books, on='Book-Title').drop_duplicates('Book-Title')[['Book-Title', 'Book-Author', 'Image-URL-M', 'num_ratings', 'avg_rating']]

print("Saving Scikit-Learn Model and Dataframes...")
pickle.dump(popular_df, open('popular.pkl', 'wb'))
pickle.dump(pt, open('pt.pkl', 'wb'))
pickle.dump(books, open('books.pkl', 'wb'))
pickle.dump(model, open('model.pkl', 'wb')) # <--- Exporting the actual ML Model!

print("Done.")
