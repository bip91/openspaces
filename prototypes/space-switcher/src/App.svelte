<script>
  // Prototype jetable : bande d'espaces persistante (façon Arc), pas un menu
  // radial — décidé en conversation comme la meilleure réponse à « espaces
  // toujours accessibles, pas perturbant ». Données bidon, pas branché sur le
  // vrai moteur (voir docs/spec.md, le but est de sentir le geste, pas
  // d'intégrer).

  let spaces = [
    { id: "demo", name: "démo", color: "#6b7280" },
    { id: "lumen", name: "Refonte boutique Lumen", color: "#2563eb" },
    { id: "acme", name: "Client ACME", color: "#16a34a" },
  ];

  let objects = [
    { id: 1, name: "commande", spaceId: "demo" },
    { id: 2, name: "délai obligatoire", spaceId: "demo" },
    { id: 3, name: "devis-acme-03", spaceId: "acme" },
    { id: 4, name: "cas-usage-directeur", spaceId: "demo" },
    { id: 5, name: "contrat-lumen", spaceId: "lumen" },
  ];

  let activeSpaceId = "demo";
  let dragOverSpaceId = null;
  let draggedObjectId = null;

  $: activeObjects = objects.filter((o) => o.spaceId === activeSpaceId);

  function selectSpace(id) {
    activeSpaceId = id;
  }

  function onDragStart(event, objectId) {
    draggedObjectId = objectId;
    event.dataTransfer.setData("text/plain", String(objectId));
    event.dataTransfer.effectAllowed = "move";
  }

  function onDragOverSpace(event, spaceId) {
    event.preventDefault();
    dragOverSpaceId = spaceId;
  }

  function onDragLeaveSpace() {
    dragOverSpaceId = null;
  }

  function onDropOnSpace(event, spaceId) {
    event.preventDefault();
    const objectId = Number(event.dataTransfer.getData("text/plain"));
    objects = objects.map((o) => (o.id === objectId ? { ...o, spaceId } : o));
    dragOverSpaceId = null;
    draggedObjectId = null;
  }
</script>

<main>
  <nav class="strip" aria-label="Espaces">
    {#each spaces as space (space.id)}
      <button
        class="space-icon"
        class:active={space.id === activeSpaceId}
        class:drag-over={space.id === dragOverSpaceId}
        style="--color: {space.color}"
        title={space.name}
        on:click={() => selectSpace(space.id)}
        on:dragover={(e) => onDragOverSpace(e, space.id)}
        on:dragleave={onDragLeaveSpace}
        on:drop={(e) => onDropOnSpace(e, space.id)}
      >
        {space.name.slice(0, 1).toUpperCase()}
      </button>
    {/each}
  </nav>

  <section class="content">
    <h1>{spaces.find((s) => s.id === activeSpaceId)?.name}</h1>
    <p class="hint">
      Clique une autre bulle pour changer d'espace. Glisse une carte sur une
      bulle pour y déplacer l'objet.
    </p>
    <ul class="objects">
      {#each activeObjects as object (object.id)}
        <li
          class="object-card"
          class:dragging={object.id === draggedObjectId}
          draggable="true"
          on:dragstart={(e) => onDragStart(e, object.id)}
        >
          {object.name}
        </li>
      {/each}
      {#if activeObjects.length === 0}
        <li class="empty">Aucun objet dans cet espace.</li>
      {/if}
    </ul>
  </section>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: system-ui, sans-serif;
    background: #fafafa;
    color: #1a1a1a;
  }

  main {
    display: flex;
    height: 100vh;
  }

  .strip {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.6rem;
    width: 56px;
    padding: 1rem 0;
    background: #fff;
    border-right: 1px solid #ddd;
  }

  .space-icon {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 2px solid var(--color);
    background: #fff;
    color: var(--color);
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.12s ease, background 0.12s ease;
  }

  .space-icon:hover {
    transform: scale(1.08);
  }

  .space-icon.active {
    background: var(--color);
    color: #fff;
  }

  .space-icon.drag-over {
    transform: scale(1.2);
    box-shadow: 0 0 0 3px color-mix(in srgb, var(--color) 40%, transparent);
  }

  .content {
    flex: 1;
    padding: 1.5rem 2rem;
  }

  .hint {
    color: #777;
    font-size: 0.85rem;
  }

  .objects {
    list-style: none;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
  }

  .object-card {
    padding: 0.6rem 1rem;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    cursor: grab;
    font-size: 0.9rem;
  }

  .object-card.dragging {
    opacity: 0.4;
  }

  .empty {
    color: #aaa;
    font-size: 0.85rem;
  }
</style>
