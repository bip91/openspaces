<script>
  // Prototype jetable : fenêtrage glissable/redimensionnable, pas branché sur
  // le vrai moteur. Teste deux gestes à la fois : déplacer/redimensionner une
  // fenêtre, et rouvrir Objets/Liens/Bus comme des fenêtres séparées plutôt
  // que des pages — la question laissée ouverte en conversation.

  let nextZ = 1;

  let windows = [
    {
      id: "objets",
      title: "Objets",
      x: 60,
      y: 60,
      width: 360,
      height: 260,
      z: nextZ++,
      open: true,
      lines: ["commande — Table, v2", "délai obligatoire — Exigence", "classeur-démo — Dossier"],
    },
    {
      id: "liens",
      title: "Liens",
      x: 460,
      y: 120,
      width: 340,
      height: 220,
      z: nextZ++,
      open: true,
      lines: ["délai obligatoire --correspondence--> commande", "commande --classification--> classeur-démo"],
    },
    {
      id: "bus",
      title: "Bus",
      x: 260,
      y: 320,
      width: 380,
      height: 200,
      z: nextZ++,
      open: false,
      lines: ["create_object @ harnais-web -> autorisé (23 ms)", "create_object @ lecteur-demo -> refusé (forbidden)"],
    },
  ];

  let drag = null; // { id, startX, startY, originX, originY }
  let resize = null; // { id, startX, startY, originW, originH }

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
    windows = windows.map((w) =>
      w.id === drag.id ? { ...w, x: drag.originX + dx, y: drag.originY + dy } : w
    );
  }

  function onDragEnd() {
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

<main>
  <div class="desktop">
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
          {#each win.lines as line}
            <p>{line}</p>
          {/each}
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

  <nav class="dock" aria-label="Fenêtres">
    {#each windows as win (win.id)}
      <button class:open={win.open} on:click={() => toggleWindow(win.id)}>{win.title}</button>
    {/each}
  </nav>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: system-ui, sans-serif;
    background: #e5e7eb;
    color: #1a1a1a;
  }

  main {
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .desktop {
    position: relative;
    flex: 1;
    overflow: hidden;
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
  }
  .body p {
    margin: 0.3rem 0;
    color: #444;
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

  .dock {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
    padding: 0.6rem;
    background: #fff;
    border-top: 1px solid #ddd;
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
</style>
