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

  $: filtered = commands.filter((c) => c.toLowerCase().includes(query.toLowerCase()));

  function focusOnMount(node) {
    node.focus();
  }

  function choose(command) {
    onChoose(command);
  }

  function onKeydown(event) {
    if (event.key === "Escape") {
      event.stopPropagation();
      onClose();
    } else if (event.key === "Enter" && filtered.length > 0) {
      event.stopPropagation();
      choose(filtered[0]);
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
  <div class="menu" style="left:{x}px; top:{y}px" on:click|stopPropagation on:keydown|stopPropagation>
    {#if title}<div class="menu-title">{title}</div>{/if}
    <input
      type="text"
      placeholder="Tape pour filtrer ou rappeler une commande…"
      bind:value={query}
      use:focusOnMount
      on:keydown={onKeydown}
    />
    <ul>
      {#each filtered as command}
        <li><button on:click={() => choose(command)}>{command}</button></li>
      {:else}
        <li class="empty">Aucune commande</li>
      {/each}
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
