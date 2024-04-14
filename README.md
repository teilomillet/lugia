# lugia
Lugia permet de basculer entre différents modèles de langage (LLMs), utilisable n'importe où avec une connexion internet et une clé API. 
Une connexion à un stockage objet S3 est nécessaire pour sauvegarder les conversations et y accéder ultérieurement. (AWS, Scaleway, ...)

Je suis actuellement satisfait de Lugia malgré mes autres projets qui me prennent beaucoup de temps. À terme, il est prévu d'intégrer Ollama et de nombreuses améliorations sont possibles.

## Instructions pour l'installation:
1. Téléchargez le projet via `git clone`.
2. Accédez au répertoire avec `cd lugia`.
3. Activez l'environnement virtuel avec `poetry shell`.
4. Installez les dépendances avec `poetry install`.
5. Pour utiliser Podman (ou Docker), construisez l'image avec `podman build -t localhost/lugia:latest .` et lancez l'application avec `podman run -p 8000:8000 localhost/lugia:latest` pour démarrer **Lugia**.

Si les conversations ne se chargent pas correctement, le problème peut venir de votre navigateur.  Essayez de copier-coller l'URL dans un autre navigateur pour voir si cela résout le problème.

### Configuration nécessaire:
Créez un fichier `.env` contenant les clés d'accès nécessaires :

.env :
```
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
LUGIA_ACCESS_KEY_ID=
LUGIA_SECRET_KEY=
```

À propos des versions précédentes:
Les données étaient initialement sauvegardées en local au format .json. Cependant, le passage d'un ordinateur à l'autre étant fréquent, il est plus pratique et économique de travailler sur plusieurs appareils avec un stockage centralisé.
