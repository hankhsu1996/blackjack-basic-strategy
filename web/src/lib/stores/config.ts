import { writable, derived } from "svelte/store";

export interface ConfigState {
  numDecks: number;
  dealerHitsSoft17: boolean;
  doubleAfterSplit: boolean;
  resplitAces: boolean;
  dealerPeeks: boolean;
}

export const config = writable<ConfigState>({
  numDecks: 6,
  dealerHitsSoft17: false,
  doubleAfterSplit: true,
  resplitAces: false,
  dealerPeeks: true,
});

export const strategyFilename = derived(config, ($config) => {
  const decks = $config.numDecks === 0 ? "inf" : $config.numDecks;
  const s17 = $config.dealerHitsSoft17 ? "h17" : "s17";
  const das = $config.doubleAfterSplit ? "das" : "ndas";
  const rsa = $config.resplitAces ? "rsa" : "nrsa";
  const peek = $config.dealerPeeks ? "peek" : "nopeek";
  return `${decks}-${s17}-${das}-${rsa}-${peek}.json`;
});
