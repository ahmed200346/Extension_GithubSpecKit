from pydantic import BaseModel, Field
from typing import List

class TechnicalStackSchema(BaseModel):
    """
    Sous-schéma détaillant la pile technique et ses contraintes physiques.
    Extrait directement depuis la topologie du graphe d'ingestion.
    """
    languages_and_frameworks: List[str] = Field(
        ...,
        description=(
            "Liste ordonnée des langages, frameworks et outils tiers explicitement nommés. "
            "Le LLM doit extraire ces informations en priorité depuis les nœuds de type 'tool_configuration' "
            "du dictionnaire 'elements' (ex: FastAPI, PostgreSQL, Alembic)."
        )
    )
    architectural_constraints: List[str] = Field(
        ...,
        description=(
            "Contraintes et décisions d'architecture fortes imposées au code. "
            "Le LLM doit obligatoirement analyser les nœuds de type 'constraint' et 'non_functional_requirement' "
            "pour lister ces règles (ex: exécution asynchrone obligatoire, isolation des tests de base de données)."
        )
    )

class SummaryOutputModel(BaseModel):
    """
    Modèle de validation principal pour la sortie du Summary Agent.
    Exploite la structure multi-dimensionnelle du Parsing Agent.
    """
    executive_brief: str = Field(
        ...,
        description=(
            "Synthèse macro de l'intention du système et de sa valeur métier. "
            "Doit fusionner les données de 'project_info' (nom, explication) et le 'doc_type' "
            "pour contextualiser le livrable en 3 ou 4 phrases techniques et assertives. Maximum 150 mots."
        )
    )
    technical_stack: TechnicalStackSchema = Field(
        ...,
        description="Détails de la pile technologique et des contraintes physiques extraites du graphe."
    )
    maturity_assessment: str = Field(
        ...,
        description=(
            "Évaluation narrative et objective de la viabilité technique du document. "
            "Doit obligatoirement qualifier l'état (ex: PRÊT, IMMATURE, ou CRITIQUE) "
            "en se basant explicitement sur le volume et la sévérité des éléments du tableau 'structural_gaps'."
        )
    )
    critical_dependencies: List[str] = Field(
        ...,
        description=(
            "Liste des dépendances techniques bloquantes, clés d'API requises ou flux externes. "
            "Le LLM doit obligatoirement identifier ces dépendances en parcourant le tableau 'relationships' "
            "et en ciblant les arcs de liaison de type 'depends_on' ou 'relates_to'."
        )
    )
# from pydantic import BaseModel, Field
# from typing import List

# class TechnicalStackSchema(BaseModel):
#     """
#     Sous-schéma détaillant la pile technique et ses contraintes physiques.
#     """
#     languages_and_frameworks: List[str] = Field(
#         ...,
#         description=(
#             "Liste ordonnée des langages, frameworks, bibliothèques et outils tiers "
#             "explicitement mentionnés (ex: FastAPI, PostgreSQL, LocalStorage, Resend)."
#         )
#     )
#     architectural_constraints: List[str] = Field(
#         ...,
#         description=(
#             "Contraintes physiques et décisions architecturales fortes imposées par le projet "
#             "(ex: absence d'authentification, architecture asynchrone, persistance locale pure, etc.)."
#         )
#     )

# class SummaryOutputModel(BaseModel):
#     """
#     Modèle de validation principal pour la sortie du Summary Agent.
#     Garantit l'alignement strict avec summary_spec.json.
#     """
#     executive_brief: str = Field(
#         ...,
#         description=(
#             "Synthèse macro de l'intention de l'application et de sa valeur métier. "
#             "Doit être rédigée sur un ton technique et assertif en 3 ou 4 phrases maximum. "
#             "Aucune hallucination ou extrapolation fonctionnelle n'est autorisée."
#         )
#     )
#     technical_stack: TechnicalStackSchema = Field(
#         ...,
#         description="Détails de la pile technologique et des contraintes d'implémentation."
#     )
#     maturity_assessment: str = Field(
#         ...,
#         description=(
#             "Évaluation narrative et objective de la viabilité du document d'architecture. "
#             "Doit obligatoirement qualifier le projet (ex: PRÊT, IMMATURE, ou CRITIQUE) "
#             "en s'appuyant sur le nombre de 'structural_gaps' et d''open_questions' du projet."
#         )
#     )
#     critical_dependencies: List[str] = Field(
#         ...,
#         description=(
#             "Liste des dépendances bloquantes, des intégrations externes critiques, ou "
#             "des prérequis de configuration (ex: variables d'environnement pour clés d'API, limites physiques du LocalStorage)."
#         )
#     )