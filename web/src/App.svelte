<script lang="ts">
  import { fade } from "svelte/transition";
  import { ExternalLink, Menu, X } from "lucide-svelte";
  import ConfigPanel from "./lib/components/ConfigPanel.svelte";
  import StrategyTable from "./lib/components/StrategyTable.svelte";
  import Legend from "./lib/components/Legend.svelte";
  import { strategyFilename } from "./lib/stores/config";
  import type { StrategyData } from "./lib/types/strategy";

  let strategyData: StrategyData | null = null;
  let error: string | null = null;
  let menuOpen = false;

  $: loadStrategy($strategyFilename);

  async function loadStrategy(filename: string) {
    try {
      const response = await fetch(
        `${import.meta.env.BASE_URL}strategies/${filename}`
      );
      if (!response.ok) {
        throw new Error(`Failed to load strategy: ${response.statusText}`);
      }
      strategyData = await response.json();
      error = null;
    } catch (e) {
      error = e instanceof Error ? e.message : "Unknown error";
    }
  }
</script>

<main class="min-h-screen flex flex-col lg:flex-row bg-base-100">
  <!-- Mobile header -->
  <header class="lg:hidden flex items-center justify-center relative p-4 bg-base-200">
    <h1 class="font-semibold">Blackjack Basic Strategy</h1>
    <button
      class="btn btn-ghost btn-sm absolute right-4"
      onclick={() => (menuOpen = !menuOpen)}
    >
      {#if menuOpen}
        <X size={20} />
      {:else}
        <Menu size={20} />
      {/if}
    </button>
  </header>

  <!-- Mobile menu overlay -->
  {#if menuOpen}
    <div
      class="lg:hidden fixed inset-0 top-14 bg-base-200 px-12 py-4 z-50 flex flex-col"
      transition:fade={{ duration: 150 }}
    >
      <ConfigPanel />

      <!-- Spacer -->
      <div class="flex-1"></div>

      <a
        href="https://github.com/hankhsu1996/blackjack-basic-strategy"
        target="_blank"
        rel="noopener noreferrer"
        class="flex items-center justify-center gap-1.5 text-sm font-medium text-base-content/70 hover:text-base-content mb-8"
      >
        <span>View on GitHub</span>
        <ExternalLink size={14} />
      </a>
    </div>
  {/if}

  <!-- Desktop Sidebar -->
  <aside
    class="hidden lg:flex w-72 shrink-0 bg-base-200 p-4 h-screen overflow-y-auto flex-col"
  >
    <h1 class="font-semibold mt-4 mb-10 text-center">Blackjack Basic Strategy</h1>

    <ConfigPanel />

    <!-- Spacer -->
    <div class="flex-1"></div>

    <!-- GitHub link -->
    <a
      href="https://github.com/hankhsu1996/blackjack-basic-strategy"
      target="_blank"
      rel="noopener noreferrer"
      class="flex items-center justify-center gap-1.5 text-sm font-medium text-base-content/70 hover:text-base-content mt-4"
    >
      <span>View on GitHub</span>
      <ExternalLink size={14} />
    </a>
  </aside>

  <!-- Strategy Tables -->
  <div class="flex-1 p-4 pt-8 pb-32 lg:pt-4 lg:pb-4 overflow-auto flex flex-col items-center justify-center">
    {#if error}
      <div class="alert alert-error">
        <span>{error}</span>
      </div>
    {:else if strategyData}
      <div class="flex flex-col lg:flex-row gap-6 lg:gap-8 lg:-ml-36">
        <StrategyTable title="Hard Totals" data={strategyData.hard} />
        <StrategyTable title="Soft Totals" data={strategyData.soft} />
        <StrategyTable title="Pairs" data={strategyData.pairs} />
      </div>

      <Legend />
    {/if}
  </div>
</main>
