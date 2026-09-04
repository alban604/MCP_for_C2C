# 🏔️ MCP Camp to Camp (Alpine Route Context Provider)

Un serveur **Model Context Protocol (MCP)** conçu pour enrichir les capacités des LLMs dans la préparation et l'analyse de courses en montagne (alpinisme, escalade, ski de randonnée, etc.). 

Ce projet expose un ensemble d'outils permettant à un assistant IA d'interagir avec les bases de données communautaires et les services météorologiques afin de fournir des conseils précis sur les conditions d'un itinéraire.

## ✨ Fonctionnalités (Outils exposés au LLM)

- **Recherche de topos :** Permet au LLM d'interroger une base de données d'itinéraires pour récupérer les caractéristiques techniques (cotation, dénivelé, engagement, matériel requis).
- **Analyse des dernières sorties (Scraping) :** Extraction automatisée des comptes-rendus communautaires récents. Le LLM peut utiliser ces données pour synthétiser les conditions actuelles (état du glacier, présence de glace/neige, regel) et mettre en évidence les erreurs d'itinéraires classiques mentionnées par les autres cordées.
- **Contexte météorologique global :** Récupération de la météo des jours passés (pour évaluer la purge des faces ou le regel nocturne) et des prévisions à venir sur le secteur visé.

## 🛠️ Technologies utilisées

- **Langage :** Python
- **Serveur MCP :** FastMCP 
- **Scraping & Extraction :** Playwright / Selenium (pour extraire dynamiquement les comptes-rendus de sorties)
- **Données Météo :** Open-Meteo API
- **Interface/Test :** Gradio (pour tester les requêtes manuellement avant intégration LLM)

## 💡 Cas d'usage (Exemple de prompt)

Une fois le serveur connecté à votre client MCP (comme l'application Claude ou un client custom), vous pouvez demander à l'IA :

> *"Je prévois de faire la traversée des arêtes de la Meije ce week-end. Cherche le topo, vérifie la météo des 3 derniers jours pour évaluer le regel, et fais-moi un résumé des conditions rencontrées par les cordées qui y sont allées cette semaine. Précise les erreurs d'itinéraires fréquentes."*

L'IA appellera alors de manière autonome les outils de scraping et de météo pour construire une réponse argumentée, sourcée et à jour.
