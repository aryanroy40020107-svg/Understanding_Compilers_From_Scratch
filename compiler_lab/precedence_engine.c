#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_SYM 20
#define MAX_NODES 40

typedef struct {
    char name[30];
    int is_merged;
} Node;

int N;
char symbols[MAX_SYM][10];
char relation[MAX_SYM][MAX_SYM];

Node nodes[MAX_NODES];
int parent_node[MAX_NODES];
int num_nodes = 0;

int adj[MAX_NODES][MAX_NODES];
int visited[MAX_NODES];
int rec_stack[MAX_NODES];
int longest_path[MAX_NODES];

FILE *trace_file;
FILE *paths_file;

int find_set(int i) {
    if (parent_node[i] == i) return i;
    return parent_node[i] = find_set(parent_node[i]);
}

void union_sets(int i, int j) {
    int root_i = find_set(i);
    int root_j = find_set(j);
    if (root_i != root_j) {
        parent_node[root_i] = root_j;
    }
}

void log_stack(int stack[], int top, char* action) {
    fprintf(trace_file, "ACTION:%s|STACK:[", action);
    for (int i = 0; i <= top; i++) {
        fprintf(trace_file, "%s%s", nodes[stack[i]].name, (i == top) ? "" : ",");
    }
    fprintf(trace_file, "]\n");
}

int dfs_cycle(int u, int stack[], int *top) {
    visited[u] = 1;
    rec_stack[u] = 1;
    stack[++(*top)] = u;
    log_stack(stack, *top, "PUSH");

    for (int v = 0; v < num_nodes; v++) {
        if (adj[u][v]) {
            if (!visited[v]) {
                if (dfs_cycle(v, stack, top)) return 1;
            } else if (rec_stack[v]) {
                fprintf(trace_file, "CYCLE_DETECTED:%s->%s|STACK:[]\n", nodes[u].name, nodes[v].name);
                return 1;
            }
        }
    }

    log_stack(stack, *top, "POP");
    (*top)--;
    rec_stack[u] = 0;
    return 0;
}

void trace_all_paths(int u, int current_path[], int path_len, int start_node_idx) {
    current_path[path_len] = u;
    path_len++;

    int has_outgoing = 0;
    for (int v = 0; v < num_nodes; v++) {
        if (adj[u][v]) {
            has_outgoing = 1;
            trace_all_paths(v, current_path, path_len, start_node_idx);
        }
    }

    if (!has_outgoing || path_len > 1) {
        fprintf(paths_file, "START:%s|LENGTH:%d|PATH:", nodes[start_node_idx].name, path_len - 1);
        for (int i = 0; i < path_len; i++) {
            fprintf(paths_file, "%s%s", nodes[current_path[i]].name, (i == path_len - 1) ? "" : "->");
        }
        fprintf(paths_file, "\n");
    }
}

int get_longest_path(int u) {
    if (longest_path[u] != -1) return longest_path[u];
    int max_len = 0;
    for (int v = 0; v < num_nodes; v++) {
        if (adj[u][v]) {
            int len = 1 + get_longest_path(v);
            if (len > max_len) max_len = len;
        }
    }
    return longest_path[u] = max_len;
}

