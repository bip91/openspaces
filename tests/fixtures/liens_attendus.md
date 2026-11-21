# Liens attendus

Référence des correspondances exigence ↔ table/champ, pour comparer aux
liens proposés par l'opération IA de proposition de liens (lot 4). Sert à
mesurer « liens proposés acceptés majoritairement sans saisie manuelle ».

| Mail | Exigence (résumé) | Table(s) / champ(s) attendu(s) |
| --- | --- | --- |
| 01 | signer un changement par une personne ou un agent, jamais les deux | `Version.author`, `Version.agent_name`, `Version.nature` |
| 01 | lister tous les changements d'un composant, dans l'ordre | `Version` (via `Object.versions`), `Event` |
| 02 | un regard différent par vue, sans mélange | `Typing`, `Layer`, `ObjectType` |
| 02 | ne pas écraser le regard d'une autre vue | `Typing.layer` (portée par calque) |
| 03 | dépendance typée entre deux composants | `Link.nature`, `Link.source`, `Link.target` |
| 03 | dépendance vers une itération précise | `Link.version` |
| 04 | fichiers volumineux séparés des attributs | `Blob` |
| 04 | garder la trace même si le fichier est supprimé | `Provenance.source_blob`, `Provenance.anchor` |
| 05 | être alerté d'un changement sur un composant utilisé | `Aspect.pointcut`, `Aspect.action` |
| 05 | règles d'alerte propres à chaque vue | `Aspect.layer` |
| 06 | écart entre vues signalé et visible | `Divergence.description`, `Divergence.status` |
| 06 | jamais corrigé automatiquement | `Divergence.status` (transition `open` → `resolved` toujours explicite) |
| 07 | retrouver un composant sans son nom exact | `Embedding` *(ambigu : voir note)* |
| 08 | signature double personne + agent sur une itération | contredit `Version` (contrainte `version_author_xor_agent_name`) — pas un lien, un cas de `divergences_attendues.md` (D1) |
| 09 | garder trace des suggestions et de leur décision | `Proposal.input`, `Proposal.output`, `Proposal.decision` |

**Note (mail 07, ambigu)** : si l'extraction retient l'interprétation
« recherche plein texte », le lien attendu serait plutôt vers les attributs
indexés de `Version` que vers `Embedding`. Les deux interprétations sont
acceptables pour la mesure du critère ; consigner laquelle a été retenue.
