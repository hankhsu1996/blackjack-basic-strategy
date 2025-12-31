<script lang="ts">
  import { LEGEND_ITEMS } from "../utils/colors";
</script>

<div class="flex flex-wrap gap-2 mt-4">
  {#each LEGEND_ITEMS as item}
    <div
      class="flex items-center gap-1 px-2 py-1 rounded text-xs font-medium"
      style="background-color: {item.color}"
    >
      <span class="font-bold">{item.action}</span>
      <span>= {item.label}</span>
    </div>
  {/each}
</div>
