import os
import re
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, KeepTogether, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# 1. State array with uniform UPPERCASE representation
states = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'ERR']

# 2. Structural edge map updated
edges = [
    ('0', '1', '<'), ('0', '5', '='), ('0', '6', '>'),
    ('1', '2', '='), ('1', '3', '>'), ('1', '4', '*'),
    ('5', '9', '='), ('5', 'ERR', '*'),
    ('6', '7', '='), ('6', '8', '*')
]

# 3. Spatial textbook layout map with corrected string key mapping
pos = {
    '0': (0, 2),
    '1': (2, 4),   '5': (2, 2),   '6': (2, 0),
    '2': (4.5, 5), '3': (4.5, 4), '4': (4.5, 3),
    '9': (4.5, 2.3), 'ERR': (4.5, 1.7),
    '7': (4.5, 1), '8': (4.5, 0)
}

def parse_trace_file(filename):
    if not os.path.exists(filename):
        print(f"Error: Log file '{filename}' not found.")
        return []
    
    traces = []
    pattern = r"State\s+([0-9a-zA-Z\s\->]+)"
    
    with open(filename, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            
            match = re.search(pattern, line_str)
            if match:
                raw_path = match.group(1).replace(" ", "")
                state_sequence = raw_path.split("->")
            else:
                state_sequence = ['0']
                
            has_pushback = "retract" in line_str.lower() or "pushback" in line_str.lower()
            clean_desc = line_str.replace("<", "&lt;").replace(">", "&gt;")
            
            traces.append({
                "description": clean_desc,
                "path": state_sequence,
                "pushback": has_pushback
            })
            
    return traces

def generate_dfa_vector_image(log_desc, path):
    G = nx.DiGraph()
    G.add_nodes_from(states)
    for u, v, w in edges:
        G.add_edge(u, v, weight=w)
        
    fig, ax = plt.subplots(figsize=(7, 4.3))
    
    active_edges = []
    for idx in range(len(path) - 1):
        active_edges.append((path[idx], path[idx+1]))
        
    node_colors = []
    for node in G.nodes():
        if node == path[-1]:
            node_colors.append('#2ecc71')
        elif node in path:
            node_colors.append('#3498db')
        else:
            node_colors.append('#f8f9fa')
            
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=600, edgecolors='#7f8c8d', ax=ax)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold', ax=ax)
    
    for u, v in G.edges():
        is_active = (u, v) in active_edges
        edge_color = '#e74c3c' if is_active else '#bdc3c7'
        width = 2.5 if is_active else 1.0
        style = 'dashed' if 'pushback' in G[u][v]['weight'] else 'solid'
        
        nx.draw_networkx_edges(
            G, pos, edgelist=[(u,v)], edge_color=edge_color, width=width, 
            style=style, arrowsize=12, connectionstyle="arc3,rad=0.08", ax=ax
        )
        
    edge_labels = {(u, v): d['weight'] for u, v, d in G.edges(data=True)}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7, label_pos=0.5, ax=ax)
    
    ax.axis('off')
    plt.tight_layout()
    
    img_buf = BytesIO()
    plt.savefig(img_buf, format='png', dpi=120, bbox_inches='tight')
    img_buf.seek(0)
    plt.close(fig)
    
    return img_buf

