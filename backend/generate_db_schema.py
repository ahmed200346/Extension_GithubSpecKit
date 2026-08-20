import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(backend_dir)

try:
    from app.models import Base
except ImportError as e:
    print(f"❌ Erreur d'importation : {e}")
    sys.exit(1)

def generate_mermaid_erd():
    lines = ["```mermaid", "erDiagram"]
    
    # Parcours des tables
    for table_name, table in Base.metadata.tables.items():
        lines.append(f"    {table_name} {{")
        for col in table.columns:
            col_type = str(col.type).split("(")[0]
            flags = []
            if col.primary_key:
                flags.append("PK")
            if col.foreign_keys:
                flags.append("FK")
            flag_str = f' "{",".join(flags)}"' if flags else ""
            lines.append(f"        {col_type} {col.name}{flag_str}")
        lines.append("    }")
        
        # Foreign Keys (Relations)
        for fk in table.foreign_keys:
            target_table = fk.column.table.name
            lines.append(f"    {target_table} ||--o{{ {table_name} : references")
            
    lines.append("```")
    return "\n".join(lines)

if __name__ == "__main__":
    print("⏳ Génération du code Mermaid ERD...")
    mermaid_code = generate_mermaid_erd()
    
    output_path = os.path.join(backend_dir, "schema_erd.mmd")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code)
        
    print(f"✅ Schéma généré sans aucune DLL dans : {output_path}")
    print("\n--- CODE À COPIER DANS VOTRE README.MD ---\n")
    print(mermaid_code)