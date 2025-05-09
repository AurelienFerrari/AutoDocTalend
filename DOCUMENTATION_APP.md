# Documentation de l’application Python docTalend

## Objectif

L’application `ADT (AutoDocTalend)` automatise la génération de documentation Markdown à partir de fichiers HTML exportés depuis Talend. Elle met en forme, enrichit et structure la documentation des jobs Talend pour la rendre plus claire, maintenable et exploitable.

Avec ADT, documenter devient simple… et même agréable !
---

## Structure des principaux scripts

### 1. `main.py`

- **Rôle** : Point d’entrée de l’application.
- **Fonctions principales** :
  - Cherche les fichiers `.html` dans le dossier `documentations`.
  - Pour chaque fichier, appelle `generate_markdown` pour générer la documentation Markdown correspondante dans `markdowns/`.
  - Archive les fichiers HTML traités dans le dossier `archives/`.

### 2. `talend_doc_cleaner.py`

- **Rôle** : Cœur de la génération de la documentation à partir des fichiers HTML générés par Talend.
- **Fonctions clés** :
  - `generate_markdown(input_path, output_path)` : Orchestration complète de la génération du fichier Markdown à partir d’un fichier HTML Talend.
  - `extract_sections(soup)` : Extrait toutes les sections de haut niveau du HTML, en ignorant les sections de contexte.
  - `extract_unique_components(soup)` : Liste tous les types de composants utilisés dans le job Talend.
  - `extract_context_usages(soup)` : Repère tous les paramètres contextuels (`context.x`) utilisés dans le job.
  - `write_section(...)` : Gère l’écriture structurée des différentes sections Markdown, notamment la liste des composants et la section de contexte.
  - `write_table_of_contents(...)` : Génère dynamiquement la table des matières selon les sections réellement présentes dans la documentation.
  - `load_composant_descriptions(...)` : Charge les descriptions des composants depuis un fichier YAML externe (optionnel).
  - `parse_connector_info(...)` : Extrait les métadonnées du connecteur (nom, version, objectif, etc.) depuis la section Description du HTML.
  - `write_context_section(...)` : Génère la section « Context Utilisé », affichant les variables de contexte et leurs valeurs si disponibles.
  - `get_context_value_from_table(...)` : Extrait la valeur d’une variable de contexte à partir du tableau ContextePROD dans le HTML.

- **Spécificités** :
  - Les sections `Paramètres` et `Code source` sont systématiquement ignorées dans la documentation finale pour plus de clarté.
  - La section « Context Utilisé » est générée automatiquement et insérée juste après le tableau des types de composants utilisés.
  - Tous les commentaires et docstrings du code sont en anglais pour faciliter la collaboration internationale et la maintenance.
  - La table des matières est toujours à jour avec la structure réelle du document généré.
  - **Format attendu pour l'historique du connecteur** : chaque entrée de l'historique doit suivre le format : `v1.0 07/05/2025 AFE - Ceci est une explication` (version, date, initiales de l'auteur, description de la modification).
  - **Champ "Objectif" obligatoire** : le champ « Objectif » (résumé) du connecteur doit impérativement être renseigné. Il correspond au résumé fonctionnel du connecteur et sera affiché dans la documentation générée.

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
2. Déposer le fichier ZIP Talend généré dans le dossier `zips/`.
3. Installer les dépendances (une seule fois) :
   ```bash
   pip install -r requirements.txt
   ```
4. Lancer l’application :
   ```bash
   python main.py
   ```
5. Un fichier Markdown est généré dans `markdowns/` pour chaque job, structuré et enrichi.
6. Les fichiers sources sont archivés automatiquement.

---

## Extension et personnalisation

- Pour enrichir la description des composants, éditer le fichier `composants.yaml`.
- Pour ignorer ou ajouter des sections, adapter la liste `SECTIONS_TO_IGNORE` dans `talend_doc_cleaner.py`.
 
---
