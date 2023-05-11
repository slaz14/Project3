# import libraries
from flask import Flask, render_template, request # pip install flask
import requests # pip install requests
import os # pip install os
import pandas as pd # pip install pandas 

app = Flask(__name__)

# Spoonacular API endpoint
api_endpoint = "https://api.spoonacular.com/recipes/complexSearch?apiKey=0abe62999be14e448d7b27fefd51916e"

# Get Spoonacular API key from environment variable
api_key = os.environ.get("SPOONACULAR_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # Load contacts from CSV file into a DataFrame
    try:
        contacts_df = pd.read_csv('contacts.csv')
    except FileNotFoundError:
        # If the CSV file doesn't exist, create an empty DataFrame
        contacts_df = pd.DataFrame({'Name': [], 'Email': [], 'Message': []})

    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Add new contact to pandas DataFrame
        new_contact = pd.DataFrame({'Name': [name], 'Email': [email], 'Message': [message]})
        contacts_df = contacts_df.append(new_contact, ignore_index=True)

        # Save pandas DataFrame to CSV file
        contacts_df.to_csv('contacts.csv', index=False)

        # Render success page
        return render_template('contact_success.html')

    # Render contact form page
    return render_template('contact.html')

@app.route('/favorites')
def favorites():
    # Load favorite recipes from CSV file into a DataFrame
    try:
        favorites_df = pd.read_csv('favorites.csv')
    except FileNotFoundError:
        # If the CSV file doesn't exist, create an empty DataFrame
        favorites_df = pd.DataFrame({'Title': [], 'Image': [], 'URL': [], 'Ingredients': []})

    # Convert DataFrame to a list of dictionaries
    favorites = favorites_df.to_dict('records')

    # Render favorites template
    return render_template('favorites.html', favorites=favorites)


@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    # Load favorite recipes from CSV file into a DataFrame
    try:
        favorites_df = pd.read_csv('favorites.csv')
    except FileNotFoundError:
        # If the CSV file doesn't exist, create an empty DataFrame
        favorites_df = pd.DataFrame({'Title': [], 'Image': [], 'URL': [], 'Ingredients': []})

    # Get recipe title from request body
    title = request.form['title']

    # Check if recipe is already in favorites
    if title in favorites_df['Title'].tolist():
        return "Recipe already in favorites"

    # Load recipes from Spoonacular API
    response = requests.get(api_endpoint, params={'apiKey': api_key, 'query': title})
    data = response.json()

    # Check if there are any results
    if not data['results']:
        return "No results found"

    # Get the first recipe in the results
    recipe = data['results'][0]

    # Get the recipe source URL, or use a default URL
    if 'sourceUrl' in recipe:
        url = recipe['sourceUrl']
    else:
        url = 'https://spoonacular.com/'

    # Get the recipe ingredients, or use an empty list
    if 'usedIngredients' in recipe and 'missedIngredients' in recipe:
        ingredients = [i['name'] for i in recipe['usedIngredients'] + recipe['missedIngredients']]
    else:
        ingredients = []

    # Add recipe to favorites DataFrame
    new_favorite = pd.DataFrame({'Title': [recipe['title']], 'Image': [recipe['image']], 'URL': [url], 'Ingredients': [ingredients]})
    favorites_df = favorites_df.append(new_favorite, ignore_index=True)

    # Save favorites DataFrame to CSV file
    favorites_df.to_csv('favorites.csv', index=False)

    return "Recipe added to favorites"


@app.route('/recommendations', methods=['POST'])
def recommendations():
    # Get ingredients and query from form
    ingredients = request.form.get('ingredients')
    query = request.form.get('query')

    # Build API query parameters
    params = {
        'apiKey': api_key,
        'addRecipeInformation': 'true',
        'fillIngredients': 'true',
        'instructionsRequired': 'true',
        'number': '10'
    }

    # Add ingredients or query parameter to API query
    if ingredients:
        params['includeIngredients'] = ingredients.split(', ')
    elif query:
        params['query'] = query
    else:
        return "Please provide ingredients or a query"

    # Call Spoonacular API
    response = requests.get(api_endpoint, params=params)

    # Parse response JSON
    data = response.json()

    # Check if 'results' key exists in JSON
    if 'results' not in data:
        return "No results found"

    # Get recipe results
    results = []
    for recipe in data['results']:
        # Get the recipe title
        title = recipe['title']

        # Get the recipe image URL
        if recipe['image'].startswith('http'):
            image = recipe['image']
        else:
            image = f"https://spoonacular.com/recipeImages/{recipe['image']}"

        # Get the recipe source URL
        url = recipe['sourceUrl']

        # Get the recipe ingredients
        ingredients = [i['name'] for i in recipe['usedIngredients'] + recipe['missedIngredients']]

        # Add the recipe data to the results list
        results.append({'title': title, 'image': image, 'url': url, 'ingredients': ingredients})

    # Check if results list is empty
        if not results:
            return "No recipes found for the given ingredients."

        return render_template('recommendations.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
