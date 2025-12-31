<script lang="ts">
  import { getActionColor } from "../utils/colors";

  export let action: string;

  $: bgColor = getActionColor(action);
</script>

<td
  class="w-7 h-6 text-xs lg:w-8 lg:h-7 lg:text-sm border border-base-300 text-center font-medium"
  style="background-color: {bgColor}"
>
  {action}
</td>
