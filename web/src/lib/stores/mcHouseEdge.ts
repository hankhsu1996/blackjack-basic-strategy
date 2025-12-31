import { writable } from "svelte/store";
import type { MCHouseEdgeData } from "../types/strategy";

export const mcData = writable<MCHouseEdgeData | null>(null);
export const mcLoading = writable(true);

export async function loadMCData(): Promise<void> {
  mcLoading.set(true);
  try {
    const response = await fetch(
      `${import.meta.env.BASE_URL}strategies/mc_house_edge.json`
    );
    if (response.ok) {
      mcData.set(await response.json());
    } else {
      mcData.set(null);
    }
  } catch {
    mcData.set(null);
  } finally {
    mcLoading.set(false);
  }
}
