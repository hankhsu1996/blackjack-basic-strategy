/**
 * CUDA Monte Carlo Blackjack Simulator
 *
 * Loads strategy from JSON file, simulates with finite deck shoe.
 *
 * Compile: nvcc -O3 -arch=sm_86 -o monte_carlo monte_carlo.cu cJSON.c
 * Run: ./monte_carlo [strategy.json] [num_hands_billions]
 *
 * Example: ./monte_carlo ../web/public/strategies/6-h17-das-rsa-peek-32.json 10
 */

#include <cuda_runtime.h>
#include <curand_kernel.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "cJSON.h"

// ============================================================================
// Configuration
// ============================================================================

// Game rules (will be read from JSON)
struct GameConfig {
    int num_decks;
    bool dealer_hits_soft_17;
    float blackjack_pays;
    bool dealer_peeks;
    int max_split_hands;      // Max hands from splitting (default 4)
    bool resplit_aces;        // Can resplit aces
    float penetration;        // Reshuffle at this fraction (0.75 = 75%)
};

// Strategy tables (will be copied to GPU)
// Actions: 0=Stand, 1=Hit, 2=Double(hit), 3=Double(stand), 4=Split
__constant__ int8_t d_hard_strategy[18 * 10];   // [total-4][upcard-2]
__constant__ int8_t d_soft_strategy[10 * 10];   // [total-12][upcard-2]
__constant__ int8_t d_pair_strategy[10 * 10];   // [card-2][upcard-2]
__constant__ GameConfig d_config;

// ============================================================================
// JSON Parsing (simple, host-side)
// ============================================================================

int8_t parse_action(const char* action) {
    if (strcmp(action, "S") == 0) return 0;   // Stand
    if (strcmp(action, "H") == 0) return 1;   // Hit
    if (strcmp(action, "Dh") == 0) return 2;  // Double or Hit
    if (strcmp(action, "Ds") == 0) return 3;  // Double or Stand
    if (strcmp(action, "D") == 0) return 2;   // Double
    if (strcmp(action, "P") == 0) return 4;   // Split
    if (strcmp(action, "Ph") == 0) return 4;  // Split or Hit
    return 1;  // Default to hit
}

int parse_hard_label(const char* label) {
    // "5" -> 1, "19" -> 15 (index = total - 4)
    return atoi(label) - 4;
}

int parse_soft_label(const char* label) {
    // "A,2" -> 1, "A,9" -> 8 (index = second card - 1)
    if (strlen(label) >= 3 && label[0] == 'A') {
        return atoi(label + 2) - 1;
    }
    return -1;
}

int parse_pair_label(const char* label) {
    // "2,2" -> 0, "10,10" -> 8, "A,A" -> 9
    if (label[0] == 'A') return 9;
    return atoi(label) - 2;
}

char* read_file(const char* filename) {
    FILE* f = fopen(filename, "rb");
    if (!f) return NULL;

    fseek(f, 0, SEEK_END);
    long length = ftell(f);
    fseek(f, 0, SEEK_SET);

    char* content = (char*)malloc(length + 1);
    size_t read_bytes = fread(content, 1, length, f);
    content[read_bytes] = '\0';
    fclose(f);
    return content;
}

