De : Youssef (lead front)
À : l'équipe outillage
Objet : Dépendances entre composants

Quand un composant dépend d'un autre (par exemple une icône qui dépend
d'une palette de couleurs), je veux qu'on puisse l'enregistrer, avec le
type de dépendance (« utilise », « remplace », etc.).

Important : une dépendance doit toujours pointer vers une itération
précise du composant dont elle dépend, pas vers le composant « en
général ». Sinon, le jour où on regarde l'historique, on ne saura pas
quelle version exacte était visée au moment où la dépendance a été créée,
et ça fausse toute analyse d'impact plus tard.
