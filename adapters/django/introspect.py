"""Introspection des modèles Django vers des attributs d'objet Table (lot 5).

Étape 1 du scénario de démonstration : « importer les modèles Django du
projet, les tables apparaissent avec leur schéma ». Lecture seule — ne
touche jamais à l'ORM en écriture, seulement à `_meta` pour décrire le
schéma.
"""


def table_attributes(model):
    """Construit les attributs ``{"name", "fields"}`` d'un objet Table à partir
    d'un modèle Django (conforme au schéma du type ``Table``, voir ``seed_demo``).
    """
    fields = list(model._meta.fields) + list(model._meta.many_to_many)
    return {
        "name": model.__name__,
        "fields": [
            {"name": field.name, "type": field.get_internal_type(), "nullable": bool(field.null)}
            for field in fields
        ],
    }
