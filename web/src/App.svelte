<script lang="ts">
  import ConfigPanel from "./lib/components/ConfigPanel.svelte";
  import StrategyTable from "./lib/components/StrategyTable.svelte";
  import Legend from "./lib/components/Legend.svelte";
  import { strategyFilename } from "./lib/stores/config";
  import type { StrategyData } from "./lib/types/strategy";

  let strategyData: StrategyData | null = null;
  let loading = false;
  let error: string | null = null;

  $: loadStrategy($strategyFilename);

  async function loadStrategy(filename: string) {
    loading = true;
    error = null;
    try {
      const response = await fetch(
        `${import.meta.env.BASE_URL}strategies/${filename}`
      );
      if (!response.ok) {
        throw new Error(`Failed to load strategy: ${response.statusText}`);
      }
      strategyData = await response.json();
    } catch (e) {
      error = e instanceof Error ? e.message : "Unknown error";
      strategyData = null;
    } finally {
      loading = false;
    }
  }
</script>

<main class="min-h-screen flex flex-col lg:flex-row bg-base-100">
  <!-- Config Panel -->
  <aside
    class="w-full lg:w-64 lg:shrink-0 bg-base-200 p-4 lg:h-screen lg:overflow-y-auto"
  >
    <!-- Mobile: Collapsible -->
    <details class="lg:hidden collapse collapse-arrow bg-base-100 rounded-box">
      <summary class="collapse-title font-medium">Game Rules</summary>
      <div class="collapse-content">
        <ConfigPanel />
      </div>
    </details>

    <!-- Desktop: Always visible -->
    <div class="hidden lg:block">
      <ConfigPanel />
    </div>
  </aside>

  <!-- Strategy Tables -->
  <div class="flex-1 p-4 overflow-auto">
    {#if loading}
      <div class="flex items-center justify-center h-full min-h-[200px]">
        <span class="loading loading-spinner loading-lg"></span>
      </div>
    {:else if error}
      <div class="alert alert-error">
        <span>{error}</span>
      </div>
    {:else if strategyData}
      <div class="mb-2 text-sm text-base-content/70">
        {strategyData.config.description}
      </div>

      <div class="flex flex-col lg:flex-row gap-4 lg:min-w-max">
        <StrategyTable title="Hard Totals" data={strategyData.hard} />
        <StrategyTable title="Soft Totals" data={strategyData.soft} />
        <StrategyTable title="Pairs" data={strategyData.pairs} />
      </div>

      <Legend />
    {/if}
  </div>
</main>
