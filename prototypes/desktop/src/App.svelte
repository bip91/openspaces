<script>
  import CommandMenu from "./CommandMenu.svelte";
  import { Cpu } from "@lucide/svelte";

  // Prototype jetable : fusion des prototypes précédents (bande d'espaces,
  // fenêtrage glissable/accrochable), pas branché sur le vrai moteur, données
  // bidon. Le menu radial a été remplacé par un menu contextuel générique
  // (prompt en haut, commandes principales dessous) — testé en vrai, pas
  // forcément plus clair qu'une liste.

  let spaces = [
    { id: "demo", name: "démo", color: "#6b7280" },
    { id: "lumen", name: "Refonte boutique Lumen", color: "#2563eb" },
    { id: "acme", name: "Client ACME", color: "#16a34a" },
  ];
  // Système n'est pas un espace de travail (pas d'activité, pas de dossiers,
  // pas de sélection) — juste un espace de plus dans la liste pour que ses
  // fonctions passent par le même menu clic-droit que les autres, plutôt
  // qu'une section d'icônes à part codée en dur.
  const SYSTEM_SPACE = { id: "system", name: "Système" };
  const SYSTEM_COMMANDS = ["Objets", "Liens", "Bus", "Paramètres"];

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

  // Dossiers épinglés : vivent dans un espace (même FK que tout le reste du
  // moteur réel), affichés sous la bulle de l'espace actif — navigation
  // fréquente, donc toujours visible, pas caché derrière un menu.
  let dossiers = [
    { id: 1, name: "Clients Lumen", spaceId: "lumen" },
    { id: 2, name: "Exigences", spaceId: "demo" },
  ];
  $: pinnedDossiers = dossiers.filter((d) => d.spaceId === activeSpaceId);

  let lastAction = "";
  let toastTimer;
  function flashAction(text) {
    lastAction = text;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (lastAction = ""), 2200);
  }

  // --- Menu contextuel générique (CommandMenu.svelte) ---

  let commandMenu = null; // { x, y, title, commands, onChoose } | null

  function closeCommandMenu() {
    commandMenu = null;
  }

  const OBJECT_COMMANDS = ["Voir", "Modifier", "Lier", "Classer", "Typer", "Décider", "Historique"];

  function openObjectMenu(event, objectName) {
    event.preventDefault();
    const { clientX: x, clientY: y } = event;
    commandMenu = {
      x,
      y,
      title: objectName,
      commands: OBJECT_COMMANDS,
      onChoose: (cmd) => handleObjectCommand(cmd, objectName, x, y),
    };
  }

  function handleObjectCommand(cmd, objectName, x, y) {
    if (cmd === "Historique") {
      closeCommandMenu();
      openHistoryWindow(objectName, x, y);
      return;
    }
    if (cmd === "Classer") {
      openClasserMenu(objectName, x, y);
      return;
    }
    closeCommandMenu();
    flashAction(`${cmd} — ${objectName}`);
  }

  function openClasserMenu(objectName, x, y) {
    const names = dossiers.filter((d) => d.spaceId === activeSpaceId).map((d) => d.name);
    commandMenu = {
      x,
      y,
      title: `Classer « ${objectName} » dans…`,
      commands: names.length ? names : ["(aucun dossier dans cet espace)"],
      onChoose: (dossierName) => {
        closeCommandMenu();
        flashAction(`Classé « ${objectName} » → « ${dossierName} »`);
      },
    };
  }

  const SPACE_COMMANDS = ["Nouveau dossier ici", "Renommer l'espace"];

  function openSpaceMenu(event, space) {
    event.preventDefault();
    const { clientX: x, clientY: y } = event;
    commandMenu = {
      x,
      y,
      title: space.name,
      commands: space.id === "system" ? SYSTEM_COMMANDS : SPACE_COMMANDS,
      onChoose: (cmd) => handleSpaceCommand(cmd, space),
    };
  }

  function handleSpaceCommand(cmd, space) {
    closeCommandMenu();
    if (cmd === "Objets" || cmd === "Liens" || cmd === "Bus") {
      toggleWindow(cmd === "Objets" ? "objets" : cmd === "Liens" ? "liens" : "bus");
      return;
    }
    if (cmd === "Paramètres") {
      flashAction("Paramètres — pas encore construit");
      return;
    }
    if (cmd === "Nouveau dossier ici") {
      const name = `Dossier ${dossiers.filter((d) => d.spaceId === space.id).length + 1}`;
      dossiers = [...dossiers, { id: Date.now(), name, spaceId: space.id }];
      flashAction(`Dossier « ${name} » créé dans « ${space.name} »`);
    } else {
      flashAction(`${cmd} (simulation) — « ${space.name} »`);
    }
  }

  // --- Prompt global (barre du bas) : simulation scriptée, pas de vraie IA
  // ni de clé d'API dans ce bundle client — choisi en conversation plutôt que
  // de risquer une clé exposée dans un prototype jetable. « Toujours le
  // prompt en première ligne, le contextuel dessous » : réalisé ici pour de
  // vrai, pas juste discuté.
  let promptText = "";
  let promptResponse = "";

  function openHistoryWindow(objectName, atX, atY) {
    windows = windows.map((w) =>
      w.id === "historique"
        ? {
            ...w,
            title: objectName ? `Historique — ${objectName}` : "Historique",
            x: atX != null ? atX - w.width / 2 : w.x,
            y: atY != null ? atY + 16 : w.y,
            open: true,
          }
        : w
    );
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
  <nav class="strip" aria-label="Espaces et outils système">
    <div class="strip-top">
      {#each spaces as space (space.id)}
        <button
          class="space-icon"
          class:active={space.id === activeSpaceId}
          class:drag-over={space.id === dragOverSpaceId}
          style="--color: {space.color}"
          title={space.name}
          on:click={() => selectSpace(space.id)}
          on:contextmenu={(e) => openSpaceMenu(e, space)}
          on:dragover={(e) => onSpaceDragOver(e, space.id)}
          on:dragleave={onSpaceDragLeave}
          on:drop={(e) => onSpaceDrop(e, space.id)}
        >
          {space.name.slice(0, 1).toUpperCase()}
        </button>
      {/each}

      <div class="pinned-dossiers">
        {#each pinnedDossiers as dossier (dossier.id)}
          <div class="dossier-badge" title={dossier.name}>{dossier.name.slice(0, 1).toUpperCase()}</div>
        {/each}
      </div>
    </div>

    <div class="strip-spacer"></div>

    <!-- Système : pas un espace de travail, juste un espace de plus dans la
    liste, en bas plutôt qu'à la suite des espaces de travail — ses fonctions
    (Objets, Liens, Bus, Paramètres) passent par le même menu que n'importe
    quel autre espace. Un seul clic suffit : pas de sélection concurrente à
    départager comme pour un vrai espace. -->
    <button
      class="space-icon system-icon"
      title="Système"
      on:click={(e) => openSpaceMenu(e, SYSTEM_SPACE)}
    >
      <Cpu size={16} />
    </button>
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
                droit pour le menu des commandes.
              </p>
              {#each activeObjects as object (object.id)}
                <div
                  class="object-card"
                  draggable="true"
                  on:dragstart={(e) => onObjectDragStart(e, object.id)}
                  on:contextmenu={(e) => openObjectMenu(e, object.name)}
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
      {#if promptResponse}
        <p class="prompt-response">{promptResponse}</p>
      {/if}
      <div class="bar">
        <form class="promptbar" on:submit|preventDefault={submitPrompt}>
          <input
            type="text"
            placeholder="Demande quelque chose (ex. « extraire les exigences », « ouvrir l'historique »)…"
            bind:value={promptText}
          />
          <button type="submit">Envoyer</button>
        </form>
      </div>
    </div>
  </main>
</div>

{#if commandMenu}
  <CommandMenu
    x={commandMenu.x}
    y={commandMenu.y}
    title={commandMenu.title}
    commands={commandMenu.commands}
    onChoose={commandMenu.onChoose}
    onClose={closeCommandMenu}
  />
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
    width: 56px;
    padding: 1rem 0;
    background: #fff;
    border-right: 1px solid #ddd;
  }

  .strip-top {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.6rem;
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

  .strip-spacer {
    flex: 1;
  }

  .system-icon {
    border-radius: 6px;
    border: 1px solid #ccc;
    color: #666;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .system-icon:hover {
    background: #f3f4f6;
  }

  .pinned-dossiers {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.4rem;
    padding-top: 0.6rem;
    border-top: 1px solid #eee;
    width: 100%;
  }

  .dossier-badge {
    width: 28px;
    height: 28px;
    border-radius: 6px;
    background: #f3f4f6;
    border: 1px solid #ddd;
    color: #555;
    font-size: 0.75rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    justify-content: center;
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

  .bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem;
  }

  .promptbar {
    display: flex;
    gap: 0.5rem;
    flex: 1;
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
