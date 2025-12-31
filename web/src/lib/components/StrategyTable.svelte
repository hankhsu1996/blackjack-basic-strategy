<script lang="ts">
  import type { TableData } from "../types/strategy";
  import TableCell from "./TableCell.svelte";

  export let title: string;
  export let data: TableData;
</script>

<div class="strategy-table">
  <h3 class="text-sm font-medium mb-2 text-center text-base-content/70">
    {title}
  </h3>
  <table class="table-fixed border-separate border-spacing-0.5">
    <thead>
      <tr>
        {#each data.headers as header}
          <th
            class="w-7 h-6 lg:w-8 lg:h-7 text-center text-xs lg:text-sm font-medium text-base-content/60 select-none"
          >
            {header}
          </th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each data.rows as row}
        <tr>
          <td
            class="w-7 h-6 lg:w-8 lg:h-7 text-center text-xs lg:text-sm font-medium text-base-content/60 select-none"
          >
            {row.label}
          </td>
          {#each row.actions as action}
            <TableCell {action} />
          {/each}
        </tr>
      {/each}
    </tbody>
  </table>
</div>
