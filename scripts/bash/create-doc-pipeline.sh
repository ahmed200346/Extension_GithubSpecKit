#!/usr/bin/env bash

set -e

# Parsing des arguments
JSON_MODE=false
ARGS=()
for arg in "$@"; do
    case "$arg" in
        --json) JSON_MODE=true ;;
        --help|-h) echo "Usage: $0 [--json] <description>"; exit 0 ;;
        *) ARGS+=("$arg") ;;
    esac
done

DESCRIPTION="${ARGS[*]}"

if [ -z "$DESCRIPTION" ]; then
    echo "Usage: $0 [--json] <description>" >&2
    exit 1
fi

# Recherche de la racine du dépôt
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ] && [ "$dir" != "." ]; do
        if [ -d "$dir/.git" ] \vert{}\vert{} [ -d "$dir/scripts" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root" >&2
        exit 1
    fi
    HAS_GIT=false
fi

cd "$REPO_ROOT"

SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# Recherche du plus grand identifiant d'exécution (incrémentation doc-pipeline-###)
HIGHEST=0
if [ -d "$SPECS_DIR" ]; then
    for dir in "$SPECS_DIR"/doc-pipeline-*; do
        [ -d "$dir" ] || continue
        dirname=$(basename "$dir")
        number=$(echo "$dirname" | sed -E 's/doc-pipeline-([0-9]+).*/\1/' || echo "0")
        number=$((10#$number))
        if [ "$number" -gt "$HIGHEST" ]; then HIGHEST=$number; fi
    done
fi

NEXT=$((HIGHEST + 1))
WORKFLOW_NUM=$(printf "\%03d" "$NEXT")

# Formatage du nom de dossier et de branche Git
BRANCH_SUFFIX=$(echo "$DESCRIPTION" \vert{} tr '[:upper:]' '[:lower:]' \vert{} sed 's/[^a-zA-Z0-9]/-/g' \vert{} sed 's/-\+/-/g' \vert{} sed 's/^-//' \vert{} sed 's/-$//')
WORDS=$(echo "$BRANCH_SUFFIX" | tr '-' '\n' | grep -v '^$' \vert{} head -3 \vert{} tr '\n' '-' \vert{} sed 's/-$//')
BRANCH_NAME="doc-pipeline/${WORKFLOW_NUM}-${WORDS}"
WORKFLOW_ID="doc-pipeline-${WORKFLOW_NUM}"

# Création de la branche Git si Git est disponible
if [ "$HAS_GIT" = true ]; then
    git checkout -b "$BRANCH_NAME" 2>/dev/null \vert{}\vert{} git checkout "$BRANCH_NAME" 2>/dev/null || true
else
    >&2 echo "[doc-pipeline] Warning: Git not detected; skipped branch creation"
fi

# Dossier cible dans specs/
WORKFLOW_DIR="$SPECS_DIR/${WORKFLOW_ID}-${WORDS}"
mkdir -p "$WORKFLOW_DIR"

# NOUVEAUX CHEMINS : Pointent vers extensions/ à la racine du projet
TEMPLATE="$REPO_ROOT/extensions/workflows/doc-pipeline/template.md"
TASKS_TEMPLATE="$REPO_ROOT/extensions/workflows/doc-pipeline/tasks-template.md"

TEMPLATE_FILE="$WORKFLOW_DIR/${WORKFLOW_ID}.md"
TASKS_FILE="$WORKFLOW_DIR/tasks.md"

# Copie des templates
if [ -f "$TEMPLATE" ]; then
    cp "$TEMPLATE" "$TEMPLATE_FILE"
else
    echo "# Document Spec" > "$TEMPLATE_FILE"
fi

if [ -f "$TASKS_TEMPLATE" ]; then
    cp "$TASKS_TEMPLATE" "$TASKS_FILE"
else
    echo "# Tasks" > "$TASKS_FILE"
fi

# Remplacement dynamique des IDs (compatible Linux/Windows/Git Bash)
perl -pi -e "s/doc-pipeline-###/${WORKFLOW_ID}/g" "$TEMPLATE_FILE" "$TASKS_FILE" 2>/dev/null || true

# Conversion en chemins absolus propres
TEMPLATE_FILE_ABS=$(cd "$(dirname "$TEMPLATE_FILE")" && pwd)/$(basename "$TEMPLATE_FILE")
TASKS_FILE_ABS=$(cd "$(dirname "$TASKS_FILE")" && pwd)/$(basename "$TASKS_FILE")

# Sortie au format JSON pour Claude Code
if $JSON_MODE; then
    printf '{"WORKFLOW_ID":"%s","BRANCH_NAME":"%s","TEMPLATE_FILE":"%s","TASKS_FILE":"%s","WORKFLOW_NUM":"%s"}\n' \
        "$WORKFLOW_ID" "$BRANCH_NAME" "$TEMPLATE_FILE_ABS" "$TASKS_FILE_ABS" "$WORKFLOW_NUM"
else
    echo "WORKFLOW_ID: $WORKFLOW_ID"
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "TEMPLATE_FILE: $TEMPLATE_FILE_ABS"
    echo "TASKS_FILE: $TASKS_FILE_ABS"
    echo "WORKFLOW_NUM: $WORKFLOW_NUM"
fi
# #!/usr/bin/env bash

# set -e

# # Parsing des arguments
# JSON_MODE=false
# ARGS=()
# for arg in "$@"; do
#     case "$arg" in
#         --json) JSON_MODE=true ;;
#         --help|-h) echo "Usage: $0 [--json] <description>"; exit 0 ;;
#         *) ARGS+=("$arg") ;;
#     esac
# done

# DESCRIPTION="${ARGS[*]}"

# if [ -z "$DESCRIPTION" ]; then
#     echo "Usage: $0 [--json] <description>" >&2
#     exit 1
# fi

# # Recherche de la racine du dépôt
# find_repo_root() {
#     local dir="$1"
#     while [ "$dir" != "/" ] && [ "$dir" != "." ]; do
#         if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then
#             echo "$dir"
#             return 0
#         fi
#         dir="$(dirname "$dir")"
#     done
#     return 1
# }

# SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# if git rev-parse --show-toplevel >/dev/null 2>&1; then
#     REPO_ROOT=$(git rev-parse --show-toplevel)
#     HAS_GIT=true
# else
#     REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
#     if [ -z "$REPO_ROOT" ]; then
#         echo "Error: Could not determine repository root" >&2
#         exit 1
#     fi
#     HAS_GIT=false
# fi

# cd "$REPO_ROOT"

# SPECS_DIR="$REPO_ROOT/specs"
# mkdir -p "$SPECS_DIR"

# # Recherche du plus grand identifiant d'exécution (incrémentation ###)
# HIGHEST=0
# if [ -d "$SPECS_DIR" ]; then
#     for dir in "$SPECS_DIR"/doc-pipeline-*; do
#         [ -d "$dir" ] || continue
#         dirname=$(basename "$dir")
#         number=$(echo "$dirname" | sed -E 's/doc-pipeline-([0-9]+).*/\1/' || echo "0")
#         number=$((10#$number))
#         if [ "$number" -gt "$HIGHEST" ]; then HIGHEST=$number; fi
#     done
# fi

# NEXT=$((HIGHEST + 1))
# WORKFLOW_NUM=$(printf "%03d" "$NEXT")

# # Formatage du nom de dossier et de branche Git
# BRANCH_SUFFIX=$(echo "$DESCRIPTION" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-zA-Z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
# WORDS=$(echo "$BRANCH_SUFFIX" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//')
# BRANCH_NAME="doc-pipeline/${WORKFLOW_NUM}-${WORDS}"
# WORKFLOW_ID="doc-pipeline-${WORKFLOW_NUM}"

# # Création de la branche Git si Git est disponible
# if [ "$HAS_GIT" = true ]; then
#     git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME" 2>/dev/null || true
# else
#     >&2 echo "[doc-pipeline] Warning: Git not detected; skipped branch creation"
# fi

# # Dossier cible dans specs/
# WORKFLOW_DIR="$SPECS_DIR/${WORKFLOW_ID}-${WORDS}"
# mkdir -p "$WORKFLOW_DIR"

# # Chemins des modèles
# TEMPLATE="$REPO_ROOT/.specify/extensions/workflows/doc-pipeline/template.md"
# TASKS_TEMPLATE="$REPO_ROOT/.specify/extensions/workflows/doc-pipeline/tasks-template.md"

# TEMPLATE_FILE="$WORKFLOW_DIR/template.md"
# TASKS_FILE="$WORKFLOW_DIR/tasks.md"

# # Copie des templates
# if [ -f "$TEMPLATE" ]; then
#     cp "$TEMPLATE" "$TEMPLATE_FILE"
# else
#     echo "# Document Spec" > "$TEMPLATE_FILE"
# fi

# if [ -f "$TASKS_TEMPLATE" ]; then
#     cp "$TASKS_TEMPLATE" "$TASKS_FILE"
# else
#     echo "# Tasks" > "$TASKS_FILE"
# fi

# # Remplacement dynamique des IDs dans les fichiers copiés (Compatible Linux/Windows/macOS)
# perl -pi -e "s/doc-pipeline-###/${WORKFLOW_ID}/g" "$TEMPLATE_FILE" "$TASKS_FILE" 2>/dev/null || true

# # Conversion des chemins en style UNIX/Git Bash si nécessaire
# TEMPLATE_FILE_ABS=$(cd "$(dirname "$TEMPLATE_FILE")" && pwd)/$(basename "$TEMPLATE_FILE")
# TASKS_FILE_ABS=$(cd "$(dirname "$TASKS_FILE")" && pwd)/$(basename "$TASKS_FILE")

# # Sortie au format JSON pour Claude Code
# if $JSON_MODE; then
#     printf '{"WORKFLOW_ID":"%s","BRANCH_NAME":"%s","TEMPLATE_FILE":"%s","TASKS_FILE":"%s","WORKFLOW_NUM":"%s"}\n' \
#         "$WORKFLOW_ID" "$BRANCH_NAME" "$TEMPLATE_FILE_ABS" "$TASKS_FILE_ABS" "$WORKFLOW_NUM"
# else
#     echo "WORKFLOW_ID: $WORKFLOW_ID"
#     echo "BRANCH_NAME: $BRANCH_NAME"
#     echo "TEMPLATE_FILE: $TEMPLATE_FILE_ABS"
#     echo "TASKS_FILE: $TASKS_FILE_ABS"
#     echo "WORKFLOW_NUM: $WORKFLOW_NUM"
# fi