bool load_strategy(const char* filename,
                   int8_t* hard, int8_t* soft, int8_t* pairs,
                   GameConfig* config) {
    // Initialize defaults
    for (int i = 0; i < 18 * 10; i++) {
        int total = (i / 10) + 4;
        hard[i] = (total >= 17) ? 0 : 1;
    }
    for (int i = 0; i < 10 * 10; i++) soft[i] = 1;
    for (int i = 0; i < 10 * 10; i++) pairs[i] = 1;

    char* content = read_file(filename);
    if (!content) {
        printf("Error: Cannot open %s\n", filename);
        return false;
    }

    cJSON* json = cJSON_Parse(content);
    free(content);
    if (!json) {
        printf("Error: Invalid JSON\n");
        return false;
    }

    // Parse config
    cJSON* cfg = cJSON_GetObjectItem(json, "config");
    if (cfg) {
        cJSON* decks = cJSON_GetObjectItem(cfg, "num_decks");
        cJSON* h17 = cJSON_GetObjectItem(cfg, "dealer_hits_soft_17");
        cJSON* peek = cJSON_GetObjectItem(cfg, "dealer_peeks");
        cJSON* bj = cJSON_GetObjectItem(cfg, "blackjack_pays");

        cJSON* max_split = cJSON_GetObjectItem(cfg, "max_split_hands");
        cJSON* rsa = cJSON_GetObjectItem(cfg, "resplit_aces");
        cJSON* pen = cJSON_GetObjectItem(cfg, "penetration");

        config->num_decks = decks ? decks->valueint : 6;
        config->dealer_hits_soft_17 = h17 && cJSON_IsTrue(h17);
        config->dealer_peeks = peek && cJSON_IsTrue(peek);
        config->blackjack_pays = bj ? (float)bj->valuedouble : 1.5f;
        config->max_split_hands = max_split ? max_split->valueint : 4;  // Default to 4 hands
        config->resplit_aces = rsa && cJSON_IsTrue(rsa);
        config->penetration = pen ? (float)pen->valuedouble : 0.75f;  // Default 75%
    }

    printf("Config: Decks=%d, H17=%s, Peek=%s, BJ=%.2f, MaxSplit=%d, RSA=%s, Pen=%.0f%%\n",
           config->num_decks,
           config->dealer_hits_soft_17 ? "Yes" : "No",
           config->dealer_peeks ? "Yes" : "No",
           config->blackjack_pays,
           config->max_split_hands,
           config->resplit_aces ? "Yes" : "No",
           config->penetration * 100);

    // Parse hard strategy
    cJSON* hard_obj = cJSON_GetObjectItem(json, "hard");
    if (hard_obj) {
        cJSON* rows = cJSON_GetObjectItem(hard_obj, "rows");
        int count = 0;
        cJSON* row;
        cJSON_ArrayForEach(row, rows) {
            cJSON* label = cJSON_GetObjectItem(row, "label");
            cJSON* actions = cJSON_GetObjectItem(row, "actions");
            if (!label || !actions) continue;

            int row_idx = parse_hard_label(label->valuestring);
            if (row_idx < 0 || row_idx >= 18) continue;

            int col = 0;
            cJSON* action;
            cJSON_ArrayForEach(action, actions) {
                if (col < 10) {
                    hard[row_idx * 10 + col] = parse_action(action->valuestring);
                    col++;
                }
            }
            count++;
        }
        printf("Loaded %d hard rows\n", count);
    }

    // Parse soft strategy
    cJSON* soft_obj = cJSON_GetObjectItem(json, "soft");
    if (soft_obj) {
        cJSON* rows = cJSON_GetObjectItem(soft_obj, "rows");
        int count = 0;
        cJSON* row;
        cJSON_ArrayForEach(row, rows) {
            cJSON* label = cJSON_GetObjectItem(row, "label");
            cJSON* actions = cJSON_GetObjectItem(row, "actions");
            if (!label || !actions) continue;

            int row_idx = parse_soft_label(label->valuestring);
            if (row_idx < 0 || row_idx >= 10) continue;

            int col = 0;
            cJSON* action;
            cJSON_ArrayForEach(action, actions) {
                if (col < 10) {
                    soft[row_idx * 10 + col] = parse_action(action->valuestring);
                    col++;
                }
            }
            count++;
        }
        printf("Loaded %d soft rows\n", count);
    }

    // Parse pairs strategy
    cJSON* pairs_obj = cJSON_GetObjectItem(json, "pairs");
    if (pairs_obj) {
        cJSON* rows = cJSON_GetObjectItem(pairs_obj, "rows");
        int count = 0;
        cJSON* row;
        cJSON_ArrayForEach(row, rows) {
            cJSON* label = cJSON_GetObjectItem(row, "label");
            cJSON* actions = cJSON_GetObjectItem(row, "actions");
            if (!label || !actions) continue;

            int row_idx = parse_pair_label(label->valuestring);
            if (row_idx < 0 || row_idx >= 10) continue;

            int col = 0;
            cJSON* action;
            cJSON_ArrayForEach(action, actions) {
                if (col < 10) {
                    pairs[row_idx * 10 + col] = parse_action(action->valuestring);
                    col++;
                }
            }
            count++;
        }
        printf("Loaded %d pair rows\n", count);
    }

    cJSON_Delete(json);
    return true;
}

// ============================================================================
// Device Helper Functions
// ============================================================================

