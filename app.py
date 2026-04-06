import os
from flask import Flask, render_template, request, jsonify, session
import pickle
import numpy as np
import pandas as pd
import wikipedia
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    api_key = "dummy_deploy_key"
client = Groq(api_key=api_key)

# Loading the original dataframes and pickles
popular_df = pd.read_pickle('popular.pkl')
pt = pd.read_pickle('pt.pkl')
books = pd.read_pickle('books.pkl')
model = pd.read_pickle('model.pkl')

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_key_for_chatbot")

@app.route('/')
def index():
    genres = sorted(list(set(popular_df['category']))) if 'category' in popular_df.columns else []
    return render_template('index.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           image=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           rating=list(popular_df['avg_rating'].values),
                           genres=genres,
                           active_genre='All'
                           )

@app.route('/filter_books')
def filter_books():
    genre = request.args.get('genre', 'All')
    if 'category' not in popular_df.columns or genre == 'All':
        return jsonify(popular_df.to_dict(orient='records'))
    
    filtered = popular_df[popular_df['category'] == genre]
    return jsonify(filtered.to_dict(orient='records'))

@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

@app.route('/recommend_books', methods=['post'])
def recommend():
    user_input = request.form.get('user_input')
    
    if user_input not in pt.index:
        return render_template('recommend.html', data=None)

    # Use Scikit-Learn Model to dynamically predict top 5 neighbors
    book_index = np.where(pt.index == user_input)[0][0]
    distances, indices = model.kneighbors(pt.iloc[book_index, :].values.reshape(1, -1), n_neighbors=6)
    
    similar_items = [pt.index[i] for i in indices[0][1:]]

    data = []
    for book_title in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == book_title]
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Title'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Book-Author'].values))
        item.extend(list(temp_df.drop_duplicates('Book-Title')['Image-URL-M'].values))

        data.append(item)

    print(data)
    return render_template('recommend.html', data=data)

@app.route('/book/<path:title>')
def book_details(title):
    # Fetch book info
    temp_df = books[books['Book-Title'] == title]
    if temp_df.empty:
        return "Book Navigator Lost: Title not found in this sector.", 404
        
    book_df = temp_df.drop_duplicates('Book-Title').iloc[0]
    book = book_df.to_dict()

    # Recommendations
    recommendations = []
    if title in pt.index:
        book_index = np.where(pt.index == title)[0][0]
        distances, indices = model.kneighbors(pt.iloc[book_index, :].values.reshape(1, -1), n_neighbors=6)
        similar_items = [pt.index[i] for i in indices[0][1:]]
        
        for rec_title in similar_items:
            rec_df = books[books['Book-Title'] == rec_title]
            if not rec_df.empty:
                rec_df = rec_df.drop_duplicates('Book-Title').iloc[0]
                recommendations.append([rec_df['Book-Title'], rec_df['Book-Author'], rec_df['Image-URL-M']])

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
        book_match = None
        user_lower = user_message.lower()
        
        # Search for titles containing the user's message
        contains_match = books[books['Book-Title'].str.lower().str.contains(user_lower, na=False, regex=False)]
        
        if not contains_match.empty:
            book_match = contains_match.iloc[0]['Book-Title']
        
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
            return jsonify({'response': f"My AI sensors are offline right now because I don't have a valid API Key. To awaken my true intelligence, please add a valid GROQ_API_KEY to your `.env` file! For now, here's what I know from Wikipedia: {book_summary}"})

@app.route('/suggest')
def suggest():
    query = request.args.get('query', '')
    if len(query) < 2:
        return jsonify([])
    
    # Filter suggestions by pt.index to ensure we only suggest recommendable books
    query_lower = query.lower()
    matches = [title for title in pt.index if query_lower in title.lower()][:8]
    return jsonify(matches)

@app.route('/reset_chat', methods=['POST'])
def reset_chat():
    session.pop('current_book', None)
    session.pop('book_summary', None)
    return jsonify({'response': "Chat reset. Which book do you want to ask about?"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
