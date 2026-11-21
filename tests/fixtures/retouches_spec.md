# Retouches de spec

Dix modifications en prose, de la plus simple à la plus floue, avec la
traduction attendue sur le modèle (`engine/models.py`). Sert à mesurer
« au moins deux tiers des réinterprétations acceptées, telles quelles ou
après retouche mineure ».

1. **« Renommez le champ `role` du calque en `point_de_vue`. »**
   Traduction attendue : renommer `Layer.role` → `Layer.point_de_vue`
   (migration de renommage de colonne).

2. **« Le champ `shared` d'une vue doit s'appeler `visible_client`. »**
   Traduction attendue : renommer `Layer.shared` → `Layer.visible_client`
   (migration de renommage de colonne, type inchangé).

3. **« Ajoutez une date de dernière modification sur chaque composant, pas
   seulement sur l'itération. »**
   Traduction attendue : ajouter `Object.updated_at`
   (`DateTimeField(auto_now=True)`).

4. **« On veut pouvoir donner un titre court à une dépendance, en plus de
   sa nature. »**
   Traduction attendue : ajouter `Link.label`
   (`CharField(max_length=255, blank=True)`).

5. **« Les fichiers joints doivent garder le nom d'origine du fichier, pas
   seulement son empreinte. »**
   Traduction attendue : ajouter `Blob.original_name`
   (`CharField(max_length=255)`).

6. **« Quand on signale un écart de lecture, il faut pouvoir dire qui l'a
   signalé. »**
   Traduction attendue : ajouter `Divergence.reported_by`
   (`ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
   on_delete=models.SET_NULL)`).

7. **« Il faut qu'on puisse savoir combien de temps une suggestion de l'IA
   a mis à arriver. »**
   Traduction attendue : **aucun changement** — `Proposal.duration_ms`
   existe déjà. Cas piège : vérifie que la réinterprétation reconnaît
   qu'une exigence est déjà couverte plutôt que de proposer un doublon.

8. **« Les gens doivent pouvoir dire si une suggestion de l'IA est "presque
   bonne" et pas juste accepter ou refuser. »** *(flou)*
   Deux traductions plausibles, à retenir toutes les deux comme
   acceptables :
   - réutiliser `Proposal.decision = MODIFIED` (déjà présent) et documenter
     que « presque bonne, retouchée » correspond à ce choix ;
   - ou ajouter un champ dédié (ex. `Proposal.quality_rating`) si on juge
     `MODIFIED` insuffisant.

9. **« Rendez le suivi des dépendances plus souple, pour qu'on puisse
   aussi dire qu'un composant en remplace un autre. »** *(flou)*
   Traduction attendue : **aucun changement de schéma** —
   `Link.nature` est déjà un texte libre ; « remplace » est une nouvelle
   valeur possible, pas un nouveau champ. Cas piège : vérifie qu'on ne
   propose pas un champ ou une table en plus par réflexe.

10. **« On veut que l'outil soit plus intelligent sur les suggestions,
    qu'il comprenne mieux ce qu'on veut. »** *(le plus flou)*
    Traduction attendue : **pas de traduction sur le modèle** — relève de
    la qualité du modèle IA ou du prompt (lot 4), pas du schéma de
    données. Cas piège : vérifie que la réinterprétation sait refuser de
    produire un changement de modèle quand la demande n'en appelle pas un.
