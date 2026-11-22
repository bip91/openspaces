<script>
  // Prototype jetable : fusion des deux prototypes précédents (bande
  // d'espaces + fenêtrage glissable/accrochable), pas branché sur le vrai
  // moteur, données bidon. Teste l'ensemble ensemble, pas chaque geste isolé.

  let spaces = [
    { id: "demo", name: "démo", color: "#6b7280" },
    { id: "lumen", name: "Refonte boutique Lumen", color: "#2563eb" },
    { id: "acme", name: "Client ACME", color: "#16a34a" },
  ];
  let activeSpaceId = "demo";
  let dragOverSpaceId = null;

  let objects = [
    { id: 1, name: "commande", spaceId: "demo" },
    { id: 2, name: "délai obligatoire", spaceId: "demo" },
    { id: 3, name: "cas-usage-directeur", spaceId: "demo" },
    { id: 4, name: "devis-acme-03", spaceId: "acme" },
    { id: 5, name: "contrat-lumen", spaceId: "lumen" },
  ];

  $: activeObjects = objects.filter((o) => o.spaceId === activeSpaceId);

  // --- Menu radial des verbes universels (clic droit sur un objet) ---
  // Sept verbes : la taille où un menu radial reste lisible (spec : « sept ou
  // huit verbes universels »). Pas de « créer » ici — on agit sur un objet
  // déjà là, pas sur du vide.
  const VERBS = ["Voir", "Modifier", "Lier", "Classer", "Typer", "Décider", "Historique"];
  let radialMenu = null; // { x, y, objectName } | null
  let lastAction = "";

  function sliceOffset(index, total, radius = 76) {
    const angle = (2 * Math.PI * index) / total - Math.PI / 2;
    return { dx: Math.cos(angle) * radius, dy: Math.sin(angle) * radius };
  }

  function openRadialMenu(event, objectName) {
    event.preventDefault();
    radialMenu = { x: event.clientX, y: event.clientY, objectName };
  }

  function closeRadialMenu() {
    radialMenu = null;
  }

  function chooseVerb(verb) {
    lastAction = `${verb} — ${radialMenu.objectName}`;
    closeRadialMenu();
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (lastAction = ""), 2200);
    if (verb === "Historique") openHistoryWindow();
  }
  let toastTimer;

  // --- Prompt global (barre du bas) : simulation scriptée, pas de vraie IA
  // ni de clé d'API dans ce bundle client — choisi en conversation plutôt que
  // de risquer une clé exposée dans un prototype jetable. « Toujours le
  // prompt en première ligne, le contextuel dessous » : réalisé ici pour de
  // vrai, pas juste discuté.
  let promptText = "";
  let promptResponse = "";

  function openHistoryWindow() {
    windows = windows.map((w) => (w.id === "historique" ? { ...w, open: true } : w));
    bringToFront("historique");
  }

  function submitPrompt() {
    const text = promptText.trim().toLowerCase();
    if (!text) return;
    if (text.includes("exigence") || text.includes("extrai")) {
      promptResponse = "2 exigences extraites (simulation) — voir la fenêtre Objets.";
    } else if (text.includes("lien")) {
      promptResponse = "1 lien proposé vers « commande » (simulation).";
    } else if (text.includes("historique")) {
      promptResponse = "Historique ouvert (simulation).";
      openHistoryWindow();
    } else if (text.includes("espace")) {
      promptResponse = `Espace actif : « ${spaces.find((s) => s.id === activeSpaceId)?.name} » (simulation).`;
    } else {
      promptResponse = "Je ne sais pas encore faire ça (simulation).";
    }
    promptText = "";
  }

  const linkLines = [
    "délai obligatoire --correspondence--> commande",
    "commande --classification--> classeur-démo",
  ];
  const busLines = [
    "create_object @ harnais-web -> autorisé (23 ms)",
    "create_object @ lecteur-demo -> refusé (forbidden)",
  ];
  const historyLines = [
    "v3 — agent (qwen2.5:1.5b) — 21/11 23:36",
    "v2 — humain (demo) — 21/11 22:17",
    "v1 — humain (demo) — 21/11 22:16",
  ];

  let nextZ = 1;
  let windows = [
    { id: "objets", title: "Objets", x: 100, y: 50, width: 340, height: 260, z: nextZ++, open: true },
    { id: "liens", title: "Liens", x: 500, y: 110, width: 340, height: 200, z: nextZ++, open: true },
    { id: "bus", title: "Bus", x: 300, y: 330, width: 380, height: 190, z: nextZ++, open: false },
    { id: "historique", title: "Historique", x: 560, y: 340, width: 320, height: 180, z: nextZ++, open: false },
  ];

  function selectSpace(id) {
    activeSpaceId = id;
  }

  function onObjectDragStart(event, objectId) {
    event.dataTransfer.setData("text/plain", String(objectId));
    event.dataTransfer.effectAllowed = "move";
  }

  function onSpaceDragOver(event, spaceId) {
    event.preventDefault();
    dragOverSpaceId = spaceId;
  }

  function onSpaceDragLeave() {
    dragOverSpaceId = null;
  }

  function onSpaceDrop(event, spaceId) {
    event.preventDefault();
    const objectId = Number(event.dataTransfer.getData("text/plain"));
    objects = objects.map((o) => (o.id === objectId ? { ...o, spaceId } : o));
    dragOverSpaceId = null;
  }

  // --- Fenêtrage : déplacer, redimensionner, accrocher aux bords/coins ---

  let drag = null;
  let resize = null;
  let desktopEl;
  let activeZone = null;

  const EDGE = 28;
  const CORNER = 64;

  function computeZone(clientX, clientY, rect) {
    const x = clientX - rect.left;
    const y = clientY - rect.top;
    const nearTop = y < CORNER;
    const nearBottom = y > rect.height - CORNER;
    const nearLeft = x < CORNER;
    const nearRight = x > rect.width - CORNER;

    if (nearTop && nearLeft) return "top-left";
    if (nearTop && nearRight) return "top-right";
    if (nearBottom && nearLeft) return "bottom-left";
    if (nearBottom && nearRight) return "bottom-right";
    if (y < EDGE) return "maximize";
    if (x < EDGE) return "left";
    if (x > rect.width - EDGE) return "right";
    return null;
  }

  function zoneRect(zone, w, h) {
    switch (zone) {
      case "left":
        return { x: 0, y: 0, width: w / 2, height: h };
      case "right":
        return { x: w / 2, y: 0, width: w / 2, height: h };
      case "maximize":
        return { x: 0, y: 0, width: w, height: h };
      case "top-left":
        return { x: 0, y: 0, width: w / 2, height: h / 2 };
      case "top-right":
        return { x: w / 2, y: 0, width: w / 2, height: h / 2 };
      case "bottom-left":
        return { x: 0, y: h / 2, width: w / 2, height: h / 2 };
      case "bottom-right":
        return { x: w / 2, y: h / 2, width: w / 2, height: h / 2 };
      default:
        return null;
    }
  }

  function bringToFront(id) {
    nextZ += 1;
    windows = windows.map((w) => (w.id === id ? { ...w, z: nextZ } : w));
  }

  function toggleWindow(id) {
    windows = windows.map((w) => (w.id === id ? { ...w, open: !w.open } : w));
    if (windows.find((w) => w.id === id)?.open) bringToFront(id);
  }

  function onTitlePointerDown(event, win) {
    bringToFront(win.id);
    drag = { id: win.id, startX: event.clientX, startY: event.clientY, originX: win.x, originY: win.y };
    window.addEventListener("pointermove", onDragMove);
    window.addEventListener("pointerup", onDragEnd);
  }

  function onDragMove(event) {
    if (!drag) return;
    const dx = event.clientX - drag.startX;
    const dy = event.clientY - drag.startY;
    windows = windows.map((w) => (w.id === drag.id ? { ...w, x: drag.originX + dx, y: drag.originY + dy } : w));
    const rect = desktopEl.getBoundingClientRect();
    activeZone = computeZone(event.clientX, event.clientY, rect);
  }

  function onDragEnd() {
    if (activeZone && desktopEl) {
      const rect = desktopEl.getBoundingClientRect();
      const target = zoneRect(activeZone, rect.width, rect.height);
      windows = windows.map((w) => (w.id === drag.id ? { ...w, ...target } : w));
    }
    activeZone = null;
    drag = null;
    window.removeEventListener("pointermove", onDragMove);
    window.removeEventListener("pointerup", onDragEnd);
  }

  function onResizePointerDown(event, win) {
    event.stopPropagation();
    bringToFront(win.id);
    resize = { id: win.id, startX: event.clientX, startY: event.clientY, originW: win.width, originH: win.height };
    window.addEventListener("pointermove", onResizeMove);
    window.addEventListener("pointerup", onResizeEnd);
  }

  function onResizeMove(event) {
    if (!resize) return;
    const dx = event.clientX - resize.startX;
    const dy = event.clientY - resize.startY;
    windows = windows.map((w) =>
      w.id === resize.id
        ? { ...w, width: Math.max(220, resize.originW + dx), height: Math.max(140, resize.originH + dy) }
        : w
    );
  }

  function onResizeEnd() {
    resize = null;
    window.removeEventListener("pointermove", onResizeMove);
    window.removeEventListener("pointerup", onResizeEnd);
  }
