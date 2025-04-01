from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
import random
import string
import sqlite3

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'votre_clé_secrète')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Supprimer la base de données existante si elle existe
if os.path.exists('bar.db'):
    print("Suppression de l'ancienne base de données...")
    os.remove('bar.db')

db = SQLAlchemy(app)

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(8), unique=True, nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    base = db.Column(db.String(100))
    alcohol = db.Column(db.String(100))
    taste_types = db.Column(db.String(200), nullable=False)
    mood = db.Column(db.String(50))
    cocktail_name = db.Column(db.String(100))
    recipe = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)

# Créer la base de données et les tables
with app.app_context():
    print("Création de la base de données...")
    db.create_all()
    
    # Vérifier que la table a été créée correctement
    try:
        conn = sqlite3.connect('bar.db')
        cursor = conn.cursor()
        
        # Vérifier toutes les tables existantes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables existantes:", tables)
        
        # Vérifier spécifiquement la table orders
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders';")
        orders_table = cursor.fetchone()
        
        if not orders_table:
            print("La table 'orders' n'a pas été créée")
            # Créer la table manuellement si nécessaire
            cursor.execute("""
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number VARCHAR(8) UNIQUE NOT NULL,
                    customer_name VARCHAR(100) NOT NULL,
                    base VARCHAR(100),
                    alcohol VARCHAR(100),
                    taste_types VARCHAR(200) NOT NULL,
                    mood VARCHAR(50),
                    cocktail_name VARCHAR(100),
                    recipe TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    completed BOOLEAN DEFAULT 0
                )
            """)
            conn.commit()
            print("Table 'orders' créée manuellement")
        else:
            print("Table 'orders' trouvée:", orders_table)
            
        conn.close()
    except Exception as e:
        print(f"Erreur lors de la vérification/création de la base de données: {str(e)}")
        raise

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_order_number():
    # Génère un numéro de commande unique de 8 caractères
    while True:
        order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Order.query.filter_by(order_number=order_number).first():
            return order_number

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            customer_name = request.form.get('customer_name')
            alcohol_type = request.form.get('alcohol_type')
            choose_specific = request.form.get('choose_specific')
            specific_spirit = request.form.get('specific_spirit')
            base = request.form.get('base')
            taste_types = request.form.getlist('taste_types')
            mood = request.form.get('mood')

            # Définir les types d'alcools spécifiques selon la catégorie
            alcohol_specifics = {
                'blanc': ['Vodka', 'Gin', 'Rhum blanc', 'Tequila', 'Mezcal'],
                'brun': ['Whisky', 'Rhum brun', 'Cognac', 'Armagnac', 'Bourbon'],
                'liqueur': ['Amaretto', 'Baileys', 'Cointreau', 'Grand Marnier', 'Kahlua'],
                'amere': ['Campari', 'Aperol', 'Fernet', 'Suze', 'Amer Picon']
            }

            # Sélectionner les alcools pour les cocktails
            if choose_specific == 'yes' and specific_spirit:
                # Si un alcool spécifique est choisi, l'utiliser pour tous les cocktails
                selected_spirits = [specific_spirit] * 3
            else:
                # Sinon, sélectionner 3 types d'alcools différents
                available_spirits = alcohol_specifics.get(alcohol_type, ['Spiritueux'])
                selected_spirits = random.sample(available_spirits, min(3, len(available_spirits)))

            # Générer 3 propositions de cocktails
            cocktails = []
            for spirit in selected_spirits:
                # Générer la recette avec OpenAI
                prompt = f"""Crée une recette de cocktail avec les spécifications suivantes :
                - Type d'alcool principal : {spirit}
                - Types de goût : {', '.join(taste_types)}
                - Humeur : {mood if mood else 'Non spécifiée'}

                Format de la recette :
                🍸 Nom du cocktail
                🥃 Ingrédients :
                - Liste détaillée des ingrédients avec quantités précises
                🧪 Préparation :
                - Étapes de préparation détaillées
                🎯 Conseils de service :
                - Type de verre recommandé
                - Garniture suggérée
                - Température de service
                👅 Note de dégustation :
                - Description détaillée du goût et des sensations
                - Force de l'alcool (1-5)
                - Complexité de la recette (1-5)"""

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Tu es un expert en cocktails créatifs. Crée des recettes détaillées et bien formatées avec des emojis."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )

                recipe = response.choices[0].message.content

                # Générer le nom du cocktail
                name_prompt = f"""Crée un nom créatif et accrocheur pour un cocktail dans un thème FANTASTIQUE avec les caractéristiques suivantes :
                - Alcool principal : {spirit}
                - Types de goût : {', '.join(taste_types)}
                - Humeur : {mood if mood else 'Non spécifiée'}

                Le nom doit être :
                - Court et mémorable
                - Inspiré de la fantasy/science-fiction (dragons, licornes, elfes, fées, magie, etc.)
                - Utiliser des mots comme : mystique, enchanté, légendaire, mythique, céleste, etc.
                - Refléter les caractéristiques du cocktail

                Exemples de noms dans ce style :
                - Le Phénix Enflammé
                - L'Élixir des Elfes
                - Le Dragon de Cristal
                - La Potion Mystique
                - Le Sortilège de la Licorne"""

                name_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "Tu es un expert en création de noms de cocktails fantastiques. Crée des noms courts, créatifs et mémorables inspirés de la fantasy et de la science-fiction."},
                        {"role": "user", "content": name_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=50
                )

                cocktail_name = name_response.choices[0].message.content.strip()
                cocktails.append({
                    'name': cocktail_name,
                    'spirit': spirit,
                    'recipe': recipe
                })

            # Générer un numéro de commande temporaire
            temp_order_number = generate_order_number()

            # Stocker les informations temporairement dans la session
            session_data = {
                'customer_name': customer_name,
                'alcohol_type': alcohol_type,
                'base': base,
                'taste_types': taste_types,
                'mood': mood,
                'temp_order_number': temp_order_number,
                'cocktails': cocktails
            }

            return render_template('select_cocktail.html', 
                                session_data=session_data)
        except Exception as e:
            print(f"Erreur lors de la génération des cocktails : {str(e)}")
            flash('Une erreur est survenue lors de la génération des cocktails.', 'error')
            return redirect(url_for('index'))

    return render_template('index.html')

