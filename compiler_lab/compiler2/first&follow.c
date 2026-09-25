#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAX_RULES 50
#define MAX_SYMBOLS 20

typedef struct {
    char lhs;
    char rhs[MAX_SYMBOLS];
} Production;

Production grammar[MAX_RULES];
int num_productions = 0;

char non_terminals[MAX_SYMBOLS];
int num_non_terminals = 0;

char first_sets[MAX_SYMBOLS][MAX_SYMBOLS];
char follow_sets[MAX_SYMBOLS][MAX_SYMBOLS];

// Function Prototypes
void add_non_terminal(char c);
int get_nt_index(char c);
int add_to_set(char *set, char val);
void compute_first();
void compute_follow();
void print_sets();
int parse_grammar_file(const char *filename);

int main() {
    char filename[100];
    printf("Enter the grammar text file name (e.g., grammar.txt): ");
    if (scanf("%99s", filename) != 1) return 1;

    // Step 1: Parse and expand the raw grammar file with diagnostics
    if (!parse_grammar_file(filename)) {
        printf("\n[ERROR] Could not read or parse the file correctly.\n");
        return 1;
    }

    printf("\nSuccessfully loaded and expanded %d production rules.\n", num_productions);

    // Initialize FIRST and FOLLOW sets safely
    for (int i = 0; i < num_non_terminals; i++) {
        first_sets[i][0] = '\0';
        follow_sets[i][0] = '\0';
    }

    // Rule 1 of FOLLOW: Place $ in FOLLOW(Start Symbol)
    int start_idx = get_nt_index(grammar[0].lhs);
    if (start_idx != -1) {
        add_to_set(follow_sets[start_idx], '$');
    }

    // Step 2: Compute and print sets
    compute_first();
    compute_follow();
    print_sets();

    return 0;
}

// Parses text files with robust cleaning and debug logging
int parse_grammar_file(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        printf("[DEBUG] Error: Could not open file '%s'\n", filename);
        return 0;
    }
    printf("[DEBUG] File opened successfully.\n");

    char line[256];
    int line_num = 0;
    int first_line = 1;

    while (fgets(line, sizeof(line), file)) {
        line_num++;
        char clean_line[256] = "";
        int len = 0;
        int start_idx = 0;

        // Skip UTF-8 BOM if present on the very first line
        if (first_line) {
            if ((unsigned char)line[0] == 0xEF && 
                (unsigned char)line[1] == 0xBB && 
                (unsigned char)line[2] == 0xBF) {
                start_idx = 3;
                printf("[DEBUG] UTF-8 BOM detected and skipped on line 1.\n");
            }
            first_line = 0;
        }

        // Clean out spaces, newlines, and carriage returns
        for (int i = start_idx; line[i] != '\0'; i++) {
            if (line[i] == '\r' || line[i] == '\n') continue;
            
            if (!isspace((unsigned char)line[i])) {
                clean_line[len++] = line[i];
            }
        }
        clean_line[len] = '\0';

        if (strlen(clean_line) == 0) {
            printf("[DEBUG] Line %d is empty, skipping.\n", line_num);
            continue;
        }

        char lhs = clean_line[0];
        char *arrow = strstr(clean_line, "->");
        if (arrow == NULL) {
            printf("[DEBUG] Line %d ignored (no '->' found). Cleaned text: '%s'\n", line_num, clean_line);
            continue;
        }

        printf("[DEBUG] Successfully parsed line %d: LHS=%c, Clean Line='%s'\n", line_num, lhs, clean_line);

        char *rhs_start = arrow + 2;
        add_non_terminal(lhs);

        // Split alternatives separated by '|'
        char *token = strtok(rhs_start, "|");
        while (token != NULL) {
            if (num_productions >= MAX_RULES) break;

            grammar[num_productions].lhs = lhs;
            strcpy(grammar[num_productions].rhs, token);

            // Register non-terminals written on RHS
            for (int j = 0; grammar[num_productions].rhs[j] != '\0'; j++) {
                add_non_terminal(grammar[num_productions].rhs[j]);
            }

            num_productions++;
            token = strtok(NULL, "|");
        }
    }

    fclose(file);
    printf("[DEBUG] Total productions parsed: %d\n", num_productions);
    return (num_productions > 0);
}

