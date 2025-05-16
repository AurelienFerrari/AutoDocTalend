import os
from bs4 import BeautifulSoup
import re
import yaml


def format_historique_versions(historique):
    """
    Adds a line break before each new version (vX.X date) for display in the changelog/history.
    """
    # Clean possible <br> HTML tags and carriage returns
    histo = re.sub(r'<br\s*/?>', '\n', historique, flags=re.IGNORECASE)
    histo = histo.replace('\r','').replace('\n','')
    # Add a line break before each pattern vX.X date (except at the start of the text)
    histo = re.sub(r'(?<!^)(?<!\n)(v\d+\.\d+\s+\d{2}/\d{2}/\d{4})', r'\n\1', histo)
    return histo.strip()

SECTIONS_TO_IGNORE = [
    'Liste des contextes', 'Context List', 'ContexteDefault', 'ContextePROD',
    'Context', 'context', 'Contexts', 'contexts',
    'Paramètres supplémentaires', 'Statut & Logs', 'Prévisualiser l\'image',
    'Propriétés', 'Valeurs', 'Nom', 'Langue', 'Statut',
    'Exécution multi thread', 'tContextLoad implicite',
    'Utiliser les statistiques (tStatCatcher)', 'Utiliser les logs (tLogCatcher)',
    'Utiliser les volumes (tFlowMeterCatcher)', 'Dans la console',
    'Dans des fichiers', 'Dans la base de données',
    'Capturer les statistiques des composants', "Capturer les erreurs de l'exécutable",
    "Capturer les erreurs de l'utilisateur", "Capturer les alertes à l'utilisateur"
]

ANCHORS_TO_IGNORE = [
    'Context List', 'ContexteDefault', 'ContextePROD', 'Context', 'context', 'Contexts', 'contexts', 'Prévisualiser l\'image'
]

def is_context_section(title):
    """
    Checks if a given section title should be ignored based on predefined keywords.
    Args:
        title (str): The section title to check.
    Returns:
        bool: True if the title matches any ignored keyword, False otherwise.
    """
    return any(kw.lower() in title.lower() for kw in SECTIONS_TO_IGNORE)

def extract_sections(soup):
    """
    Extracts all top-level sections from the HTML soup, skipping those identified as context sections.
    Returns a list of dictionaries, each with keys 'title' and 'content'.
    'title' is the section header, 'content' is a list of HTML strings belonging to the section.
    """
    output = []
    for h2 in soup.find_all('h2'):
        title = h2.get_text(strip=True)
        if is_context_section(title):
            continue
        section_content = []
        for sibling in h2.next_siblings:
            if sibling.name == 'h2':
                break
            if sibling.name and sibling.get('class') and any('context' in c for c in sibling.get('class')):
                continue
            section_content.append(str(sibling))
        if section_content:
            output.append({'title': title, 'content': section_content})
    return output

def extract_unique_components(soup):
    """
    Extracts unique component types from the 'Liste des composants' section of the HTML soup.
    Args:
        soup (BeautifulSoup): Parsed HTML soup object.
    Returns:
        list: Sorted list of unique component types (e.g., tFileDelete, tMap, ...).
    """
    unique_types = set()
    # Search for the 'Liste des composants' section
    for h2 in soup.find_all('h2'):
        if 'composant' in h2.get_text(strip=True).lower():
            # Find the table immediately after the header
            table = h2.find_next('table')
            if table:
                for row in table.find_all('tr')[1:]:  # skip header
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        comp_type = cols[1].get_text(strip=True)
                        unique_types.add(comp_type)
            break
    return sorted(unique_types)


def html_to_markdown(html):
    """
    Converts HTML content to plain markdown-like text by extracting visible text.
    Args:
        html (str): HTML content as a string.
    Returns:
        str: Extracted plain text from the HTML.
    Note:
        This is a simple conversion and can be improved using markdownify or similar libraries if needed.
    """
    text = BeautifulSoup(html, 'html.parser').get_text(separator='\n', strip=True)
    return text


