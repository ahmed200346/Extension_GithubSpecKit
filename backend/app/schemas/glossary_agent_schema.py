# app/schemas/glossary_schema.py
"""
glossary_schema.py — Modèle de validation Pydantic v2 pour le Glossary Agent.
Aligné sur la topologie du graphe d'ingestion (éléments, identifiants, attributs).
"""

from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class TermCategory(str, Enum):
    BUSINESS_DOMAIN = "BUSINESS_DOMAIN"   
    TECHNICAL_STACK = "TECHNICAL_STACK"   

class DiscoveryType(str, Enum):
    EXPLICIT = "EXPLICIT"   
    IMPLICIT = "IMPLICIT"   

class GlossaryItem(BaseModel):
    """
    Modèle de validation atomique pour un élément du glossaire.
    Contraint par la topologie géométrique et les attributs du Parsing Agent.
    """
    term: str = Field(
        ..., 
        description=(
            "Le jeton technique exact, l'acronyme ou le nom brut de l'entité métier trouvé dans le graphe. "
            "Doit appliquer la politique anti-décoration nominale stricte : aucun formatage, "
            "aucune extension d'acronyme entre parenthèses (ex: extraire 'JWT' et non 'JWT (JSON Web Token)')."
        )
    )
    category: TermCategory = Field(
        ..., 
        description=(
            "Classification catégorielle stricte du terme. "
            "Le LLM doit mapper vers 'BUSINESS_DOMAIN' les nœuds de type 'entity', 'user_story' ou 'functional_requirement'. "
            "Il doit mapper vers 'TECHNICAL_STACK' les nœuds de type 'tool_configuration' ou 'architecture_choice'."
        )
    )
    discovery: DiscoveryType = Field(
        ..., 
        description=(
            "Type de découverte sémantique du concept. "
            "Renseigner 'EXPLICIT' si la technologie ou l'entité is nommée textuellement dans un nœud du graphe. "
            "Renseigner 'IMPLICIT' si le standard (ex: ISO 8601, RBAC, CORS) est activement moissonné "
            "en déduisant sa nécessité depuis les règles, plages numériques ou contraintes de sécurité d'un nœud."
        )
    )
    contextual_anchor: str = Field(
        ..., 
        description=(
            "L'ancre physique garantissant la traçabilité géométrique. "
            "Le LLM doit obligatoirement y renseigner la valeur textuelle exacte du champ 'identifier' "
            "du nœud d'origine (ex: FR-001, CON-03, US-02) ou le titre exact de la section source."
        )
    )
    project_definition: str = Field(
        ..., 
        description=(
            "Définition opérationnelle à haute densité, confinée exclusivement aux limites du projet. "
            "Doit intégrer les attributs numériques et règles métiers portés par le nœud. "
            "RÈGLE STRICTE ANTI-TAUTOLOGIE : Interdiction absolue de réutiliser la chaîne du champ 'term' "
            "(insensible à la casse), ses sous-composants ou ses variables d'environnement dérivées (ex: pas de RESEND_API_KEY "
            "si le terme est 'Resend') à l'intérieur de cette définition."
        )
    )

class GlossaryOutputModel(BaseModel):
    """
    Modèle de validation principal pour la sortie du Glossary & Technology Anchor Agent.
    Garantit l'ancrage conceptuel sans hallucination sémantique.
    """
    project_name: str = Field(
        ..., 
        description=(
            "L'identité formelle de l'application. Doit être extraite au caractère près "
            "depuis le champ 'project_info.project_name' du graphe de métadonnées du parser."
        )
    )
    items: List[GlossaryItem] = Field(
        ..., 
        description=(
            "Liste normalisée et déterministe de termes et de standards technologiques, "
            "obtenue par la traversée systématique des nœuds et des attributs du graphe d'ingestion."
        )
    )
# # app/schemas/glossary_schema.py
# """
# glossary_schema.py — Modèle de validation Pydantic v2 pour le Glossary Agent.
# Aligné sur la topologie du graphe d'ingestion (éléments, identifiants, attributs).
# """

# from pydantic import BaseModel, Field
# from typing import List
# from enum import Enum

# class TermCategory(str, Enum):
#     BUSINESS_DOMAIN = "BUSINESS_DOMAIN"   
#     TECHNICAL_STACK = "TECHNICAL_STACK"   

# class DiscoveryType(str, Enum):
#     EXPLICIT = "EXPLICIT"   
#     IMPLICIT = "IMPLICIT"   

# class GlossaryItem(BaseModel):
#     """
#     Modèle de validation atomique pour un élément du glossaire.
#     Contraint par la topologie géométrique et les attributs du Parsing Agent.
#     """
#     term: str = Field(
#         ..., 
#         description=(
#             "Le jeton technique exact, l'acronyme ou le nom brut de l'entité métier trouvé dans le graphe. "
#             "Doit appliquer la politique anti-décoration nominale stricte : aucun formatage, "
#             "aucune extension d'acronyme entre parenthèses (ex: extraire 'JWT' et non 'JWT (JSON Web Token)')."
#         )
#     )
#     category: TermCategory = Field(
#         ..., 
#         description=(
#             "Classification catégorielle stricte du terme. "
#             "Le LLM doit mapper vers 'BUSINESS_DOMAIN' les nœuds de type 'entity', 'user_story' ou 'functional_requirement'. "
#             "Il doit mapper vers 'TECHNICAL_STACK' les nœuds de type 'tool_configuration' ou 'architecture_choice'."
#         )
#     )
#     discovery: DiscoveryType = Field(
#         ..., 
#         description=(
#             "Type de découverte sémantique du concept. "
#             "Renseigner 'EXPLICIT' si la technologie ou l'entité est nommée textuellement dans un nœud du graphe. "
#             "Renseigner 'IMPLICIT' si le standard (ex: ISO 8601, RBAC, CORS) est activement moissonné "
#             "en déduisant sa nécessité depuis les règles, plages numériques ou contraintes de sécurité d'un nœud."
#         )
#     )
#     contextual_anchor: str = Field(
#         ..., 
#         description=(
#             "L'ancre physique garantissant la traçabilité géométrique. "
#             "Le LLM doit obligatoirement y renseigner la valeur textuelle exacte du champ 'identifier' "
#             "du nœud d'origine (ex: FR-001, CON-03, US-02) ou le titre exact de la section source."
#         )
#     )
#     project_definition: str = Field(
#         ..., 
#         description=(
#             "Définition opérationnelle à haute densité, confinée exclusivement aux limites du projet. "
#             "Doit intégrer les attributs numériques et règles métiers portés par le nœud. "
#             "RÈGLE STRICTE ANTI-TAUTOLOGIE : Interdiction absolue de réutiliser la chaîne du champ 'term' "
#             "(insensible à la casse) ou ses variantes grammaticales à l'intérieur de cette définition."
#         )
#     )

# class GlossaryOutputModel(BaseModel):
#     """
#     Modèle de validation principal pour la sortie du Glossary & Technology Anchor Agent.
#     Garantit l'ancrage conceptuel sans hallucination sémantique.
#     """
#     project_name: str = Field(
#         ..., 
#         description=(
#             "L'identité formelle de l'application. Doit être extraite au caractère près "
#             "depuis le champ 'project_info.project_name' du graphe de métadonnées du parser."
#         )
#     )
#     items: List[GlossaryItem] = Field(
#         ..., 
#         description=(
#             "Liste normalisée et déterministe de termes et de standards technologiques, "
#             "obtenue par la traversée systématique des nœuds et des attributs du graphe d'ingestion."
#         )
#     )