</script>

<div class="shell">
  <nav class="strip" aria-label="Espaces">
    {#each spaces as space (space.id)}
      <button
        class="space-icon"
        class:active={space.id === activeSpaceId}
        class:drag-over={space.id === dragOverSpaceId}
        style="--color: {space.color}"
        title={space.name}
        on:click={() => selectSpace(space.id)}
        on:dragover={(e) => onSpaceDragOver(e, space.id)}
        on:dragleave={onSpaceDragLeave}
        on:drop={(e) => onSpaceDrop(e, space.id)}
      >
        {space.name.slice(0, 1).toUpperCase()}
      </button>
    {/each}
  </nav>

  <main>
    <div class="desktop" bind:this={desktopEl}>
      {#if activeZone}
        {@const preview = zoneRect(activeZone, desktopEl.clientWidth, desktopEl.clientHeight)}
        <div
          class="snap-preview"
          style="left:{preview.x}px; top:{preview.y}px; width:{preview.width}px; height:{preview.height}px"
        ></div>
      {/if}

      {#each windows.filter((w) => w.open) as win (win.id)}
        <section
          class="window"
          style="left:{win.x}px; top:{win.y}px; width:{win.width}px; height:{win.height}px; z-index:{win.z}"
          on:pointerdown={() => bringToFront(win.id)}
        >
          <header on:pointerdown={(e) => onTitlePointerDown(e, win)}>
            <span>{win.title}</span>
            <button class="close" on:click={() => toggleWindow(win.id)} aria-label="Fermer">×</button>
          </header>
          <div class="body">
            {#if win.id === "objets"}
              <p class="hint">
                Glisse une carte sur une bulle d'espace pour la déplacer. Clic
                droit pour le menu des verbes.
              </p>
              {#each activeObjects as object (object.id)}
                <div
                  class="object-card"
                  draggable="true"
                  on:dragstart={(e) => onObjectDragStart(e, object.id)}
                  on:contextmenu={(e) => openRadialMenu(e, object.name)}
                >
                  {object.name}
                </div>
              {:else}
                <p class="empty">Aucun objet dans cet espace.</p>
              {/each}
            {:else if win.id === "liens"}
              {#each linkLines as line}<p>{line}</p>{/each}
            {:else if win.id === "historique"}
              {#each historyLines as line}<p>{line}</p>{/each}
            {:else}
              {#each busLines as line}<p>{line}</p>{/each}
            {/if}
          </div>
          <div
            class="resize-handle"
            role="button"
            tabindex="0"
            aria-label="Redimensionner"
            on:pointerdown={(e) => onResizePointerDown(e, win)}
          ></div>
        </section>
      {/each}
    </div>

    <div class="bottombar">
      <form class="promptbar" on:submit|preventDefault={submitPrompt}>
        <input
          type="text"
          placeholder="Demande quelque chose (ex. « extraire les exigences », « ouvrir l'historique »)…"
          bind:value={promptText}
        />
        <button type="submit">Envoyer</button>
      </form>
      {#if promptResponse}
        <p class="prompt-response">{promptResponse}</p>
      {/if}
      <nav class="dock" aria-label="Fenêtres">
        {#each windows as win (win.id)}
          <button class:open={win.open} on:click={() => toggleWindow(win.id)}>{win.title}</button>
        {/each}
      </nav>
    </div>
  </main>
</div>

{#if radialMenu}
  <div
    class="radial-overlay"
    role="button"
    tabindex="0"
    aria-label="Fermer le menu"
    on:click={closeRadialMenu}
    on:contextmenu|preventDefault={closeRadialMenu}
    on:keydown={(e) => e.key === "Escape" && closeRadialMenu()}
  >
    <div class="radial-menu" style="left:{radialMenu.x}px; top:{radialMenu.y}px">
      <div class="radial-center">{radialMenu.objectName}</div>
      {#each VERBS as verb, i}
        {@const offset = sliceOffset(i, VERBS.length)}
        <button
          class="radial-slice"
          style="transform: translate({offset.dx}px, {offset.dy}px) translate(-50%, -50%)"
          on:click|stopPropagation={() => chooseVerb(verb)}
        >
          {verb}
        </button>
      {/each}
    </div>
  </div>
{/if}

{#if lastAction}
  <div class="toast">{lastAction}</div>
{/if}

<style>
  :global(body) {
    margin: 0;
    font-family: system-ui, sans-serif;
    background: #e5e7eb;
    color: #1a1a1a;
  }

  .shell {
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

  main {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .desktop {
    position: relative;
    flex: 1;
    overflow: hidden;
  }

  .snap-preview {
    position: absolute;
    background: rgba(37, 99, 235, 0.18);
    border: 2px solid rgba(37, 99, 235, 0.6);
    border-radius: 4px;
    pointer-events: none;
    transition: all 0.08s ease;
  }

  .window {
    position: absolute;
    display: flex;
    flex-direction: column;
    background: #fff;
    border: 1px solid #c7c7c7;
    border-radius: 8px;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
    overflow: hidden;
  }

  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.4rem 0.6rem;
    background: #f3f4f6;
    border-bottom: 1px solid #e0e0e0;
    cursor: move;
    font-size: 0.85rem;
    font-weight: 600;
    user-select: none;
  }

  .close {
    border: none;
    background: transparent;
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    color: #888;
  }
  .close:hover {
    color: #c00;
  }

  .body {
    flex: 1;
    padding: 0.5rem 0.75rem;
    font-size: 0.85rem;
    overflow: auto;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .body p {
    margin: 0.2rem 0;
    color: #444;
  }
  .hint {
    color: #999;
    font-size: 0.75rem;
  }
  .empty {
    color: #aaa;
  }

  .object-card {
    padding: 0.45rem 0.7rem;
    background: #f9fafb;
    border: 1px solid #ddd;
    border-radius: 6px;
    cursor: grab;
    font-size: 0.85rem;
    width: fit-content;
  }

  .resize-handle {
    position: absolute;
    right: 0;
    bottom: 0;
    width: 14px;
    height: 14px;
    cursor: nwse-resize;
    background: linear-gradient(135deg, transparent 50%, #bbb 50%);
  }

  .bottombar {
    background: #fff;
    border-top: 1px solid #ddd;
  }

  .promptbar {
    display: flex;
    gap: 0.5rem;
    padding: 0.6rem 0.6rem 0;
  }
  .promptbar input {
    flex: 1;
    padding: 0.5rem 0.7rem;
    border-radius: 6px;
    border: 1px solid #ccc;
    font-size: 0.85rem;
  }
  .promptbar button {
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid #2563eb;
    background: #2563eb;
    color: #fff;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .prompt-response {
    margin: 0.4rem 0.6rem 0;
    font-size: 0.8rem;
    color: #555;
  }

  .dock {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    padding: 0.6rem;
  }
  .dock button {
    padding: 0.4rem 0.9rem;
    border-radius: 6px;
    border: 1px solid #ccc;
    background: #f3f4f6;
    font-size: 0.85rem;
    cursor: pointer;
  }
  .dock button.open {
    background: #2563eb;
    border-color: #2563eb;
    color: #fff;
  }

  .radial-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: transparent;
    border: none;
    padding: 0;
  }

  .radial-menu {
    position: absolute;
    width: 0;
    height: 0;
  }

  .radial-center {
    position: absolute;
    left: 0;
    top: 0;
    transform: translate(-50%, -50%);
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: #1f2937;
    color: #fff;
    font-size: 0.65rem;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 0.2rem;
    overflow: hidden;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
  }

  .radial-slice {
    position: absolute;
    left: 0;
    top: 0;
    width: 64px;
    height: 40px;
    border-radius: 20px;
    border: 1px solid #ddd;
    background: #fff;
    font-size: 0.75rem;
    cursor: pointer;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.15);
    transition: background 0.08s ease, color 0.08s ease;
  }
  .radial-slice:hover {
    background: #2563eb;
    color: #fff;
  }

  .toast {
    position: fixed;
    bottom: 70px;
    left: 50%;
    transform: translateX(-50%);
    background: #1f2937;
    color: #fff;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    font-size: 0.85rem;
    z-index: 1100;
  }
</style>