def load_composant_descriptions(yaml_path="composants.yaml"):
    """
    Loads component descriptions from a YAML file.
    Args:
        yaml_path (str): Path to the YAML file containing component descriptions.
    Returns:
        dict: Dictionary of component descriptions, or empty dict if loading fails.
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error while reading YAML file: {e}")
        return {}

def parse_connector_info(sections):
    """
    Extracts connector metadata from the 'Description' section.
    Args:
        sections (list): List of section dictionaries, each with 'title' and 'content'.
    Returns:
        dict: Dictionary containing connector metadata fields such as name, version, objective, etc.
    Behavior:
        - Parses the 'Description' section for key-value pairs.
        - Fills in the metadata dictionary with extracted values.
        - If 'historique' is missing but 'description' starts with a version pattern, uses 'description' as 'historique'.
    """
    desc_section = next((s for s in sections if s['title'].strip().lower() == 'description'), None)
    info = {'nom': '', 'version': '', 'historique': '', 'creation': '', 'modification': '', 'description': '', 'objectif': ''}
    if desc_section:
        for content in desc_section['content']:
            soup_desc = BeautifulSoup(content, 'html.parser')
            rows = soup_desc.find_all('tr')
            for row in rows:
                cols = row.find_all(['td', 'th'])
                if len(cols) == 2:
                    key = cols[0].get_text(strip=True).lower()
                    val = cols[1].get_text(strip=True)
                    if key == 'nom':
                        info['nom'] = val
                    elif key == 'version':
                        info['version'] = val
                    elif key == 'historique':
                        info['historique'] = val
                    elif key == 'création' and not info['creation']:
                        info['creation'] = val
                    elif key == 'modification' and not info['modification']:
                        info['modification'] = val
                    elif key == 'description':
                        info['description'] = val
                    elif key == 'objectif':
                        info['objectif'] = val
    # If 'historique' is missing but 'description' starts with a version pattern, use 'description' as 'historique'
    if not info['historique'] and info['description'].strip().lower().startswith('v'):
        info['historique'] = info['description']
    return info

def write_connector_description(f, info):
    """
    Writes the connector description block at the top of the markdown file.
    Args:
        f (file object): The open file object to write to.
        info (dict): Connector metadata dictionary (name, version, objective, etc.).
    Behavior:
        - Writes connector name, objective (as summary), version, creation/modification dates, and history.
        - Handles formatting and missing values gracefully.
    """
    f.write("## Description du connecteur\n\n")
    f.write(f"**Nom :** {info['nom']}\n\n")
    if 'objectif' in info and info['objectif'].strip():
        f.write(f"**Résumé :** {info['objectif'].strip()}\n\n")
    f.write(f"**Version :** {info['version']}\n\n")
    f.write(f"**Création :** {info['creation']}\n\n")
    f.write(f"**Modification :** {info['modification']}\n\n")
    f.write(f"**Historique :**\n\n")
    historique = info['historique']
    if historique.strip():
        histo = format_historique_versions(historique)
        for line in histo.split('\n'):
            if line.strip():
                f.write(f"- {line}\n")
    else:
        f.write("(Aucun historique trouvé)\n")
    f.write("\n")

def get_context_value_from_table(soup, context_name):
    """
    Searches for the value of a given context variable in the ContextePROD table of the HTML soup.

    Args:
        soup (BeautifulSoup): Parsed HTML soup object.
        context_name (str): The name of the context variable to look for.

    Returns:
        str or None: The value of the context variable if found, otherwise None.
    """
    # Search for the table associated with ContextePROD
    context_prod_found = False
    tables = soup.find_all('table')
    for idx, table in enumerate(tables):
        # Check if this table contains the mention 'ContextePROD'
        if table.find(string=lambda t: t and 'ContextePROD' in t):
            context_prod_found = True
            # Look for the next table with columns 'Nom' and 'Valeur'
            for next_table in tables[idx+1:]:
                headers = [th.get_text(strip=True).lower() for th in next_table.find_all('th')]
                if 'nom' in headers and 'valeur' in headers:
                    idx_nom = headers.index('nom')
                    idx_valeur = headers.index('valeur')
                    for tr in next_table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) > max(idx_nom, idx_valeur):
                            nom = tds[idx_nom].get_text(strip=True)
                            valeur = tds[idx_valeur].get_text(strip=True)
                            if nom == context_name:
                                return valeur
                    break  # Only look for one context prod table
            break  # Only look for one ContextePROD
    return None

def substitute_context_vars(expr, soup):
    """
    Substitute each context.<name> in expr with its value from the ContextePROD table.
    
    Args:
        expr (str): The expression to substitute context variables in.
        soup (BeautifulSoup): The parsed HTML soup object.
    
    Returns:
        str: The expression with context variables substituted.
    """
    import re
    # Search for the context prod table (ContextePROD)
    context_prod = {}
    tables = soup.find_all('table')
    for idx, table in enumerate(tables):
        if table.find(string=lambda t: t and 'ContextePROD' in t):
            for next_table in tables[idx+1:]:
                headers = [th.get_text(strip=True).lower() for th in next_table.find_all('th')]
                if 'nom' in headers and 'valeur' in headers:
                    idx_nom = headers.index('nom')
                    idx_valeur = headers.index('valeur')
                    for tr in next_table.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) > max(idx_nom, idx_valeur):
                            nom_var = tds[idx_nom].get_text(strip=True)
                            valeur_var = tds[idx_valeur].get_text(strip=True)
                            context_prod[nom_var] = valeur_var
                    break
            break
    matches = re.findall(r'context\.([a-zA-Z0-9_]+)', expr)
    for var in matches:
        if var in context_prod:
            expr = re.sub(r'context\.' + re.escape(var), context_prod[var], expr)
    expr = expr.replace('+', '').replace('"', '').replace("'", '').strip()
    expr = re.sub(r'\s+', '', expr)
    return expr

def write_section(f, section, unique_components, composants_info, context_vars=None, soup=None):
    """
    Writes a markdown section to the output file, handling special cases for component sections.

    Args:
        f (file object): The open file object to write to.
        section (dict): Section data with 'title' and 'content'.
        unique_components (list): List of unique component types found in the documentation.
        composants_info (dict): Dictionary of component descriptions from YAML.
        context_vars (list or None): List of unique context variable names (only used for 'Liste des composants').
        soup (BeautifulSoup, optional): Parsed HTML soup object.

    Behavior:
        - For component list sections, writes a table and details for each component.
        - For other sections, converts HTML content to markdown-like text and writes it.
    """
    title = section['title'].strip()
    if title.lower() == 'liste des composants':
        f.write("## Liste des composants\n\n")
        f.write("### Types de composants utilisés\n\n")
        f.write("| Type de composant |\n")
        f.write("|-------------------|\n")
        for comp_type in unique_components:
            f.write(f"| {comp_type} |\n")
        f.write("\n---\n\n")
        # Add the 'Context Utilisé' section immediately after the component list
        f.write("## Context Utilisé\n\n")
        if context_vars:
            for var in context_vars:
                var_lower = var.lower()
                if ('o2t' in var_lower or 'password' in var_lower):
                    f.write(f"- `{var}`\n")
                else:
                    valeur = None
                    if soup is not None:
                        var_name = var.replace('context.', '')
                        valeur = get_context_value_from_table(soup, var_name)
                    if valeur:
                        f.write(f"- `{var}` = `{valeur}`\n")
                    else:
                        f.write(f"- `{var}`\n")
        else:
            f.write("_No context parameters used._\n")
        # Search for historical CSV files
        if soup is not None:
            csv_files = []
            # Search in links (legacy method)
            for link in soup.find_all(['a', 'span']):
                href = link.get('href') or link.get('data-filepath') or ''
                text = link.get_text(strip=True).lower()
                if href and href.lower().endswith('.csv'):
                    if any(x in href.lower() or x in text for x in ['histo', 'historique', 'suivi']):
                        root_path = os.path.abspath(href)
                        csv_files.append((os.path.basename(href), root_path))
            # Search in tFileOutputDelimited/tFileInputDelimited component tables
            for table in soup.find_all('table'):
                nom_unique = None
                nom_fichier = None
                for row in table.find_all('tr'):
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        cle = cols[0].get_text(strip=True).lower()
                        val = cols[1].get_text(strip=True)
                        if 'nom unique' in cle:
                            nom_unique = val
                        if 'nom de fichier' in cle:
                            nom_fichier = val
                if nom_unique and nom_fichier:
                    if ('tfileoutputdelimited' in nom_unique.lower() or 'tfileinputdelimited' in nom_unique.lower()):
                        if ('.csv' in nom_fichier.lower() and any(x in nom_fichier.lower() for x in ['histo', 'historique', 'suivi'])):
                            chemin_reel = substitute_context_vars(nom_fichier, soup)
                            csv_files.append((os.path.basename(chemin_reel), chemin_reel))
            # Display the Historique section if files are found
            if csv_files:
                # Remove duplicates (name, path)
                seen = set()
                unique_csv_files = []
                for nom, chemin in csv_files:
                    key = (nom, chemin)
                    if key not in seen:
                        seen.add(key)
                        unique_csv_files.append((nom, chemin))
                f.write('\n## Historique\n\n')
                for nom, chemin in unique_csv_files:
                    chemin_affiche = chemin
                    if 'context.' in chemin_affiche:
                        chemin_affiche = substitute_context_vars(chemin_affiche, soup)
                    f.write(f'- **{nom}** : `{chemin_affiche}`\n')
                f.write('\n---\n\n')
        f.write("\n---\n\n")
    elif title.lower() in ['context utilisé', 'context utilise']:
        # This section is no longer displayed here, as it is generated right after the component list
        pass
    elif title.lower() == 'description des composants':
        f.write("## Description des composants\n\n")
        f.write("### Utilité et exemples des composants\n\n")
        for comp_type in unique_components:
            desc = composants_info.get(comp_type, None)
            f.write(f"#### {comp_type}\n")
            if desc:
                f.write(f"- **Utilité** : {desc.get('utilite','')}\n")
                f.write(f"- **Exemple** : {desc.get('exemple','')}\n\n")
            else:
                f.write("- _Description non renseignée dans le fichier de configuration._\n\n")
        f.write("---\n\n")
    else:
        for content in section['content']:
            md = html_to_markdown(content)
            if md.strip():
                f.write(md + '\n\n')

def extract_context_usages(soup):
    """
    Extracts all unique context.x usages from the HTML soup.
    Args:
        soup (BeautifulSoup): Parsed HTML soup object.
    Returns:
        set: Set of unique context parameter names (e.g., context.FOO_BAR)
    """
    context_pattern = re.compile(r"context\.([a-zA-Z0-9_]+)")
    context_vars = set()
    # Search all text nodes and code/pre blocks
    for tag in soup.find_all(text=True):
        for match in context_pattern.findall(tag):
            context_vars.add(f"context.{match}")
    return sorted(context_vars)

def write_context_section(f, context_vars, soup=None):
    """
    Writes the 'Context Utilisé' section to the markdown file.
    Affiche la valeur de chaque variable contextuelle trouvée dans le HTML.

    Args:
        f (file object): The open file object to write to.
        context_vars (list): List of context variable names (e.g., context.MAIL_HOST).
        soup (BeautifulSoup, optional): Parsed HTML soup object to extract values from.
    """
    f.write("## Context Utilisé\n\n")
    if context_vars:
        for var in context_vars:
            val = None
            if soup is not None:
                val = get_context_value_from_table(soup, var.split('.')[-1])
            if val:
                f.write(f"- {var} : {val}\n")
                val = tag.split(':')[-1].strip()
            else:
                val = tag.strip()
            break
            context_dict[var] = val
        for var in context_vars:        
            valeur = context_dict.get(var, None)
            if 'mail' in var.lower():
                if valeur:
                    f.write(f"- `{var}` = `{valeur}`\n")
                else:
                    f.write(f"- `{var}`\n")
            else:
                f.write(f"- `{var}`\n")
    else:
        f.write("_Aucun paramètre contextuel utilisé._\n")
    f.write("\n---\n\n")

    # Search for the correct HTML file in documentations/
    html_path = None
    doc_dir = os.path.join(os.path.dirname(__file__), "documentations")
    for fname in os.listdir(doc_dir):
        if fname.endswith(".html"):
            html_path = os.path.join(doc_dir, fname)
            break
    noms_uniques = set()
    param_data = {}
    if html_path:
        with open(html_path, "r", encoding="utf-8") as fin:
            contenu = fin.read()
            soup = BeautifulSoup(contenu, "html.parser")
            # Search for all unique O2T names
            for match in re.findall(r"tO2T(?:Input|Output)_\d+", contenu):
                noms_uniques.add(match)
            # For each unique name, find the component parameter table
            for nom in noms_uniques:
                table = None
                # Search for a table containing the row "Nom unique" with the value nom
                for t in soup.find_all("table"):
                    found = False
                    for row in t.find_all("tr"):
                        cols = row.find_all(["td", "th"])
                        if len(cols) >= 2 and "Nom unique" in cols[0].get_text(strip=True) and nom == cols[1].get_text(strip=True):
                            table = t
                            found = True
                            break
                    if found:
                        break
                # If the table is found, extract the useful values
                if table:
                    params = {}
                    for row in table.find_all("tr"):
                        cols = row.find_all(["td", "th"])
                        if len(cols) >= 2:
                            cle = cols[0].get_text(strip=True)
                            val = cols[1].get_text(strip=True)
                            params[cle] = val
                    param_data[nom] = params
def write_o2t_header(f, unique_components, composants_info):
    import re, os
    from bs4 import BeautifulSoup
    # Search for the correct HTML file in documentations/
    html_path = None
    doc_dir = os.path.join(os.path.dirname(__file__), "documentations")
    for fname in os.listdir(doc_dir):
        if fname.endswith(".html"):
            html_path = os.path.join(doc_dir, fname)
            break
    noms_uniques = set()
    param_data = {}
    if html_path:
        with open(html_path, "r", encoding="utf-8") as fin:
            contenu = fin.read()
            soup = BeautifulSoup(contenu, "html.parser")
            # Search for all unique O2T names
            for match in re.findall(r"tO2T(?:Input|Output)_\d+", contenu):
                noms_uniques.add(match)
            # For each unique name, find the component parameter table
            for nom in noms_uniques:
                table = None
                # Search for a table containing the row "Nom unique" with the value nom
                for t in soup.find_all("table"):
                    found = False
                    for row in t.find_all("tr"):
                        cols = row.find_all(["td", "th"])
                        if len(cols) >= 2 and "Nom unique" in cols[0].get_text(strip=True) and nom == cols[1].get_text(strip=True):
                            table = t
                            found = True
                            break
                    if found:
                        break
                # If the table is found, extract the useful values
                if table:
                    params = {}
                    for row in table.find_all("tr"):
                        cols = row.find_all(["td", "th"])
                        if len(cols) >= 2:
                            cle = cols[0].get_text(strip=True)
                            val = cols[1].get_text(strip=True)
                            params[cle] = val
                    param_data[nom] = params
    if not noms_uniques:
        f.write("_Aucun composant O2T trouvé dans la documentation._\n\n---\n\n")
        print("Aucun composant O2T trouvé dans la documentation.")
        return
    f.write("## En-tête One2Team\n\n")
    f.write("| Nom unique | Modèle de fiche | Requête O2T / Type List |\n")
    f.write("|------------|-----------------|-------------------------|\n")
    for nom in sorted(noms_uniques):
        params = param_data.get(nom, {})
        if nom.startswith("tO2TInput"):
            fiche_modele = params.get("modèle de fiche", "")
            requete = params.get("Requête O2T", "")
            f.write(f"| {nom} | {fiche_modele} | {requete} |\n")
        elif nom.startswith("tO2TOutput"):
            type_list = params.get("Type List", "")
            f.write(f"| {nom} | {type_list} |  |\n")
    f.write("\n---\n\n")

def write_simple_summary(f, sections):
    """
    Écrit un sommaire simple (sans liens) avec une liste fixe de titres, dans l'ordre défini.
    """
    f.write("## Sommaire\n\n")
    titres = [
        "Description du connecteur",
        "En-tête One2Team",
        "Liste des composants",
        "Description des composants"
    ]
    for titre in titres:
        f.write(f"- {titre}\n")
    f.write("\n")

def generate_markdown(input_path, output_path):
    """
    Orchestrates the generation of a markdown documentation file from a Talend HTML file.

    Args:
        input_path (str): Path to the input HTML file.
        output_path (str): Path to the output markdown file.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    sections = extract_sections(soup)
    unique_components = extract_unique_components(soup)
    composants_info = load_composant_descriptions(os.path.join(os.path.dirname(__file__), "composants.yaml"))
    connector_info = parse_connector_info(sections)
    context_vars = extract_context_usages(soup)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Talend Documentation\n\n")
        f.write("> Generated automatically.\n\n")
        f.write("---\n\n")
        # Add simple summary without links
        write_simple_summary(f, sections)
        # Connector description
        write_connector_description(f, connector_info)
        # Add O2T header juste après la description du connecteur
        write_o2t_header(f, unique_components, composants_info)
        # Write all other sections, except En-tête One2Team
        for section in sections:
            titre = section['title'].strip().lower()
            if titre in ['description du connecteur', 'en-tête one2team', 'description du projet', 'description', 'résumé', 'paramètres', 'code source']:
                continue
            write_section(f, section, unique_components, composants_info, context_vars, soup)
        f.write("\n---\n")
    print(f"Clean documentation generated in {output_path}")