void add_non_terminal(char c) {
    if (!isupper(c)) return;
    for (int i = 0; i < num_non_terminals; i++) {
        if (non_terminals[i] == c) return;
    }
    non_terminals[num_non_terminals++] = c;
}

int get_nt_index(char c) {
    for (int i = 0; i < num_non_terminals; i++) {
        if (non_terminals[i] == c) return i;
    }
    return -1;
}

int add_to_set(char *set, char val) {
    int len = strlen(set);
    for (int i = 0; i < len; i++) {
        if (set[i] == val) return 0; 
    }
    set[len] = val;
    set[len + 1] = '\0';
    return 1; 
}

void compute_first() {
    int change = 1;
    while (change) {
        change = 0;
        for (int i = 0; i < num_productions; i++) {
            char lhs = grammar[i].lhs;
            int lhs_idx = get_nt_index(lhs);
            char *rhs = grammar[i].rhs;
            int rhs_len = strlen(rhs);
            
            if (rhs[0] == '#') {
                if (add_to_set(first_sets[lhs_idx], '#')) change = 1;
                continue;
            }
            
            int j;
            for (j = 0; j < rhs_len; j++) {
                char symbol = rhs[j];
                
                if (!isupper(symbol)) {
                    if (add_to_set(first_sets[lhs_idx], symbol)) change = 1;
                    break; 
                } else {
                    int sym_idx = get_nt_index(symbol);
                    if (sym_idx == -1) break;
                    
                    int has_epsilon = 0;
                    char *sym_first = first_sets[sym_idx];
                    
                    for (int k = 0; sym_first[k] != '\0'; k++) {
                        if (sym_first[k] != '#') {
                            if (add_to_set(first_sets[lhs_idx], sym_first[k])) change = 1;
                        } else {
                            has_epsilon = 1;
                        }
                    }
                    if (!has_epsilon) break;
                }
            }
            if (j == rhs_len) {
                if (add_to_set(first_sets[lhs_idx], '#')) change = 1;
            }
        }
    }
}

void compute_follow() {
    int change = 1;
    while (change) {
        change = 0;
        for (int i = 0; i < num_productions; i++) {
            char lhs = grammar[i].lhs;
            int lhs_idx = get_nt_index(lhs);
            char *rhs = grammar[i].rhs;
            int rhs_len = strlen(rhs);
            
            for (int j = 0; j < rhs_len; j++) {
                char B = rhs[j];
                if (!isupper(B)) continue; 
                
                int B_idx = get_nt_index(B);
                if (B_idx == -1) continue;
                
                int tail_derived_epsilon = 1;
                
                for (int k = j + 1; k < rhs_len; k++) {
                    char beta = rhs[k];
                    if (!isupper(beta)) {
                        if (add_to_set(follow_sets[B_idx], beta)) change = 1;
                        tail_derived_epsilon = 0;
                        break;
                    } else {
                        int beta_idx = get_nt_index(beta);
                        if (beta_idx == -1) { tail_derived_epsilon = 0; break; }
                        
                        int beta_has_epsilon = 0;
                        for (int m = 0; first_sets[beta_idx][m] != '\0'; m++) {
                            char f_sym = first_sets[beta_idx][m];
                            if (f_sym != '#') {
                                if (add_to_set(follow_sets[B_idx], f_sym)) change = 1;
                            } else {
                                beta_has_epsilon = 1;
                            }
                        }
                        if (!beta_has_epsilon) {
                            tail_derived_epsilon = 0;
                            break;
                        }
                    }
                }
                
                if (tail_derived_epsilon && lhs_idx != -1) {
                    for (int m = 0; follow_sets[lhs_idx][m] != '\0'; m++) {
                        if (add_to_set(follow_sets[B_idx], follow_sets[lhs_idx][m])) change = 1;
                    }
                }
            }
        }
    }
}

void print_sets() {
    printf("\n%-15s %-20s %-20s\n", "Non-Terminal", "FIRST Set", "FOLLOW Set");
    printf("------------------------------------------------------\n");
    for (int i = 0; i < num_non_terminals; i++) {
        printf("  %-13c { ", non_terminals[i]);
        for (int j = 0; first_sets[i][j] != '\0'; j++) {
            printf("%c ", first_sets[i][j]);
        }
        printf("} %-11s { ", "");
        for (int j = 0; follow_sets[i][j] != '\0'; j++) {
            printf("%c ", follow_sets[i][j]);
        }
        printf("}\n");
    }
}