// Shoe structure for finite deck simulation
struct Shoe {
    int8_t cards[416];  // Max 8 decks * 52 cards
    int size;           // Total cards in shoe (0 = infinite deck mode)
    int pos;            // Current position (cards dealt = pos)
    int reshuffle_at;   // Reshuffle when pos reaches this
};

__device__ void init_shoe(Shoe* shoe, int num_decks, float penetration, curandState* state) {
    shoe->size = num_decks * 52;
    shoe->pos = 0;

    // Infinite deck mode: size=0, no cards to shuffle
    if (num_decks == 0) {
        shoe->reshuffle_at = 0;
        return;
    }

    shoe->reshuffle_at = (int)(shoe->size * penetration);  // Reshuffle at penetration %

    // Build and shuffle shoe
    int idx = 0;
    for (int d = 0; d < num_decks; d++) {
        for (int i = 0; i < 4; i++) {  // 4 suits
            shoe->cards[idx++] = 11;  // Ace
            for (int v = 2; v <= 9; v++) {
                shoe->cards[idx++] = v;
            }
            shoe->cards[idx++] = 10;  // 10
            shoe->cards[idx++] = 10;  // J
            shoe->cards[idx++] = 10;  // Q
            shoe->cards[idx++] = 10;  // K
        }
    }

    // Fisher-Yates shuffle
    for (int i = shoe->size - 1; i > 0; i--) {
        int j = curand(state) % (i + 1);
        int8_t temp = shoe->cards[i];
        shoe->cards[i] = shoe->cards[j];
        shoe->cards[j] = temp;
    }
}

__device__ void reshuffle_shoe(Shoe* shoe, curandState* state) {
    // No-op for infinite deck
    if (shoe->size == 0) return;

    shoe->pos = 0;
    // Fisher-Yates shuffle
    for (int i = shoe->size - 1; i > 0; i--) {
        int j = curand(state) % (i + 1);
        int8_t temp = shoe->cards[i];
        shoe->cards[i] = shoe->cards[j];
        shoe->cards[j] = temp;
    }
}

// Infinite deck draw (for continuous shuffle / no shoe)
__device__ __forceinline__ int draw_card_infinite(curandState* state) {
    int r = curand(state) % 13;
    if (r == 0) return 11;      // Ace
    if (r >= 10) return 10;     // 10, J, Q, K
    return r + 1;               // 2-9
}

__device__ __forceinline__ int draw_card_from_shoe(Shoe* shoe, curandState* state) {
    // Should not be called for infinite deck, but guard anyway
    if (shoe->size == 0) {
        return draw_card_infinite(state);
    }
    if (shoe->pos >= shoe->reshuffle_at) {
        reshuffle_shoe(shoe, state);
    }
    return shoe->cards[shoe->pos++];
}

// Draw card - from shoe or infinite deck depending on config
__device__ __forceinline__ int draw_card(Shoe* shoe, curandState* state) {
    if (d_config.num_decks == 0) {
        return draw_card_infinite(state);
    }
    return draw_card_from_shoe(shoe, state);
}

__device__ __forceinline__ int hand_value(int* cards, int num_cards) {
    int total = 0;
    int aces = 0;

    for (int i = 0; i < num_cards; i++) {
        total += cards[i];
        if (cards[i] == 11) aces++;
    }

    while (total > 21 && aces > 0) {
        total -= 10;
        aces--;
    }

    return total + (aces > 0 ? 100 : 0);
}

__device__ int get_action(int* cards, int num_cards, int dealer_upcard, bool can_split) {
    int hv = hand_value(cards, num_cards);
    int total = hv % 100;
    bool is_soft = hv >= 100;
    int dealer_idx = dealer_upcard - 2;

    // Check for pair
    if (can_split && num_cards == 2 && cards[0] == cards[1]) {
        int pair_card = cards[0];
        int pair_idx = pair_card - 2;
        int action = d_pair_strategy[pair_idx * 10 + dealer_idx];
        if (action == 4) return 4;  // Split
    }

    // Soft hand
    if (is_soft && total >= 12 && total <= 21) {
        int soft_idx = total - 12;
        return d_soft_strategy[soft_idx * 10 + dealer_idx];
    }

    // Hard hand
    if (total >= 4 && total <= 21) {
        int hard_idx = total - 4;
        if (hard_idx < 0) hard_idx = 0;
        if (hard_idx > 17) hard_idx = 17;
        return d_hard_strategy[hard_idx * 10 + dealer_idx];
    }

    return 1;  // Hit
}