int main() {
    FILE *fin = fopen("/mnt/d/btech_jgec/2026-27/compiler_lab/matrix_input.txt", "r");
    if (!fin) { printf("Error opening input file\n"); return 1; }

    fscanf(fin, "%d", &N);
    for (int i = 0; i < N; i++) fscanf(fin, "%s", symbols[i]);
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            fscanf(fin, " %c", &relation[i][j]);
        }
    }
    fclose(fin);

    int total_raw_nodes = 2 * N;
    char raw_names[MAX_NODES][30];

    for (int i = 0; i < N; i++) {
        sprintf(raw_names[2 * i], "f_%s", symbols[i]);
        sprintf(raw_names[2 * i + 1], "g_%s", symbols[i]);
    }

    for (int i = 0; i < total_raw_nodes; i++) parent_node[i] = i;

    // 1. Merge equal precedence relations ('=')
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (relation[i][j] == '=') {
                union_sets(2 * i, 2 * j + 1);
            }
        }
    }

    // 2. Build component labels
    int rep_map[MAX_NODES];
    num_nodes = 0;

    for (int i = 0; i < total_raw_nodes; i++) {
        if (find_set(i) == i) {
            rep_map[i] = num_nodes;
            
            // Build merged string if multiple nodes share this root
            char combined_name[50] = "";
            int count = 0;
            for (int k = 0; k < total_raw_nodes; k++) {
                if (find_set(k) == i) {
                    if (count > 0) strcat(combined_name, "/");
                    strcat(combined_name, raw_names[k]);
                    count++;
                }
            }
            strcpy(nodes[num_nodes].name, combined_name);
            num_nodes++;
        }
    }

    // Map all non-root indices to representative ID
    int final_node_id[MAX_NODES];
    for (int i = 0; i < total_raw_nodes; i++) {
        final_node_id[i] = rep_map[find_set(i)];
    }

    // 3. Directed Edge Construction
    memset(adj, 0, sizeof(adj));
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            if (relation[i][j] == '<') {
                int u = final_node_id[2 * j + 1]; // g_j -> f_i
                int v = final_node_id[2 * i];
                if (u != v) adj[u][v] = 1;
            } else if (relation[i][j] == '>') {
                int u = final_node_id[2 * i];     // f_i -> g_j
                int v = final_node_id[2 * j + 1];
                if (u != v) adj[u][v] = 1;
            }
        }
    }

    // Write incidence snapshot text file
    FILE *finc = fopen("/mnt/d/btech_jgec/2026-27/compiler_lab/incidence.txt", "w");
    fprintf(finc, "INCIDENCE MATRIX\n");
    for (int i = 0; i < num_nodes; i++) fprintf(finc, "%s ", nodes[i].name);
    fprintf(finc, "\n");
    for (int i = 0; i < num_nodes; i++) {
        for (int j = 0; j < num_nodes; j++) {
            if (adj[i][j]) {
                fprintf(finc, "E_%s->%s ", nodes[i].name, nodes[j].name);
            }
        }
        fprintf(finc, "\n");
    }
    fclose(finc);

    // 4. Trace DFS & Cycle Detection
    trace_file = fopen("/mnt/d/btech_jgec/2026-27/compiler_lab/trace_log.txt", "w");
    int stack[MAX_NODES];
    int top = -1;

    memset(visited, 0, sizeof(visited));
    memset(rec_stack, 0, sizeof(rec_stack));

    for (int i = 0; i < num_nodes; i++) {
        if (!visited[i]) {
            if (dfs_cycle(i, stack, &top)) {
                printf("Error: Precedence graph contains cycles! Aborting.\n");
                fclose(trace_file);
                return 1;
            }
        }
    }
    fclose(trace_file);

    // 5. Trace path logs
    paths_file = fopen("/mnt/d/btech_jgec/2026-27/compiler_lab/paths_log.txt", "w");
    int current_path[MAX_NODES];
    for (int i = 0; i < num_nodes; i++) {
        trace_all_paths(i, current_path, 0, i);
    }
    fclose(paths_file);

    // 6. Compute longest path outputs
    memset(longest_path, -1, sizeof(longest_path));
    FILE *fout = fopen("/mnt/d/btech_jgec/2026-27/compiler_lab/matrix_output.txt", "w");
    fprintf(fout, "Symbol f g\n");
    for (int i = 0; i < N; i++) {
        int f_idx = final_node_id[2 * i];
        int g_idx = final_node_id[2 * i + 1];
        fprintf(fout, "%s %d %d\n", symbols[i], get_longest_path(f_idx), get_longest_path(g_idx));
    }

    fclose(fout);
    printf("[✓] Engine compiled and executed successfully!\n");
    return 0;
}