@app.route('/confirm_selection', methods=['POST'])
def confirm_selection():
    try:
        cocktail_index = int(request.form.get('cocktail_index'))
        customer_name = request.form.get('customer_name')
        alcohol_type = request.form.get('alcohol_type')
        base = request.form.get('base')
        taste_types = request.form.get('taste_types').split(',')
        mood = request.form.get('mood')
        temp_order_number = request.form.get('temp_order_number')
        cocktails = eval(request.form.get('cocktails'))

        selected_cocktail = cocktails[cocktail_index]

        # Créer la commande dans la base de données
        order = Order(
            order_number=temp_order_number,
            customer_name=customer_name,
            base=base,
            alcohol=alcohol_type,
            taste_types=', '.join(taste_types),
            mood=mood,
            cocktail_name=selected_cocktail['name'],
            recipe=selected_cocktail['recipe']
        )
        db.session.add(order)
        db.session.commit()

        return render_template('confirm.html', 
                             customer_name=customer_name,
                             order_number=temp_order_number,
                             recipe=selected_cocktail['recipe'])
    except Exception as e:
        print(f"Erreur lors de la confirmation de la sélection : {str(e)}")
        flash('Une erreur est survenue lors de la confirmation de la commande.', 'error')
        return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    
    # Convertir les objets Order en dictionnaires
    orders_data = []
    for order in orders:
        order_dict = {
            'order_number': order.order_number,
            'customer_name': order.customer_name,
            'alcohol': order.alcohol,
            'base': order.base,
            'taste_types': order.taste_types,
            'mood': order.mood,
            'status': 'servi' if order.completed else 'en_attente',
            'created_at': order.created_at.isoformat(),
            'recipe': order.recipe
        }
        orders_data.append(order_dict)
    
    return render_template('dashboard.html', orders=orders_data)

@app.route('/complete_order/<int:order_id>', methods=['POST'])
def complete_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.completed = True
    db.session.commit()
    flash('Commande marquée comme terminée !', 'success')
    return redirect(url_for('dashboard'))

@app.route('/confirm', methods=['POST'])
def confirm():
    customer_name = request.form.get('customer_name')
    alcohol_type = request.form.get('alcohol_type')
    taste_types = request.form.get('taste_types', '').split(',')
    mood = request.form.get('mood')
    
    # Générer un numéro de commande unique
    order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Créer une nouvelle commande
    order = Order(
        customer_name=customer_name,
        alcohol_type=alcohol_type,
        taste_types=taste_types,
        mood=mood,
        order_number=order_number,
        status='en_attente'
    )
    db.session.add(order)
    db.session.commit()
    
    # Générer le cocktail avec GPT
    prompt = f"""Crée une recette de cocktail avec les caractéristiques suivantes :
    - Type d'alcool : {alcohol_type}
    - Goûts : {', '.join(taste_types)}
    - Humeur : {mood}

    Format de réponse souhaité :
        🍸 Nom du cocktail
        🥃 Ingrédients :
        - Liste des ingrédients avec quantités
        🧪 Préparation :
        - Étapes de préparation
        🎯 Conseils de service :
        - Conseils pour servir le cocktail
        👅 Note de dégustation :
        - Description du goût et des sensations"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Tu es un expert en cocktails créatifs. Crée des recettes détaillées et bien formatées avec des emojis."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=500
    )

    recipe = response.choices[0].message.content
    
    return render_template('confirm.html', 
                         customer_name=customer_name,
                         order_number=order_number,
                         recipe=recipe)

@app.route('/clear_all_orders', methods=['POST'])
def clear_all_orders():
    try:
        Order.query.delete()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Toutes les commandes ont été supprimées'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_status/<order_number>', methods=['POST'])
def update_status(order_number):
    try:
        order = Order.query.filter_by(order_number=order_number).first()
        if order:
            order.completed = True
            db.session.commit()
            return jsonify({'success': True, 'message': 'Statut de la commande mis à jour'})
        return jsonify({'success': False, 'message': 'Commande non trouvée'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_orders')
def get_orders():
    try:
        orders = Order.query.order_by(Order.created_at.desc()).all()
        orders_data = []
        for order in orders:
            orders_data.append({
                'order_number': order.order_number,
                'customer_name': order.customer_name,
                'alcohol': order.alcohol,
                'base': order.base,
                'taste_types': order.taste_types,
                'mood': order.mood,
                'cocktail_name': order.cocktail_name,
                'recipe': order.recipe,
                'completed': order.completed,
                'created_at': order.created_at.isoformat()
            })
        return jsonify(orders_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 