__device__ int play_dealer(int* cards, int num_cards, Shoe* shoe, curandState* state) {
    while (true) {
        int hv = hand_value(cards, num_cards);
        int total = hv % 100;
        bool is_soft = hv >= 100;

        if (total > 21) return total;
        if (total > 17) return total;
        if (total == 17) {
            if (d_config.dealer_hits_soft_17 && is_soft) {
                cards[num_cards++] = draw_card(shoe, state);
                continue;
            }
            return total;
        }
        cards[num_cards++] = draw_card(shoe, state);
    }
}

__device__ int play_player_hand(
    int* cards, int* num_cards,
    int dealer_upcard,
    float* bet,
    Shoe* shoe,
    curandState* state
) {
    while (true) {
        int hv = hand_value(cards, *num_cards);
        int total = hv % 100;

        if (total > 21) return total;
        if (total == 21) return total;

        int action = get_action(cards, *num_cards, dealer_upcard, false);

        if (action == 0) {
            return total;  // Stand
        } else if (action == 3) {
            // Double if can, else stand
            if (*num_cards == 2) {
                cards[(*num_cards)++] = draw_card(shoe, state);
                *bet *= 2.0f;
                return hand_value(cards, *num_cards) % 100;
            }
            return total;
        } else if (action == 1) {
            cards[(*num_cards)++] = draw_card(shoe, state);
        } else if (action == 2) {
            // Double if can, else hit
            if (*num_cards == 2) {
                cards[(*num_cards)++] = draw_card(shoe, state);
                *bet *= 2.0f;
                return hand_value(cards, *num_cards) % 100;
            }
            cards[(*num_cards)++] = draw_card(shoe, state);
        } else {
            return total;
        }
    }
}

__device__ float play_single_hand(
    int* player_cards, int player_count,
    int* dealer_cards, int dealer_count,
    Shoe* shoe,
    curandState* state,
    float bet
) {
    // Player's turn
    while (true) {
        int hv = hand_value(player_cards, player_count);
        int total = hv % 100;

        if (total > 21) return -bet;
        if (total == 21) break;

        int action = get_action(player_cards, player_count, dealer_cards[0], false);

        if (action == 0) {
            break;
        } else if (action == 3) {
            if (player_count == 2) {
                player_cards[player_count++] = draw_card(shoe, state);
                bet *= 2.0f;
                break;
            }
            break;
        } else if (action == 1) {
            player_cards[player_count++] = draw_card(shoe, state);
        } else if (action == 2) {
            if (player_count == 2) {
                player_cards[player_count++] = draw_card(shoe, state);
                bet *= 2.0f;
                break;
            }
            player_cards[player_count++] = draw_card(shoe, state);
        } else {
            break;
        }
    }

    int player_total = hand_value(player_cards, player_count) % 100;
    if (player_total > 21) return -bet;

    int dealer_total = play_dealer(dealer_cards, dealer_count, shoe, state);

    if (dealer_total > 21) return bet;
    if (player_total > dealer_total) return bet;
    if (player_total < dealer_total) return -bet;
    return 0.0f;
}

// ============================================================================
// Main Simulation Kernel
// ============================================================================

