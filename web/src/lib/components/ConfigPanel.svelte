<script lang="ts">
  import { config } from "../stores/config";
</script>

<div class="space-y-4">
  <h2 class="text-lg font-bold">Game Rules</h2>

  <!-- Number of Decks -->
  <div class="form-control w-full">
    <label class="label" for="num-decks">
      <span class="label-text">Number of Decks</span>
    </label>
    <select
      id="num-decks"
      class="select select-bordered select-sm w-full"
      bind:value={$config.numDecks}
    >
      <option value={1}>1 Deck</option>
      <option value={2}>2 Decks</option>
      <option value={4}>4 Decks</option>
      <option value={6}>6 Decks</option>
      <option value={8}>8 Decks</option>
      <option value={0}>Infinite</option>
    </select>
  </div>

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
</div>
