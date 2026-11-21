# Divergences attendues

Référence pour mesurer « aucune divergence manquée sur les cas préparés,
peu de fausses alertes ». Chaque cas contradictoire décrit un changement
technique réel (ou hypothétique mais plausible sur le schéma actuel) qui
contredit une exigence d'un mail. Les cas de contrôle décrivent un
changement qui respecte l'exigence : ils ne doivent **pas** déclencher de
`Divergence`.

## Cas contradictoires (doivent déclencher une Divergence)

### D1 — traçabilité auteur/agent

- **Exigence** : mail `01`, « jamais les deux en même temps sur le même
  changement ».
- **Changement technique** : une migration qui assouplit la contrainte
  `version_author_xor_agent_name` sur `Version` (autoriser `author` et
  `agent_name` renseignés ensemble).
- **Contradiction** : l'exigence interdit explicitement qu'une
  modification porte les deux signatures à la fois.

### D2 — un seul regard par vue

- **Exigence** : mail `02`, « un seul regard par personne sur un composant
  à la fois, pas plusieurs qui s'empilent ».
- **Changement technique réel** : `Typing.Meta.constraints` n'impose
  l'unicité que sur `(object, layer, type)` — rien n'empêche plusieurs
  lignes `Typing` pour le même `(object, layer)` avec des `type`
  différents.
- **Contradiction** : le schéma autorise plusieurs typages simultanés dans
  la même vue pour le même composant, alors que l'exigence en veut un seul.

### D3 — dépendance vers une itération précise

- **Exigence** : mail `03`, « une dépendance doit toujours pointer vers
  une itération précise ».
- **Changement technique réel** : `Link.version` est `null=True,
  blank=True`.
- **Contradiction** : le schéma autorise une dépendance sans itération
  précisée.

### D4 — provenance qui survit à la suppression du fichier

- **Exigence** : mail `04`, « ne jamais perdre la trace qu'une itération
  en est issue » même si le fichier source est supprimé.
- **Changement technique réel** : `Provenance.source_blob` a
  `on_delete=models.SET_NULL`.
- **Contradiction** : supprimer le `Blob` met `source_blob` à `NULL` sans
  laisser de trace de ce qu'il y avait avant.

### D5 — écart jamais résolu tout seul

- **Exigence** : mail `06`, « il ne faut surtout pas que l'outil essaie de
  deviner qui a raison et corrige ça tout seul ».
- **Changement technique hypothétique** : un aspect qui passe
  automatiquement une `Divergence` à `resolved` dès qu'une nouvelle
  itération est déposée sur un des composants concernés.
- **Contradiction** : correction automatique et silencieuse d'un écart,
  contraire à l'exigence et à la règle d'architecture n°8 (CLAUDE.md).

## Cas de contrôle (ne doivent pas déclencher de Divergence)

### N1 — alertes par vue

- **Exigence** : mail `05`, chaque vue peut définir ses propres règles
  d'alerte.
- **Changement technique** : `Aspect.layer` est une clé étrangère
  obligatoire vers `Layer`, `pointcut`/`action` en JSON libre par aspect.
- **Conformité** : chaque vue peut effectivement déclarer ses propres
  règles, sans configuration globale partagée.

### N2 — distinguer humain et agent

- **Exigence** : mail `01`, savoir si un changement vient d'une personne
  ou d'un automatisme.
- **Changement technique** : `Version.nature` (`human`/`agent`) combiné à
  la contrainte `version_author_xor_agent_name` actuelle (non modifiée).
- **Conformité** : correspond exactement à l'exigence, rien à signaler.

### N3 — fichiers volumineux séparés des attributs

- **Exigence** : mail `04`, pouvoir joindre des fichiers volumineux sans
  ralentir le reste.
- **Changement technique** : `Blob` est une table séparée adressée par
  `sha256`, distincte de `Version.attributes`.
- **Conformité** : les fichiers ne transitent jamais par les attributs
  édités en continu, l'exigence est respectée.
