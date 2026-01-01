<script lang="ts">
  import { config } from "../stores/config";

  const deckOptions = [
    { value: 1, label: "1" },
    { value: 2, label: "2" },
    { value: 4, label: "4" },
    { value: 6, label: "6" },
    { value: 8, label: "8" },
    { value: 0, label: "∞" },
  ];

  const bjPayOptions: Array<{ value: "3:2" | "6:5"; label: string }> = [
    { value: "3:2", label: "3:2" },
    { value: "6:5", label: "6:5" },
  ];

  const maxSplitOptions = [
    { value: 2, label: "2" },
    { value: 3, label: "3" },
    { value: 4, label: "4" },
  ];
</script>

<div class="space-y-4 px-4">
  <!-- === GAME SETUP === -->

  <!-- Number of Decks -->
  <div>
    <div class="text-sm mb-2">Decks</div>
    <div class="flex gap-1">
      {#each deckOptions as opt}
        <button
          class="btn btn-sm flex-1 min-w-0 {$config.numDecks === opt.value
            ? 'bg-base-300 border-base-300'
            : 'btn-ghost'}"
          onclick={() => ($config.numDecks = opt.value)}
        >
          {opt.label}
        </button>
      {/each}
    </div>
  </div>

  <!-- Blackjack Payout -->
  <div>
    <div class="text-sm mb-2">Blackjack Pays</div>
    <div class="flex gap-1">
      {#each bjPayOptions as opt}
        <button
          class="btn btn-sm flex-1 min-w-0 {$config.blackjackPays === opt.value
            ? 'bg-base-300 border-base-300'
            : 'btn-ghost'}"
          onclick={() => ($config.blackjackPays = opt.value)}
        >
          {opt.label}
        </button>
      {/each}
    </div>
  </div>

  <!-- === DEALER RULES === -->

  <!-- Dealer Hits Soft 17 -->
  <div class="form-control">
    <label class="label cursor-pointer justify-start gap-3">
      <input
        type="checkbox"
        class="toggle toggle-sm"
        bind:checked={$config.dealerHitsSoft17}
      />
      <span class="label-text">Dealer hits soft 17 (H17)</span>
    </label>
  </div>

  <!-- Dealer Peeks -->
  <div class="form-control">
    <label class="label cursor-pointer justify-start gap-3">
      <input
        type="checkbox"
        class="toggle toggle-sm"
        bind:checked={$config.dealerPeeks}
      />
      <span class="label-text">Dealer peeks for BJ</span>
    </label>
  </div>

  <!-- === DOUBLING === -->

  <!-- Double After Split -->
  <div class="form-control">
    <label class="label cursor-pointer justify-start gap-3">
      <input
        type="checkbox"
        class="toggle toggle-sm"
        bind:checked={$config.doubleAfterSplit}
      />
      <span class="label-text">Double after split (DAS)</span>
    </label>
  </div>

  <!-- === SPLITTING === -->

  <!-- Max Split Hands -->
  <div>
    <div class="text-sm mb-2">Max Split Hands</div>
    <div class="flex gap-1">
      {#each maxSplitOptions as opt}
        <button
          class="btn btn-sm flex-1 min-w-0 {$config.maxSplitHands === opt.value
            ? 'bg-base-300 border-base-300'
            : 'btn-ghost'}"
          onclick={() => ($config.maxSplitHands = opt.value)}
        >
          {opt.label}
        </button>
      {/each}
    </div>
  </div>

  <!-- Resplit Aces -->
  <div class="form-control">
    <label class="label cursor-pointer justify-start gap-3">
      <input
        type="checkbox"
        class="toggle toggle-sm"
        bind:checked={$config.resplitAces}
      />
      <span class="label-text">Resplit aces (RSA)</span>
    </label>
  </div>

  <!-- Hit split aces (fixed: no) -->
  <div class="form-control opacity-50">
    <label class="label cursor-not-allowed justify-start gap-3">
      <input
        type="checkbox"
        class="toggle toggle-sm"
        disabled
        checked={false}
      />
      <span class="label-text">Hit split aces</span>
    </label>
  </div>

  <!-- === OTHER === -->

  <!-- Late Surrender -->
  <div class="form-control">
    <label class="label cursor-pointer justify-start gap-3">
      <input
        type="checkbox"
        class="toggle toggle-sm"
        bind:checked={$config.lateSurrender}
      />
      <span class="label-text">Late surrender</span>
    </label>
  </div>
</div>
