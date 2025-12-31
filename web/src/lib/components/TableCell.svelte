<script lang="ts">
  import { getActionColor } from "../utils/colors";

  export let action: string;

  $: bgColor = getActionColor(action);
  $: isDouble = action.length > 1;
</script>

<td
  class="w-7 h-6 lg:w-8 lg:h-7 text-center font-normal rounded-sm transition-colors duration-200 select-none {isDouble
    ? 'text-[13px]'
    : 'text-[14px]'}"
  style="background-color: {bgColor}"
>
  {action}
</td>
