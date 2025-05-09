import os
from talend_doc_cleaner import generate_markdown
import talend_zip_importer

def main():
    # 1. Import ZIP files (talend_zip_importer script executes on import)
    # 2. Generate markdown files for each imported HTML file
    doc_dir = 'documentations'
    md_dir = 'markdowns'
    os.makedirs(md_dir, exist_ok=True)
    html_found = False
    for fname in os.listdir(doc_dir):
        if fname.lower().endswith('.html'):
            html_found = True
            input_path = os.path.join(doc_dir, fname)
            base_name = os.path.splitext(fname)[0]
            output_path = os.path.join(md_dir, f'doc_{base_name}.md')
            print(f"Génération de {output_path} depuis {fname}")
            generate_markdown(input_path, output_path)
            archives_dir = 'archives'
            os.makedirs(archives_dir, exist_ok=True)
            html_dst = os.path.join(archives_dir, fname)
            try:
                os.replace(input_path, html_dst)
                print(f"Archivé {fname} dans {archives_dir}")
            except Exception as e:
                print(f"Erreur lors de l'archivage de {fname}: {e}")
    if not html_found:
        print(f"Aucun fichier .html trouvé dans {doc_dir}, aucune documentation générée.")

if __name__ == "__main__":
    main()
