<script lang="ts">
  import type { TableData } from "../types/strategy";
  import TableCell from "./TableCell.svelte";

  export let title: string;
  export let data: TableData;
</script>

<div class="strategy-table">
  <h3 class="text-sm font-semibold mb-2 text-center">{title}</h3>
  <table class="table-fixed border-collapse text-xs">
    <thead>
      <tr>
        {#each data.headers as header}
          <th
            class="w-7 h-6 lg:w-8 lg:h-7 bg-base-200 border border-base-300 text-center text-xs lg:text-sm"
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
            class="w-7 h-6 lg:w-8 lg:h-7 bg-base-200 border border-base-300 text-center font-medium text-xs lg:text-sm"
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
