# ratedesk

Un back office hotelier ou le formulaire de saisie des tarifs change de forme
selon qui le remplit.

Un revenue manager voit tous les etablissements et fixe ses prix librement. Un
partenaire de distribution ne voit que les tarifs de son canal, sur les seuls
hotels ou il a un contrat, et ce contrat lui impose un plancher de prix, un
plafond de remise et une duree minimale de sejour. Les erreurs apparaissent
pendant la saisie, sans passer par le bouton d'enregistrement.

## Le principe

Les regles de contrat vivent dans un seul fichier, `rates/rules.py`, qui ne
connait ni l'admin ni les formulaires. Le formulaire les appelle a
l'enregistrement, et une route de verification les appelle pendant la saisie.
Aucune regle n'est reecrite en JavaScript, donc les deux chemins ne peuvent pas
diverger. Un test le verifie en comparant les deux messages caractere par
caractere.

Le canal d'un partenaire n'est jamais lu depuis le navigateur. Il vient de la
session, ce qui rend la route de verification aussi sure que le formulaire.

## Lancer

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py runserver
```

Puis `http://127.0.0.1:8000/admin/`. Trois comptes, mot de passe `demo` :

| Compte | Ce qu'il voit |
| --- | --- |
| `manager` | tout, sans contrainte de contrat |
| `booking` | ses tarifs sur les deux hotels |
| `expedia` | ses tarifs sur un seul hotel, il n'a pas de contrat sur l'autre |

Le mode d'emploi detaille, avec les parcours de test, est dans `tester.html`.

## Tests

```bash
.venv/bin/python manage.py test rates
```
