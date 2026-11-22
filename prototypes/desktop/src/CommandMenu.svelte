<script>
  // Menu contextuel générique : prompt en haut (filtre/rappel de commande),
  // commandes principales dessous. Remplace le menu radial — testé pour de
  // vrai, pas forcément plus clair qu'une liste. Même composant pour les
  // objets, les espaces, et les sous-menus (ex. « Classer dans… »).

  export let x;
  export let y;
  export let title = "";
  export let commands = [];
  export let onChoose;
  export let onClose;

  let query = "";

  // Test UI/UX : « ! » bascule le prompt en mode « commande directe » (comme
  // le préfixe « ! » de ce même outil pour lancer une commande shell) —
  // évalue le ressenti d'un caractère spécial pour sortir de la liste connue,
  // pas une vraie exécution derrière.
  $: isRawMode = query.startsWith("!");
  $: rawCommand = query.slice(1).trim();
  $: filtered = isRawMode ? [] : commands.filter((c) => c.toLowerCase().includes(query.toLowerCase()));

  function focusOnMount(node) {
    node.focus();
  }

  // Le menu s'ouvre en bas-gauche du point de clic par défaut (left:x,
  // top:y) ; près d'un bord de l'écran (ex. Système, tout en bas de la
  // barre latérale), ça le ferait dépasser — on bascule vers le bord
  // opposé une fois la taille réelle connue (après montage).
  function keepInViewport(node) {
    const rect = node.getBoundingClientRect();
    if (rect.bottom > window.innerHeight) {
      node.style.top = "auto";
      node.style.bottom = `${Math.max(8, window.innerHeight - y)}px`;
    }
    if (rect.right > window.innerWidth) {
      node.style.left = "auto";
      node.style.right = `${Math.max(8, window.innerWidth - x)}px`;
    }
  }

  function choose(command) {
    onChoose(command);
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      event.stopPropagation();
      onClose();
    } else if (event.key === "Enter") {
      event.stopPropagation();
      if (isRawMode && rawCommand) choose(`!${rawCommand}`);
      else if (!isRawMode && filtered.length > 0) choose(filtered[0]);
    }
  }
</script>

<div
  class="overlay"
  role="button"
  tabindex="0"
  aria-label="Fermer le menu"
  on:click={onClose}
  on:keydown={(e) => e.key === "Escape" && onClose()}
>
  <div
    class="menu"
    style="left:{x}px; top:{y}px"
    use:keepInViewport
    on:click|stopPropagation
    on:keydown|stopPropagation
  >
    {#if title}<div class="menu-title">{title}</div>{/if}
    <input
      type="text"
      class:raw-mode={isRawMode}
      placeholder="Tape pour filtrer, ou « ! » pour une commande directe…"
      bind:value={query}
      use:focusOnMount
      on:keydown={onKeydown}
    />
    <ul>
      {#if isRawMode}
        {#if rawCommand}
          <li><button class="raw-item" on:click={() => choose(`!${rawCommand}`)}>→ Exécuter « {rawCommand} »</button></li>
        {:else}
          <li class="empty">Tape une commande après le « ! »</li>
        {/if}
      {:else}
        {#each filtered as command}
          <li><button on:click={() => choose(command)}>{command}</button></li>
        {:else}
          <li class="empty">Aucune commande</li>
        {/each}
      {/if}
    </ul>
  </div>
</div>

<style>
  .overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: transparent;
    border: none;
    padding: 0;
  }

  .menu {
    position: absolute;
    width: 220px;
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.18);
    overflow: hidden;
    font-size: 0.85rem;
  }

  .menu-title {
    padding: 0.5rem 0.7rem;
    font-weight: 600;
    font-size: 0.75rem;
    color: #666;
    border-bottom: 1px solid #eee;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  input {
    width: 100%;
    box-sizing: border-box;
    border: none;
    border-bottom: 1px solid #eee;
    padding: 0.5rem 0.7rem;
    font-size: 0.85rem;
    outline: none;
  }
  input.raw-mode {
    background: #fff7ed;
    border-bottom-color: #f59e0b;
    font-family: ui-monospace, monospace;
  }

  .raw-item {
    color: #b45309;
    font-family: ui-monospace, monospace;
  }

  ul {
    list-style: none;
    margin: 0;
    padding: 0.2rem;
    max-height: 220px;
    overflow: auto;
  }

  li button {
    width: 100%;
    text-align: left;
    padding: 0.4rem 0.6rem;
    border: none;
    background: transparent;
    border-radius: 5px;
    cursor: pointer;
    font-size: 0.85rem;
  }
  li button:hover {
    background: #eff4ff;
  }

  li.empty {
    padding: 0.4rem 0.6rem;
    color: #aaa;
  }
</style>
