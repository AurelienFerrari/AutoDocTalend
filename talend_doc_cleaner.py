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
    'Context', 'context', 'Contexts', 'contexts', 'Paramètres supplémentaires', 'Statut & Logs', 'Prévisualiser l\'image'
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

def write_table_of_contents(f, sections):
    """
    Dynamically generates the table of contents from the sections actually present in the markdown.
    Always adds:
      - One2Team header (if present)
      - Context Utilisé (if present)
      - Component list (if present)
      - Component description (if present)
    """
    toc_titles = []
    # Manually add fixed section titles if present
    fixed_titles = [
        'One2Team',
        'Description du connecteur',
        'Context Utilisé',
        'Liste des composants',
        'Description des composants'
    ]
    # Add fixed titles in order if they are in the sections
    all_titles = [s['title'] for s in sections]
    for t in fixed_titles:
        if t in all_titles:
            toc_titles.append(t)
    # Add other section titles not already included
    for t in all_titles:
        if t not in toc_titles:
            toc_titles.append(t)
    f.write("## Table of Contents\n\n")
    for title in toc_titles:
        anchor = title.lower().replace(' ', '-').replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c").replace("û", "u").replace("ô", "o").replace("î", "i").replace("ï", "i").replace("ë", "e").replace("ü", "u").replace("ä", "a").replace("ö", "o").replace("'", "").replace(",", "").replace("/", "-")
        f.write(f"- [{title}](#{anchor})\n")
    f.write("\n")


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
        # Automatically add the 'Context Utilisé' section right after the component list
        f.write("## Context Utilisé\n\n")
        if context_vars:
            for var in context_vars:
                if (('mail' in var.lower() or 'root' in var.lower()) and soup is not None):
                    var_name = var.replace('context.', '')
                    valeur = get_context_value_from_table(soup, var_name)
                    if valeur:
                        f.write(f"- `{var}` = `{valeur}`\n")
                    else:
                        f.write(f"- `{var}`\n")
                else:
                    f.write(f"- `{var}`\n")
        else:
            f.write("_No context parameters used._\n")
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
    If the context variable name contains 'mail', also displays its value found in the HTML.

    Args:
        f (file object): The open file object to write to.
        context_vars (list): List of context variable names (e.g., context.MAIL_HOST).
        soup (BeautifulSoup, optional): Parsed HTML soup object to extract values from.
    """
    f.write("## Context Utilisé\n\n")
    if context_vars:
        context_dict = {}
        if soup is not None:
            # Search for context values in the HTML
            for var in context_vars:
                var_name = var.replace('context.', '')
                val = None
                # Search all text nodes in the HTML
                for tag in soup.find_all(text=True):
                    if var_name in tag:
                        # Take the full line, then try to extract the value after '=' or ':'
                        if '=' in tag:
                            val = tag.split('=')[-1].strip()
                        elif ':' in tag:
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
        # Table of Contents
        toc_sections = [{'title': 'Description du connecteur'}] + [s for s in sections if s['title'].strip().lower() not in ['description du projet', 'description', 'résumé', 'paramètres', 'code source']]
        write_table_of_contents(f, toc_sections)
        # Connector description
        write_connector_description(f, connector_info)
        # Add O2T header if applicable
        write_o2t_header(f, unique_components, composants_info)
        for section in sections:
            if section['title'].strip().lower() in ['description du projet', 'description', 'résumé', 'paramètres', 'code source']:
                continue
            write_section(f, section, unique_components, composants_info, context_vars, soup)
        f.write("\n---\n")
    print(f"Clean documentation generated in {output_path}")
