export interface Config {
  num_decks: number;
  dealer_hits_soft_17: boolean;
  double_after_split: boolean;
  resplit_aces: boolean;
  dealer_peeks: boolean;
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
