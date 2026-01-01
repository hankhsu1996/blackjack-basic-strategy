<script lang="ts">
  import { LEGEND_ITEMS, SURRENDER_ITEM } from "../utils/colors";
  import { config } from "../stores/config";

  // Split into basic actions and double variants
  const basicItems = LEGEND_ITEMS.filter(
    (item) => !item.action.startsWith("D")
  );
  const doubleItems = LEGEND_ITEMS.filter((item) =>
    item.action.startsWith("D")
  );
</script>

<div class="flex flex-wrap gap-x-4 gap-y-2 mt-14 justify-center text-sm">
  {#each basicItems as item}
    <div class="flex items-center gap-1.5">
      <kbd
        class="kbd kbd-sm shadow-none border-none flex items-center justify-center text-[14px] select-none"
        style="background-color: {item.color}">{item.action}</kbd
      >
      <span class="text-base-content/70">{item.label}</span>
    </div>
  {/each}

  <!-- Surrender (only when enabled) -->
  {#if $config.lateSurrender}
    <div class="flex items-center gap-1.5">
      <kbd
        class="kbd kbd-sm shadow-none border-none flex items-center justify-center text-[14px] select-none"
        style="background-color: {SURRENDER_ITEM.color}">{SURRENDER_ITEM.action}</kbd
      >
      <span class="text-base-content/70">{SURRENDER_ITEM.label}</span>
    </div>
  {/if}

  <!-- Keep doubles together -->
  <div class="flex gap-x-4 flex-nowrap">
    {#each doubleItems as item}
      <div class="flex items-center gap-1.5">
        <kbd
          class="kbd kbd-sm shadow-none border-none flex items-center justify-center text-[13px] select-none"
          style="background-color: {item.color}">{item.action}</kbd
        >
        <span class="text-base-content/70">{item.label}</span>
      </div>
    {/each}
  </div>
</div>
