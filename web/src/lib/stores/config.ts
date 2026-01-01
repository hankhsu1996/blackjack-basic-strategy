import { writable, derived } from "svelte/store";

export interface ConfigState {
  numDecks: number;
  dealerHitsSoft17: boolean;
  doubleAfterSplit: boolean;
  resplitAces: boolean;
  maxSplitHands: number;
  dealerPeeks: boolean;
  blackjackPays: "3:2" | "6:5";
  lateSurrender: boolean;
}

export const config = writable<ConfigState>({
  numDecks: 8,
  dealerHitsSoft17: false,
  doubleAfterSplit: true,
  resplitAces: false,
  maxSplitHands: 4,
  dealerPeeks: true,
  blackjackPays: "3:2",
  lateSurrender: false,
});

export const strategyFilename = derived(config, ($config) => {
  const decks = $config.numDecks === 0 ? "inf" : $config.numDecks;
  const s17 = $config.dealerHitsSoft17 ? "h17" : "s17";
  const das = $config.doubleAfterSplit ? "das" : "ndas";
  const rsa = $config.resplitAces ? "rsa" : "nrsa";
  const msh = `sp${$config.maxSplitHands}`;
  const peek = $config.dealerPeeks ? "peek" : "nopeek";
  const bj = $config.blackjackPays === "3:2" ? "32" : "65";
  const sur = $config.lateSurrender ? "sur" : "nosur";
  return `${decks}-${s17}-${das}-${rsa}-${msh}-${peek}-${bj}-${sur}.json`;
});
