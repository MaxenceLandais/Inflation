import json

def calculer_inflation():
    history = []
    try:
        with open('prices_history.json', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    history.append(json.loads(line))
    except FileNotFoundError:
        print("Pas encore d'historique.")
        return

    if len(history) < 2:
        print("Besoin d'au moins deux jours de données pour calculer l'inflation.")
        return

    # On compare le premier jour enregistré avec le dernier
    debut = history[0]
    actuel = history[-1]

    # Calcul de la moyenne du panier (on pourrait pondérer ici)
    prix_moyen_debut = sum(p['prix'] for p in debut['produits']) / len(debut['produits'])
    prix_moyen_actuel = sum(p['prix'] for p in actuel['produits']) / len(actuel['produits'])

    inflation = ((prix_moyen_actuel - prix_moyen_debut) / prix_moyen_debut) * 100

    print(f"--- Rapport d'Inflation ---")
    print(f"Début : {debut['date'][:10]} | Prix moyen : {prix_moyen_debut:.2f}€")
    print(f"Aujourd'hui : {actuel['date'][:10]} | Prix moyen : {prix_moyen_actuel:.2f}€")
    print(f"Taux d'inflation calculé : {inflation:+.2f}%")

if __name__ == "__main__":
    calculer_inflation()
