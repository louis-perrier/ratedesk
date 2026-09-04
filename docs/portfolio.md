# Fiche portfolio, prête à coller dans /admin de lenopulse

Un champ par bloc, dans l'ordre du formulaire. Textes en anglais, comme les
items déjà en ligne.

**name**

```
Hotel rate desk
```

**tag**

```
Back office
```

**line**

```
Every partner sees a different form, on the same page.
```

**stack**

```
Django 5, Python, SQLite, Vanilla JS
```

**url** : laisser vide, le projet n'est pas déployé.

**image_kind** : `image` si vous mettez une capture de l'admin, `abstract` si
vous mettez le schéma `docs/mechanism-dark.svg`.

**problem**

```
Hotels sell the same room through several channels, and every channel signs a
different contract. A price that is fine on one of them quietly breaks another,
and nobody notices until the commission lands.
```

**built**

```
One admin screen that changes shape depending on who opens it. A distribution
partner only sees the hotels he has a contract on, every new rate line starts on
his own contract values, and he is told he is out of bounds while he types
rather than after saving.
```

**decisions**

```
The contract rules live in one module that knows nothing about forms or the
admin, so the live check and the save path call the exact same code. A test
compares the two messages character for character, which is what stops them from
drifting apart over time. The partner's channel is read from his session and
never from the browser, so bypassing the interface changes nothing about what
gets written.
```

**result**

```
31 tests, including the ones that forge a request to prove the browser is not
what protects the data.
```

**status**

```
Built as a working demo, running locally.
```

## Les captures à prendre

Trois écrans suffisent, connecté en `expedia` (mot de passe `demo`) :

1. La liste des hôtels, qui n'en montre qu'un, alors que la base en contient deux
2. La ligne de tarif vide, déjà remplie aux valeurs du contrat, canal grisé
3. Le message d'erreur sous le champ prix, obtenu sans avoir cliqué sur Save

La troisième est la plus parlante, c'est celle à mettre en `image_url`.
