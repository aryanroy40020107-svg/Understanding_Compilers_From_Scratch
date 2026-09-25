import os
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.backends.backend_pdf import PdfPages

BASE_DIR = "/mnt/d/btech_jgec/2026-27/compiler_lab"
MATRIX_INPUT_TXT = os.path.join(BASE_DIR, "matrix_input.txt")
INCIDENCE_TXT = os.path.join(BASE_DIR, "incidence.txt")
TRACE_LOG = os.path.join(BASE_DIR, "trace_log.txt")
PATHS_LOG = os.path.join(BASE_DIR, "paths_log.txt")
TXT_OUTPUT = os.path.join(BASE_DIR, "matrix_output.txt")
OUTPUT_XLSX = os.path.join(BASE_DIR, "output.xlsx")
OUTPUT_PDF = os.path.join(BASE_DIR, "visualization_trace.pdf")

def update_excel():
    if os.path.exists(TXT_OUTPUT):
        df = pd.read_csv(TXT_OUTPUT, sep=r'\s+')
        df.to_excel(OUTPUT_XLSX, index=False)
        print(f"[✓] Output written to {OUTPUT_XLSX}")

def parse_paths_log():
    paths_by_node = {}
    if not os.path.exists(PATHS_LOG):
        return paths_by_node
        
    with open(PATHS_LOG, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            start_node = parts[0].split(":")[1]
            length = int(parts[1].split(":")[1])
            path_str = parts[2].split(":")[1]
            
            if start_node not in paths_by_node:
                paths_by_node[start_node] = []
            paths_by_node[start_node].append({
                "length": length, 
                "path_str": path_str, 
                "nodes": path_str.split("->")
            })
    return paths_by_node

def render_visualizations():
    paths_data = parse_paths_log()

    # Load Base Graph Structure from incidence.txt
    G = nx.DiGraph()
    left_nodes, right_nodes = [], []
    pos = {}

    if os.path.exists(INCIDENCE_TXT):
        with open(INCIDENCE_TXT, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        matrix_headers = lines[1].split()
        for name in matrix_headers:
            G.add_node(name)
            if name.startswith("f_") or "/f_" in name:
                left_nodes.append(name)
            else:
                right_nodes.append(name)

        for line in lines[2:]:
            parts = line.split()
            for edge_str in parts:
                if edge_str.startswith("E_"):
                    u_v = edge_str[2:].split("->")
                    if len(u_v) == 2:
                        G.add_edge(u_v[0], u_v[1])

        for idx, n in enumerate(left_nodes):
            pos[n] = (0, -idx * 1.5)
        for idx, n in enumerate(right_nodes):
            pos[n] = (1, -idx * 1.5)

    with PdfPages(OUTPUT_PDF) as pdf:

        # =========================================================================
        # SECTION 1: OPERATOR PRECEDENCE MATRIX
        # =========================================================================
        if os.path.exists(MATRIX_INPUT_TXT):
            with open(MATRIX_INPUT_TXT, "r") as f:
                raw_lines = [line.strip() for line in f.readlines() if line.strip()]

            if len(raw_lines) >= 2:
                num_symbols = int(raw_lines[0])
                headers = raw_lines[1].split()
                table_data = [["f \\ g"] + headers]

                for idx, line in enumerate(raw_lines[2:]):
                    parts = line.split()
                    row_symbol = headers[idx] if idx < len(headers) else f"r{idx}"

                    if len(parts) < num_symbols:
                        parts += [""] * (num_symbols - len(parts))
                    table_data.append([row_symbol] + parts[:num_symbols])

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.axis('off')

                table = ax.table(cellText=table_data, loc='center', cellLoc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(11)
                table.scale(1.2, 1.8)

                for (r, c), cell in table.get_celld().items():
                    if r == 0 or c == 0:
                        cell.set_facecolor('#2c3e50')
                        cell.get_text().set_color('white')
                        cell.get_text().set_weight('bold')
                    else:
                        val = cell.get_text().get_text()
                        if val == '>':
                            cell.set_facecolor('#d1e7dd')
                            cell.get_text().set_weight('bold')
                            cell.get_text().set_color('darkgreen')
                        elif val == '<':
                            cell.set_facecolor('#f8d7da')
                            cell.get_text().set_weight('bold')
                            cell.get_text().set_color('darkred')
                        elif val == '=':
                            cell.set_facecolor('#fff3cd')
                            cell.get_text().set_weight('bold')
                            cell.get_text().set_color('darkorange')
                        else:
                            cell.set_facecolor('#ffffff')

                ax.set_title("1. Operator Precedence Matrix", fontsize=14, fontweight='bold', pad=20)
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()

        # =========================================================================
        # SECTION 2: PRECEDENCE GRAPH SNAPSHOT
        # =========================================================================
        if os.path.exists(INCIDENCE_TXT):
            fig, ax = plt.subplots(figsize=(10, 7))

            node_colors = ['#ff9999' if (n.startswith("f_") or "/f_" in n) else '#99af89' for n in G.nodes()]
            
            nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colors, node_size=2200, edgecolors='black')
            nx.draw_networkx_labels(G, pos, ax=ax, font_size=10, font_weight='bold')

            nx.draw_networkx_edges(
                G, pos, ax=ax,
                arrows=True,
                arrowstyle='->',
                arrowsize=18,
                min_source_margin=25,
                min_target_margin=25,
                edge_color='#333333',
                connectionstyle="arc3,rad=0.12"
            )

            ax.set_title("2. Precedence Graph Snapshot", fontsize=14, fontweight='bold', pad=20)
            plt.axis('off')
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()

        # =========================================================================
        # SECTION 3: DUAL DFS STACK TRACE
        # =========================================================================
        if os.path.exists(TRACE_LOG):
            with open(TRACE_LOG, "r") as f:
                trace_lines = [line.strip() for line in f.readlines() if line.strip()]

            prev_stack_len = 0
            for step_num, line in enumerate(trace_lines, start=1):
                fig, (ax_graph, ax_stack) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={'width_ratios': [1.3, 1]})

                stack_items = []
                if "STACK:[" in line:
                    raw_stack = line.split("STACK:[")[1].rstrip("]")
                    if raw_stack:
                        stack_items = [s.strip() for s in raw_stack.split(",") if s.strip()]

                curr_stack_len = len(stack_items)
                action_type = "PUSH" if curr_stack_len > prev_stack_len else ("POP" if curr_stack_len < prev_stack_len else "TRAVERSE")
                prev_stack_len = curr_stack_len

                intermediate_edges = []
                active_edge = []
                if curr_stack_len >= 2:
                    full_edges = list(zip(stack_items[:-1], stack_items[1:]))
                    intermediate_edges = full_edges[:-1]
                    active_edge = [full_edges[-1]]

                node_colors = ['#ff9999' if (n.startswith("f_") or "/f_" in n) else '#99af89' for n in G.nodes()]
                nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1200, ax=ax_graph)
                nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold', ax=ax_graph)

                nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrows=True, arrowsize=10, 
                                       edge_color='#e0e0e0', width=1.0, connectionstyle="arc3,rad=0.1", ax=ax_graph)

                if intermediate_edges:
                    nx.draw_networkx_edges(G, pos, edgelist=intermediate_edges, arrowstyle='->', arrowsize=15, 
                                           min_source_margin=18, min_target_margin=18,
                                           edge_color='#ff8c00', width=2.5, connectionstyle="arc3,rad=0.1", ax=ax_graph)

                if active_edge:
                    nx.draw_networkx_edges(G, pos, edgelist=active_edge, arrowstyle='->', arrowsize=18, 
                                           min_source_margin=18, min_target_margin=18,
                                           edge_color='#ff0000', width=3.5, connectionstyle="arc3,rad=0.1", ax=ax_graph)

                path_str = " -> ".join(stack_items) if stack_items else "Empty"
                ax_graph.set_title(f"Active Path: {path_str}", fontsize=11, fontweight='bold', color='darkred')
                ax_graph.axis('off')

                ax_stack.axis('off')
                if stack_items:
                    table_data = [[item] for item in reversed(stack_items)]
                    cell_colors = [['#ff3333'] if i == 0 else ['#ffcccc'] for i in range(len(stack_items))]
                    st_table = ax_stack.table(cellText=table_data, cellColours=cell_colors, loc='bottom', cellLoc='center', bbox=[0.2, 0.05, 0.6, 0.55])
                    st_table.auto_set_font_size(False)
                    st_table.set_fontsize(11)

                    ax_stack.text(0.5, 0.90, f"Action: [{action_type}]", fontsize=14, fontweight='bold', color="darkred", ha='center', transform=ax_stack.transAxes)
                    ax_stack.text(0.5, 0.82, "DFS Stack Trace", fontsize=12, fontweight='bold', ha='center', transform=ax_stack.transAxes)

                plt.suptitle(f"3. DFS Step {step_num}", fontsize=14, fontweight='bold')
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()

        # =========================================================================
        # SECTION 4: OUTGOING PATH HIGHLIGHTS & LONGEST PATH SELECTION
        # =========================================================================
        colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00']

        if paths_data:
            for node, p_list in paths_data.items():
                fig, (ax_graph, ax_text) = plt.subplots(1, 2, figsize=(14, 7), gridspec_kw={'width_ratios': [1.2, 1]})

                node_colors = ['#ff9999' if (n.startswith("f_") or "/f_" in n) else '#99af89' for n in G.nodes()]
                nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1200, ax=ax_graph, edgecolors='black')
                nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold', ax=ax_graph)

                # Background Edges
                nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrows=True, arrowsize=10, 
                                       edge_color='#e0e0e0', width=1.0, connectionstyle="arc3,rad=0.1", ax=ax_graph)

                max_len = max(p['length'] for p in p_list) if p_list else 0

                # Highlight evaluated outgoing paths
                for p_idx, p_info in enumerate(p_list):
                    path_nodes = p_info['nodes']
                    p_edges = list(zip(path_nodes[:-1], path_nodes[1:]))
                    c = colors[p_idx % len(colors)]
                    lw = 3.5 if p_info['length'] == max_len else 1.8
                    nx.draw_networkx_edges(G, pos, edgelist=p_edges, arrowstyle='->', arrowsize=16, 
                                           min_source_margin=18, min_target_margin=18,
                                           edge_color=c, width=lw, connectionstyle="arc3,rad=0.1", ax=ax_graph)

                ax_graph.set_title(f"Traced Paths Starting from: {node}", fontsize=12, fontweight='bold')
                ax_graph.axis('off')

                # Side Text Box: Path Length Computations
                ax_text.axis('off')
                text_summary = [f"Computation for {node}", f"Traced paths starting from {node}:"]
                for p_info in p_list:
                    p_str = " -> ".join(p_info['nodes'])
                    is_max = (p_info['length'] == max_len)
                    prefix = "★ [MAX] " if is_max else "• "
                    text_summary.append(f"{prefix}{p_str} (Length = {p_info['length']})")

                text_summary.append(f"\nSelecting path of maximum length: {max_len}")
                text_summary.append(f"Hence, precedence function value = {max_len}")

                ax_text.text(0.05, 0.90, "\n".join(text_summary), fontsize=11, verticalalignment='top',
                             bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#cccccc"))

                plt.suptitle(f"4. Longest Path Calculation for Node: {node}", fontsize=14, fontweight='bold')
                plt.tight_layout()
                pdf.savefig(fig)
                plt.close()

        # =========================================================================
        # SECTION 5: FINAL PRECEDENCE FUNCTION TABLE
        # =========================================================================
        if os.path.exists(TXT_OUTPUT):
            df = pd.read_csv(TXT_OUTPUT, sep=r'\s+')
            
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.axis('off')

            symbols = list(df['Symbol'])
            f_vals = list(df['f'])
            g_vals = list(df['g'])

            table_data = [[""] + symbols, ["f"] + [str(x) for x in f_vals], ["g"] + [str(x) for x in g_vals]]

            table = ax.table(cellText=table_data, loc='center', cellLoc='center')
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1.2, 2.0)

            for (row, col), cell in table.get_celld().items():
                if row == 0 or col == 0:
                    cell.set_facecolor('#40466e')
                    cell.get_text().set_color('white')
                    cell.get_text().set_weight('bold')
                else:
                    cell.set_facecolor('#f1f1f2')

            ax.set_title("5. Final Computed Precedence Function Table", fontsize=14, fontweight='bold', pad=20)
            plt.tight_layout()
            pdf.savefig(fig)
            plt.close()

    print(f"[✓] Generated complete PDF with all 5 sections: {OUTPUT_PDF}")

if __name__ == "__main__":
    update_excel()
    render_visualizations()