def create_pdf_report(traces, output_filename, original_input):
    print(f"Creating PDF Report: {output_filename}...")
    
    doc = SimpleDocTemplate(output_filename, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontName='Helvetica-Bold',
        fontSize=20, leading=24, textColor='#2c3e50', spaceAfter=6, alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSub', parent=styles['Normal'], fontName='Helvetica-Oblique',
        fontSize=10, leading=14, textColor='#7f8c8d', spaceAfter=25, alignment=1
    )
    heading_style = ParagraphStyle(
        'StepHead', parent=styles['Heading2'], fontName='Helvetica-Bold',
        fontSize=13, leading=16, textColor='#2980b9', spaceBefore=15, spaceAfter=6
    )
    body_style = ParagraphStyle(
        'StepBody', parent=styles['Normal'], fontName='Helvetica',
        fontSize=10, leading=14, textColor='#2c3e50'
    )
    pushback_style = ParagraphStyle(
        'PushbackAlert', parent=body_style, fontName='Helvetica-Bold',
        textColor='#c0392b'
    )
    
    clean_input_text_style = ParagraphStyle(
        'CleanInput', parent=styles['Normal'], fontName='Courier-Bold',
        fontSize=12, leading=16, textColor='#2c3e50', spaceBefore=8, spaceAfter=20
    )

    story = []
    
    # Page 1 Header Elements
    story.append(Paragraph("Lexical Analysis Automata Execution Trace Report", title_style))
    story.append(Paragraph("Generated inside compiler1 workspace via integrated pipeline", subtitle_style))
    story.append(Spacer(1, 15))
    
    # Text Stream Presentation Blocks
    story.append(Paragraph("<b>Target Input Program Stream Evaluated:</b>", body_style))
    
    sanitized_input = original_input.replace("<", "&lt;").replace(">", "&gt;")
    story.append(Paragraph(f"&nbsp;&nbsp;{sanitized_input}", clean_input_text_style))
    story.append(Spacer(1, 15))
    
    df = pd.DataFrame(traces)
    
    if df.empty:
        story.append(Paragraph("No log execution steps recorded in input file source.", body_style))
        doc.build(story)
        return

    for idx, row in df.iterrows():
        step_elements = []
        step_num = idx + 1
        
        step_elements.append(Paragraph(f"Step {step_num}: Lexeme Transaction Trace", heading_style))
        step_elements.append(Paragraph(f"<b>Log Description:</b> {row['description']}", body_style))
        step_elements.append(Paragraph(f"<b>DFA Traveled State Sequence Path:</b> {' → '.join(row['path'])}", body_style))
        
        if row['pushback']:
            step_elements.append(Paragraph("<b>⚠️ Input Pushback (Retraction) Triggered:</b> Lexer engine encountered a structural code delimiter lookahead constraint. Stream pointer retracted by 1 step safely.", pushback_style))
        else:
            step_elements.append(Paragraph("<b>Pushback Status:</b> None (Direct terminal state validation match)", body_style))
            
        step_elements.append(Spacer(1, 8))
        
        img_stream = generate_dfa_vector_image(row['description'], row['path'])
        img_flowable = Image(img_stream, width=5.5*inch, height=3.4*inch)
        step_elements.append(img_flowable)
        step_elements.append(Spacer(1, 12))
        
        story.append(KeepTogether(step_elements))
        
        if step_num % 2 == 0 and step_num < len(df):
            story.append(PageBreak())

    def draw_background_box(canvas, document):
        if document.page == 1:
            canvas.saveState()
            canvas.setFillColorRGB(0.925, 0.941, 0.945)
            canvas.setStrokeColorRGB(0.741, 0.765, 0.780)
            canvas.setLineWidth(1)
            canvas.rect(0.45 * inch, 7.75 * inch, 7.6 * inch, 0.55 * inch, fill=1, stroke=1)
            canvas.restoreState()

    doc.build(story, onFirstPage=draw_background_box, onLaterPages=lambda c, d: None)
    print(f"Compressed PDF output successfully built at: {output_filename}")

if __name__ == "__main__":
    import sys
    input_path = "/mnt/d/btech_jgec/2026-27/compiler_lab/compiler1/lexer_trace.txt"
    output_path = "/mnt/d/btech_jgec/2026-27/compiler_lab/compiler1/dfa_trace_report.pdf"
    
    # SYSTEM INTERFACE FIX: Look for the environment variable populated by Jupyter
    raw_input_stream = os.getenv("JUPYTER_LEXER_INPUT")
    
    # Fallback to sys.argv or default string only if the environment variable is blank
    if not raw_input_stream:
        if len(sys.argv) > 1:
            raw_input_stream = sys.argv[1]
        else:
            raw_input_stream = "<=   <>   <   ==   >=   >   =   <= ) ("
            
    trace_data = parse_trace_file(input_path)
    if trace_data:
        create_pdf_report(trace_data, output_path, raw_input_stream)
