from flask import Flask, request, jsonify
import sys

app = Flask(__name__)

# In-memory database
cookbook = []

@app.route('/recipes', methods=['GET'])
def get_recipes():
    return jsonify(cookbook)

@app.route('/recipes', methods=['POST'])
def add_recipe():
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        # CLI mode
        print("Enter recipe details:")
        title = input("Title: ")
        ingredients = input("Ingredients (comma-separated): ").split(',')
        steps = input("Steps (comma-separated): ").split(',')

        recipe = {
            "title": title.strip(),
            "ingredients": [ingredient.strip() for ingredient in ingredients],
            "steps": [step.strip() for step in steps]
        }
        cookbook.append(recipe)
        print("Recipe added via CLI!")
        sys.exit(0)
    else:
        # API mode
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid input, JSON data is required"}), 400

        title = data.get('title')
        ingredients = data.get('ingredients')
        steps = data.get('steps')

        if not title or not ingredients or not steps:
            return jsonify({"error": "All fields (title, ingredients, steps) are required"}), 400

        recipe = {
            "title": title,
            "ingredients": ingredients,
            "steps": steps
        }
        cookbook.append(recipe)
        return jsonify({"message": "Recipe added!", "recipe": recipe}), 201
    
    