__global__ void simulate_kernel(
    curandState* states,
    unsigned long long hands_per_thread,
    double* total_return,
    unsigned long long* total_hands
) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    curandState localState = states[tid];
    double thread_return = 0.0;

    // Initialize finite deck shoe for this thread
    Shoe shoe;
    init_shoe(&shoe, d_config.num_decks, d_config.penetration, &localState);

    // Continuous shuffle mode: reshuffle before every hand
    bool continuous_shuffle = (d_config.penetration <= 0.0f);

    for (unsigned long long i = 0; i < hands_per_thread; i++) {
        // In continuous shuffle mode, reshuffle before each hand
        if (continuous_shuffle) {
            reshuffle_shoe(&shoe, &localState);
        }

        int player_cards[12];
        int dealer_cards[12];

        player_cards[0] = draw_card(&shoe, &localState);
        player_cards[1] = draw_card(&shoe, &localState);
        dealer_cards[0] = draw_card(&shoe, &localState);
        dealer_cards[1] = draw_card(&shoe, &localState);

        int player_hv = hand_value(player_cards, 2);
        int dealer_hv = hand_value(dealer_cards, 2);
        bool player_bj = (player_hv % 100 == 21);
        bool dealer_bj = (dealer_hv % 100 == 21);

        float result;

        if (player_bj && dealer_bj) {
            result = 0.0f;
        } else if (player_bj) {
            result = d_config.blackjack_pays;
        } else if (dealer_bj) {
            result = -1.0f;
        } else {
            int action = get_action(player_cards, 2, dealer_cards[0], true);

            if (action == 4 && player_cards[0] == player_cards[1]) {
                // Split with resplit support
                int pair_card = player_cards[0];
                bool is_ace = (pair_card == 11);
                float split_result = 0.0f;

                // Hands array: each hand has cards[12], count, bet, is_from_ace_split
                int hands_cards[4][12];
                int hands_count[4];
                float hands_bet[4];
                bool hands_from_ace[4];
                int num_hands = 0;
                int max_hands = d_config.max_split_hands;

                // Initial split: create two hands
                hands_cards[0][0] = pair_card;
                hands_cards[0][1] = draw_card(&shoe, &localState);
                hands_count[0] = 2;
                hands_bet[0] = 1.0f;
                hands_from_ace[0] = is_ace;

                hands_cards[1][0] = pair_card;
                hands_cards[1][1] = draw_card(&shoe, &localState);
                hands_count[1] = 2;
                hands_bet[1] = 1.0f;
                hands_from_ace[1] = is_ace;

                num_hands = 2;

                // Check for resplits (process hands that might be pairs)
                // We iterate until no more splits possible
                bool did_split = true;
                while (did_split && num_hands < max_hands) {
                    did_split = false;
                    for (int h = 0; h < num_hands && num_hands < max_hands; h++) {
                        // Only check 2-card hands that haven't been played yet
                        if (hands_count[h] != 2) continue;

                        // Check if it's a pair
                        if (hands_cards[h][0] != hands_cards[h][1]) continue;

                        int new_pair_card = hands_cards[h][0];
                        bool new_is_ace = (new_pair_card == 11);

                        // Can't resplit aces unless allowed
                        if (new_is_ace && !d_config.resplit_aces) continue;

                        // Check if strategy says to split
                        int dealer_idx = dealer_cards[0] - 2;
                        int pair_idx = new_pair_card - 2;
                        int split_action = d_pair_strategy[pair_idx * 10 + dealer_idx];
                        if (split_action != 4) continue;

                        // Perform resplit
                        // Keep first card in current hand, add new card
                        hands_cards[h][1] = draw_card(&shoe, &localState);

                        // Create new hand with second card
                        hands_cards[num_hands][0] = new_pair_card;
                        hands_cards[num_hands][1] = draw_card(&shoe, &localState);
                        hands_count[num_hands] = 2;
                        hands_bet[num_hands] = 1.0f;
                        hands_from_ace[num_hands] = new_is_ace || hands_from_ace[h];
                        num_hands++;

                        did_split = true;
                        break;  // Restart loop to check new hands
                    }
                }

                // Now play out all hands
                int hands_total[4];
                for (int h = 0; h < num_hands; h++) {
                    if (hands_from_ace[h]) {
                        // Aces get one card only, already have it
                        hands_total[h] = hand_value(hands_cards[h], 2) % 100;
                    } else {
                        // Play normally
                        hands_total[h] = play_player_hand(
                            hands_cards[h], &hands_count[h],
                            dealer_cards[0], &hands_bet[h],
                            &shoe, &localState
                        );
                    }
                }

                // Dealer plays
                int dealer_total = play_dealer(dealer_cards, 2, &shoe, &localState);

                // Calculate results for each hand
                for (int h = 0; h < num_hands; h++) {
                    int pt = hands_total[h];
                    float bet = hands_bet[h];

                    if (pt > 21) {
                        split_result -= bet;
                    } else if (dealer_total > 21) {
                        split_result += bet;
                    } else if (pt > dealer_total) {
                        split_result += bet;
                    } else if (pt < dealer_total) {
                        split_result -= bet;
                    }
                    // Push: no change
                }

                result = split_result;
            } else {
                result = play_single_hand(player_cards, 2, dealer_cards, 2, &shoe, &localState, 1.0f);
            }
        }

        thread_return += result;
    }

    states[tid] = localState;
    atomicAdd(total_return, thread_return);
    atomicAdd(total_hands, hands_per_thread);
}

