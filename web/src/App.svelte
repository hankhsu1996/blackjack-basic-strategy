<script lang="ts">
  import { fade } from "svelte/transition";
  import { onMount } from "svelte";
  import { ExternalLink, Info, Menu, X } from "lucide-svelte";
  import ConfigPanel from "./lib/components/ConfigPanel.svelte";
  import StrategyTable from "./lib/components/StrategyTable.svelte";
  import Legend from "./lib/components/Legend.svelte";
  import { strategyFilename } from "./lib/stores/config";
  import { mcData, loadMCData } from "./lib/stores/mcHouseEdge";
  import type { StrategyData } from "./lib/types/strategy";

  let strategyData: StrategyData | null = null;
  let error: string | null = null;
  let menuOpen = false;

  // Load MC data on mount
  onMount(() => {
    loadMCData();
  });

  // Derive current MC result based on strategy filename
  $: configKey = $strategyFilename.replace(".json", "");
  $: currentMC = $mcData?.[configKey] ?? null;

  // Lock body scroll when menu is open
  $: if (typeof document !== "undefined") {
    document.body.style.overflow = menuOpen ? "hidden" : "";
  }

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

<main class="min-h-screen min-h-[100dvh] flex flex-col lg:flex-row bg-base-100">
  <!-- Mobile header (fixed) -->
  <header class="lg:hidden fixed top-0 left-0 right-0 h-14 flex items-center justify-center bg-base-200 z-50">
    <img src="{import.meta.env.BASE_URL}favicon.png" alt="" class="w-5 h-5 mr-3" />
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

  <!-- Mobile header spacer -->
  <div class="lg:hidden h-14 shrink-0"></div>

  <!-- Mobile menu overlay -->
  {#if menuOpen}
    <div
      class="lg:hidden fixed inset-0 top-14 bg-base-200 px-12 py-4 z-40 flex flex-col overflow-y-auto"
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

  <!-- Desktop Sidebar (fixed) -->
  <aside
    class="hidden lg:flex fixed left-0 top-0 w-72 bg-base-200 p-4 h-screen h-[100dvh] overflow-y-auto flex-col"
  >
    <h1 class="font-semibold mt-4 mb-10 text-center flex items-center justify-center gap-3">
      <img src="{import.meta.env.BASE_URL}favicon.png" alt="" class="w-6 h-6" />
      Blackjack Basic Strategy
    </h1>

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
  <div class="flex-1 p-4 pt-8 pb-32 lg:pt-4 lg:pb-4 overflow-auto flex flex-col items-center lg:items-start justify-center">
    {#if error}
      <div class="alert alert-error">
        <span>{error}</span>
      </div>
    {:else if strategyData}
      <div class="contents lg:block lg:w-fit lg:mx-auto" style="margin-left: max(18rem, calc(50% - 530px))">
        <div class="flex flex-col lg:flex-row gap-6 lg:gap-8">
          <StrategyTable title="Hard Totals" data={strategyData.hard} />
          <StrategyTable title="Soft Totals" data={strategyData.soft} />
          <StrategyTable title="Pairs" data={strategyData.pairs} />
        </div>

        <Legend />

        <!-- House Edge (only shown when MC data is available) -->
        {#if currentMC}
          <div class="text-center text-sm text-base-content/70 mt-4 flex items-center justify-center gap-1">
            House Edge:
            <span class="font-medium">{currentMC.house_edge.toFixed(3)}%</span>
            <span class="text-base-content/50">&plusmn; {currentMC.ci.toFixed(3)}%</span>
            <div class="tooltip tooltip-left lg:tooltip-top before:max-w-[200px] lg:before:max-w-xs before:text-xs lg:before:text-sm before:text-left before:bg-base-200 before:text-base-content before:p-2 lg:before:p-3" data-tip="Monte Carlo simulation ({currentMC.hands_billions}B hands){strategyData?.config.num_decks === 0 ? '' : ', 75% penetration'}. Simulates real casino play.">
              <Info size={13} class="opacity-50 hover:opacity-100 cursor-help" />
            </div>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</main>
