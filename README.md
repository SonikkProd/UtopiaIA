# UtopiaIA - Bar Intelligent

Un système de commande de cocktails intelligent utilisant l'IA pour créer des recettes personnalisées.

## Fonctionnalités

- Création de cocktails personnalisés basée sur les préférences du client
- Interface utilisateur intuitive
- Génération de recettes avec OpenAI GPT-3.5
- Système de suivi des commandes
- Interface de gestion pour le personnel

## Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/votre-username/UtopiaIA.git
cd UtopiaIA
```

2. Créez un environnement virtuel et activez-le :
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows : venv\Scripts\activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Créez un fichier `.env` à la racine du projet avec vos clés API :
```
OPENAI_API_KEY=votre_clé_api
SECRET_KEY=votre_clé_secrète
```

5. Lancez l'application :
```bash
python app.py
```

## Configuration requise

- Python 3.8 ou supérieur
- Clé API OpenAI
- Navigateur web moderne

## Structure du projet

```
UtopiaIA/
├── app.py              # Application principale
├── templates/          # Templates HTML
├── static/            # Fichiers statiques (CSS, JS)
├── requirements.txt   # Dépendances
└── .env              # Variables d'environnement
```

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails. 