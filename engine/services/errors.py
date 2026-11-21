class VersionConflict(Exception):
    """L'écriture optimiste a échoué : la version lue n'est plus la version courante."""

    def __init__(self, current_version):
        self.current_version = current_version
        super().__init__(
            f"version attendue dépassée, version courante = {current_version.number}"
        )


class SchemaValidationError(Exception):
    """Les attributs fournis ne respectent pas le schéma effectif du type."""

    def __init__(self, errors):
        self.errors = errors
        super().__init__("; ".join(errors))
