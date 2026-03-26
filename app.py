import os
from flask import Flask, render_template, request, jsonify, session
import pickle
import numpy as np
import wikipedia
from groq import Groq
from dotenv import load_dotenv

import mysql.connector.pooling

load_dotenv()
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Database Configuration with Connection Pooling
db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "password"),
    "database": os.getenv("MYSQL_DB", "book_recommender"),
    "charset": 'latin1'
}

db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="book_pool",
    pool_size=5,
    **db_config
)

def get_db_connection():
    return db_pool.get_connection()

# In-Memory Cache for Popular Books & Genres
GENRE_CACHE = {}
ALL_GENRES_CACHE = None

# Logic pickles still needed for matrix math
pt = pickle.load(open('pt.pkl','rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl','rb'))
# popular_df and books pkl are now replaced by MySQL for metadata

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_key_for_chatbot")

@app.route('/')
def index():
    global ALL_GENRES_CACHE
    selected_genre = request.args.get('genre', 'All')
    
    # 1. Get Genres (Cached)
    if ALL_GENRES_CACHE is None:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT category FROM popular_books WHERE category IS NOT NULL ORDER BY category")
        ALL_GENRES_CACHE = [row['category'] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
    
    # 2. Get Popular Books (Cached)
    if selected_genre not in GENRE_CACHE:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if selected_genre == 'All':
            cursor.execute("SELECT * FROM popular_books")
        else:
            cursor.execute("SELECT * FROM popular_books WHERE category = %s", (selected_genre,))
        GENRE_CACHE[selected_genre] = cursor.fetchall()
        cursor.close()
        conn.close()
    
    popular_books = GENRE_CACHE[selected_genre]

    return render_template('index.html',
                           book_name = [b['Book-Title'] for b in popular_books],
                           author=[b['Book-Author'] for b in popular_books],
                           image=[b['Image-URL-M'] for b in popular_books],
                           votes=[b['num_ratings'] for b in popular_books],
                           rating=[b['avg_rating'] for b in popular_books],
                           genres=ALL_GENRES_CACHE,
                           active_genre=selected_genre
                           )

@app.route('/filter_books')
def filter_books():
    genre = request.args.get('genre', 'All')
    
    if genre not in GENRE_CACHE:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if genre == 'All':
            cursor.execute("SELECT * FROM popular_books")
        else:
            cursor.execute("SELECT * FROM popular_books WHERE category = %s", (genre,))
        GENRE_CACHE[genre] = cursor.fetchall()
        cursor.close()
        conn.close()
    
    # Return JSON from cache
    return jsonify(GENRE_CACHE[genre])

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books',methods=['post'])
def recommend():
    user_input = request.form.get('user_input')
    
    # Check if book exists in index to prevent IndexError
    if user_input not in pt.index:
        return render_template('recommend.html', data=None)

    index = np.where(pt.index == user_input)[0][0]
    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

    data = []
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    for i in similar_items:
        book_title = pt.index[i[0]]
        # Fetch metadata from MySQL
        cursor.execute("SELECT `Book-Title`, `Book-Author`, `Image-URL-M` FROM books WHERE `Book-Title` = %s LIMIT 1", (book_title,))
        book_data = cursor.fetchone()
        
        if book_data:
            item = [
                book_data['Book-Title'],
                book_data['Book-Author'],
                book_data['Image-URL-M']
            ]
            data.append(item)

    cursor.close()
    conn.close()

    print(data)
    return render_template('recommend.html',data=data)

@app.route('/book/<path:title>')
def book_details(title):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Fetch book info
    cursor.execute("SELECT * FROM books WHERE `Book-Title` = %s LIMIT 1", (title,))
    book = cursor.fetchone()
    
    if not book:
        cursor.close()
        conn.close()
        return "Book Navigator Lost: Title not found in this sector.", 404

    # Recommendations (Similar to recommend function)
    recommendations = []
    if title in pt.index:
        idx = np.where(pt.index == title)[0][0]
        similar_items = sorted(list(enumerate(similarity_scores[idx])), key=lambda x: x[1], reverse=True)[1:5]
        
        for i in similar_items:
            rec_title = pt.index[i[0]]
            cursor.execute("SELECT `Book-Title`, `Book-Author`, `Image-URL-M` FROM books WHERE `Book-Title` = %s LIMIT 1", (rec_title,))
            rec_data = cursor.fetchone()
            if rec_data:
                recommendations.append([rec_data['Book-Title'], rec_data['Book-Author'], rec_data['Image-URL-M']])
    
    cursor.close()
    conn.close()

    # AI Summary
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a cosmic librarian. Provide a short, engaging summary and analysis of the book mentioned. Keep it within 3-4 sentences and use a premium, slightly mysterious tone."},
                {"role": "user", "content": f"Summarize the book '{title}' by {book['Book-Author']}."}
            ],
            temperature=0.7
        )
        summary = completion.choices[0].message.content
    except Exception as e:
        print("AI Error:", e)
        summary = "The cosmic record for this title is currently obscured by stellar dust. Please check back later."

    return render_template('book_details.html', book=book, recommendations=recommendations, summary=summary)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')
    
    if 'current_book' not in session:
        # Match book using MySQL for efficiency
        book_match = None
        user_lower = user_message.lower()
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Search for titles containing the user's message
        cursor.execute("SELECT `Book-Title` FROM books WHERE `Book-Title` LIKE %s LIMIT 1", (f"%{user_message}%",))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            book_match = result['Book-Title']
        
        if book_match:
            session['current_book'] = book_match
            try:
                summary = wikipedia.summary(book_match, sentences=3)
                session['book_summary'] = summary
            except Exception as e:
                session['book_summary'] = "No detailed summary available from Wikipedia."
            
            return jsonify({'response': f"Great! I know about '{book_match}'. What would you like to ask about this book?"})
        else:
            return jsonify({'response': "I couldn't find a book matching that name in our library. Please try giving me another book name."})
    else:
        # Answer question
        book_title = session['current_book']
        book_summary = session.get('book_summary', '')
        
        prompt = f"Context: You are a helpful AI assistant in a library web app. The user is asking about the book '{book_title}'.\n"
        if book_summary:
            prompt += f"Here is a summary of the book: {book_summary}\n"
        prompt += f"\nUser's question: {user_message}\n\nPlease answer the user's question based on the context and your general knowledge. Keep it concise, helpful, and conversational."
        
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": f"You are a helpful AI assistant in a library web app. The user is asking about the book '{book_title}'. {f'Context summary: {book_summary}' if book_summary else ''}"},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return jsonify({'response': completion.choices[0].message.content})
        except Exception as e:
            print("Error generating content:", e)
            return jsonify({'response': f"Groq Error: {str(e)}. Please check your GROQ_API_KEY in .env."})

@app.route('/suggest')
def suggest():
    query = request.args.get('query', '')
    if len(query) < 2:
        return jsonify([])
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Search for books that start with or contain the query
    cursor.execute("SELECT DISTINCT `Book-Title` FROM books WHERE `Book-Title` LIKE %s LIMIT 8", (f"%{query}%",))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    
    titles = [row['Book-Title'] for row in results]
    return jsonify(titles)

@app.route('/reset_chat', methods=['POST'])
def reset_chat():
    session.pop('current_book', None)
    session.pop('book_summary', None)
    return jsonify({'response': "Chat reset. Which book do you want to ask about?"})

if __name__ == '__main__':
    app.run(debug=True)
    # 