__global__ void init_rng_kernel(curandState* states, unsigned long long seed) {
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    curand_init(seed, tid, 0, &states[tid]);
}

// ============================================================================
// Main
// ============================================================================

int main(int argc, char** argv) {
    const char* strategy_file = "../web/public/strategies/8-s17-das-nrsa-sp4-peek-32.json";
    unsigned long long num_hands_billions = 1;
    int num_blocks = 34;
    int threads_per_block = 256;

    if (argc > 1) strategy_file = argv[1];
    if (argc > 2) num_hands_billions = atoll(argv[2]);
    if (argc > 3) num_blocks = atoi(argv[3]);
    if (argc > 4) threads_per_block = atoi(argv[4]);

    // Load strategy from JSON
    int8_t hard[180], soft[100], pairs[100];
    GameConfig config;

    printf("Loading strategy from: %s\n", strategy_file);
    if (!load_strategy(strategy_file, hard, soft, pairs, &config)) {
        return 1;
    }

    // Copy to GPU
    cudaMemcpyToSymbol(d_hard_strategy, hard, sizeof(hard));
    cudaMemcpyToSymbol(d_soft_strategy, soft, sizeof(soft));
    cudaMemcpyToSymbol(d_pair_strategy, pairs, sizeof(pairs));
    cudaMemcpyToSymbol(d_config, &config, sizeof(config));

    unsigned long long total_hands_target = num_hands_billions * 1000000000ULL;
    int total_threads = num_blocks * threads_per_block;
    unsigned long long hands_per_thread = total_hands_target / total_threads;

    printf("\n=== CUDA Monte Carlo Blackjack Simulator ===\n");
    printf("Target: %llu billion hands\n", num_hands_billions);
    printf("Threads: %d\n\n", total_threads);

    curandState* d_states;
    double* d_total_return;
    unsigned long long* d_total_hands;

    cudaMalloc(&d_states, total_threads * sizeof(curandState));
    cudaMalloc(&d_total_return, sizeof(double));
    cudaMalloc(&d_total_hands, sizeof(unsigned long long));
    cudaMemset(d_total_return, 0, sizeof(double));
    cudaMemset(d_total_hands, 0, sizeof(unsigned long long));

    printf("Initializing RNG...\n");
    init_rng_kernel<<<num_blocks, threads_per_block>>>(d_states, 42);
    cudaDeviceSynchronize();

    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    printf("Running simulation...\n");
    cudaEventRecord(start);
    simulate_kernel<<<num_blocks, threads_per_block>>>(d_states, hands_per_thread, d_total_return, d_total_hands);
    cudaEventRecord(stop);
    cudaDeviceSynchronize();

    cudaError_t err = cudaGetLastError();
    if (err != cudaSuccess) {
        printf("CUDA Error: %s\n", cudaGetErrorString(err));
        return 1;
    }

    float milliseconds = 0;
    cudaEventElapsedTime(&milliseconds, start, stop);

    double total_return;
    unsigned long long total_hands;
    cudaMemcpy(&total_return, d_total_return, sizeof(double), cudaMemcpyDeviceToHost);
    cudaMemcpy(&total_hands, d_total_hands, sizeof(unsigned long long), cudaMemcpyDeviceToHost);

    double house_edge = -total_return / total_hands * 100.0;
    double std_error = 1.14 / sqrt((double)total_hands) * 100.0;

    printf("\n=== Results ===\n");
    printf("Hands: %.2f billion\n", total_hands / 1e9);
    printf("House edge: %.4f%% +/- %.4f%%\n", house_edge, std_error * 1.96);
    printf("95%% CI: [%.4f%%, %.4f%%]\n", house_edge - std_error * 1.96, house_edge + std_error * 1.96);
    printf("Time: %.2f seconds\n", milliseconds / 1000.0);
    printf("Speed: %.2f million hands/sec\n", total_hands / milliseconds / 1000.0);

    cudaFree(d_states);
    cudaFree(d_total_return);
    cudaFree(d_total_hands);

    return 0;
}
