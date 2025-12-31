export interface Config {
  num_decks: number;
  dealer_hits_soft_17: boolean;
  double_after_split: boolean;
  resplit_aces: boolean;
  max_split_hands: number;
  dealer_peeks: boolean;
  blackjack_pays: number;
  description: string;
}

export interface TableRow {
  label: string;
  actions: string[];
}

export interface TableData {
  headers: string[];
  rows: TableRow[];
}

export interface StrategyData {
  config: Config;
  hard: TableData;
  soft: TableData;
  pairs: TableData;
}

export interface MCResult {
  house_edge: number;
  ci: number;
  hands_billions: number;
}

export type MCHouseEdgeData = Record<string, MCResult>;
