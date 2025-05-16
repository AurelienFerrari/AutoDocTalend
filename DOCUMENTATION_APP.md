# Documentation de l’application Python docTalend

## Objectif

L’application `ADT (AutoDocTalend)` automatise la génération de documentation Markdown à partir de fichiers HTML exportés depuis Talend. Elle met en forme, enrichit et structure la documentation des jobs Talend pour la rendre plus claire, maintenable et exploitable.

Avec ADT, documenter devient simple… et même agréable !
---
## Version de l'application

Version actuelle : 1.0

### Changelog

- Version 1.0
  - Création de l'application ADT (AutoDocTalend)

- Version 1.1
  - Création de la partie Historique en fonction de fichier suivi et historique des connecteurs talend
  - Suppression des liens hypertexte dans le sommaire
  - Affiche de tous les context utilisés dans le job sauf les password et les valeurs de o2t

## Structure des principaux scripts

### 1. `main.py`

- **Rôle** : Point d’entrée de l’application.
- **Fonctions principales** :
  - Cherche les fichiers `.html` dans le dossier `documentations`.
  - Pour chaque fichier, appelle `generate_markdown` pour générer la documentation Markdown correspondante dans `markdowns/`.
  - Archive les fichiers HTML traités dans le dossier `archives/`.

### 2. `talend_doc_cleaner.py`

- **Rôle** : Cœur de la génération de la documentation à partir des fichiers HTML produits par Talend.
- **Fonctions principales** :
  - `generate_markdown(input_path, output_path)` : Orchestration complète de la génération du fichier Markdown à partir d’un fichier HTML Talend. Gère l’ordre des sections, le sommaire, et l’archivage.
  - `extract_sections(soup)` : Extrait toutes les sections principales du HTML, en ignorant celles liées au contexte.
  - `extract_unique_components(soup)` : Liste tous les types de composants uniques utilisés dans le job Talend.
  - `extract_context_usages(soup)` : Repère tous les paramètres contextuels (`context.x`) utilisés dans le job.
  - `write_section(...)` : Gère l’écriture structurée de chaque section Markdown, y compris la liste des composants, la section contexte, et la section Historique (fichiers CSV historiques).
  - `write_simple_summary(f, sections)` : Insère un sommaire simple et fixe en haut du document Markdown.
  - `write_connector_description(f, info)` : Rédige le bloc de description du connecteur (nom, version, objectif, historique, etc.).
  - `write_o2t_header(f, unique_components, composants_info)` : Génère un tableau récapitulatif pour les composants O2T (si présents).
  - `write_context_section(f, context_vars, soup)` : Génère la section « Context Utilisé », affichant les variables de contexte et leurs valeurs extraites du tableau ContextePROD.
  - `get_context_value_from_table(soup, context_name)` : Extrait la valeur d’une variable de contexte depuis le tableau ContextePROD du HTML.
  - `substitute_context_vars(expr, soup)` : Remplace dynamiquement toutes les variables `context.<nom>` dans un chemin/une expression par leur valeur issue du ContextePROD (fonction clé pour l’affichage correct des chemins dans la section Historique).
  - `format_historique_versions(historique)` : Met en forme la section historique/changelog pour une meilleure lisibilité.
  - `load_composant_descriptions(yaml_path)` : Charge les descriptions des composants depuis un fichier YAML externe (optionnel).
  - `parse_connector_info(sections)` : Extrait les métadonnées du connecteur à partir de la section Description.
  - `is_context_section(title)` : Détermine si un titre de section doit être ignoré pour la documentation.
  - `html_to_markdown(html)` : Convertit du contenu HTML en texte markdown simplifié.

- **Spécificités** :
  - La section `Historique` est générée automatiquement, listant tous les fichiers CSV historiques/suivi référencés par les composants tFileOutputDelimited/tFileInputDelimited, avec substitution dynamique des variables de contexte pour afficher le chemin réel.
  - La section « Context Utilisé » est toujours insérée immédiatement après le tableau des types de composants utilisés.
  - Les sections `Paramètres` et `Code source` sont systématiquement ignorées pour plus de clarté.
  - Tous les commentaires et docstrings du code sont en anglais pour faciliter la maintenance et la collaboration internationale.
  - La table des matières reflète toujours la structure réelle du document généré.
  - **Format attendu pour l'historique du connecteur** : chaque entrée doit suivre le format : `v1.0 07/05/2025 AFE - Ceci est une explication` (version, date, initiales de l'auteur, description de la modification).
  - **Champ "Objectif" obligatoire** : le champ « Objectif » (résumé) du connecteur doit impérativement être renseigné et sera affiché dans la documentation générée.

### 3. `talend_zip_importer.py`

- **Rôle** : Automatisation de l’import et de l’extraction des fichiers ZIP contenant des jobs Talend.
- **Fonctionnement** :
  - Cherche les fichiers ZIP dans le dossier `zips`.
  - Extrait les fichiers HTML et les place dans `documentations/`.
  - Archive les ZIP traités dans `archives/`.

---

## Dépendances

- `BeautifulSoup` (`bs4`) : Parsing HTML.
- `pyyaml` : Lecture de fichiers de configuration YAML pour enrichir les descriptions de composants.
- Standard Python : `os`, `shutil`, `zipfile`, `re`.

---

## Installation des dépendances

Avant la première utilisation, installez les dépendances nécessaires :

```bash
pip install -r requirements.txt
```

---

## Organisation des dossiers

- `zips/` : Déposer ici les ZIP Talend à traiter.
- `documentations/` : Les fichiers HTML extraits et à documenter.
- `markdowns/` : Documentation générée au format Markdown.
- `archives/` : Fichiers HTML et ZIP archivés après traitement.

---


## Exemple de flux de traitement

1. Depuis Talend, générer la documentation HTML du job à documenter.
2. Créer les dossiers de la partie Organisation des dossiers
3. Déposer le fichier ZIP Talend généré dans le dossier `zips/`.
4. Installer les dépendances (une seule fois) :
   ```bash
   pip install -r requirements.txt
   ```
5. Lancer l’application :
   ```bash
   python main.py
   ```
6. Un fichier Markdown est généré dans `markdowns/` pour chaque job, structuré et enrichi.
7. Les fichiers sources sont archivés automatiquement.

---

## Extension et personnalisation

- Pour enrichir la description des composants, éditer le fichier `composants.yaml`.
- Pour ignorer ou ajouter des sections, adapter la liste `SECTIONS_TO_IGNORE` dans `talend_doc_cleaner.py`.
 
---
