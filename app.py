import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import random
import string
from collections import defaultdict


def generate_dag(node_count, max_depth):
    
    nodes = list(string.ascii_uppercase[:node_count])
    G = nx.DiGraph()
    G.add_nodes_from(nodes)
    
    for i in range(1, node_count):
        possible_parents = nodes[max(0, i - max_depth):i]
        parent = random.choice(possible_parents)
        G.add_edge(parent, nodes[i])
    
    # Add some extra edges, ensuring we don't create cycles
    for i in range(node_count):
        possible_children = nodes[i+1:min(node_count, i + max_depth + 1)]
        num_extra_edges = random.randint(0, len(possible_children))
        for _ in range(num_extra_edges):
            if possible_children:
                child = random.choice(possible_children)
                G.add_edge(nodes[i], child)
                possible_children.remove(child)
    
    generations = list(nx.topological_generations(G))
    for i, generation in enumerate(generations):
        for node in generation:
            G.nodes[node]['layer'] = i
        
    return G
    
def set_seed(default_seed=123):
    random.seed(default_seed)
    
def visualize_dag(G, issue_nodes=None):
    pos = nx.multipartite_layout(G, subset_key="layer")
    plt.figure(figsize=(14, 10))
    
    node_colors = ['lightblue' if node not in (issue_nodes or []) else 'red' for node in G.nodes()]
    
    nx.draw(G, pos, with_labels=True, node_color=node_colors, 
            node_size=500, arrows=True, arrowsize=20, font_size=10, font_weight='bold', edge_color='gray')
    
    title = "Service Map DAG" if not issue_nodes else "Service Map DAG with Performance Issues Highlighted"
    plt.title(title, fontsize=16)
    plt.axis('off')
    return plt

def analyze_root_cause(G, issue_nodes):
    all_paths = []
    potential_root_causes = []

    # Find all paths between issue nodes
    for i, start in enumerate(issue_nodes):
        for end in issue_nodes[i+1:]:
            try:
                paths = list(nx.all_simple_paths(G, start, end))
                for path in paths:
                    all_paths.append("".join(path))
            except nx.NetworkXNoPath:
                continue
    
    # If only one path the edge is the root cause
    if len(all_paths) == 1:
        potential_root_causes.append(all_paths[0])
    else:
        # Identify edge nodes (potential root causes)
        for i in range(len(all_paths)):
            spath = all_paths.pop(0)
            not_in_count = 0
            all_path_count = 0
            for path in all_paths:
                all_path_count = all_path_count + 1
                if spath in path:
                    break
                else:
                    not_in_count = not_in_count + 1 
            if not_in_count == all_path_count:
                potential_root_causes.append(spath)
        
    # Count occurrences of each edge node in potential root cause paths
    root_cause_counts = defaultdict(int)
    for path in potential_root_causes:
        node = path[-1]
        root_cause_counts[node] += 1

    # Sort potential root causes by their occurrence count
    sorted_root_causes = sorted(root_cause_counts.items(), key=lambda x: x[1], reverse=True)

    return sorted_root_causes

def main():
    set_seed()
    
    st.title("Service Map DAG Analyzer")
    st.write("This tool generates random service maps, analyzes performance issues, and identifies potential root causes.")

    num_nodes = st.slider("Number of nodes", min_value=2, max_value=26, value=15)
    depth = st.slider("Minimum graph depth", min_value=2, max_value=20, step=1)

    if st.number_input("Random seed (optional)", min_value=0, value=123, key="seed"):
        set_seed(st.session_state.seed)
        
    if st.button("Generate New Random DAG"):
        dag = generate_dag(num_nodes, depth)
        st.session_state.dag = dag
        st.session_state.issue_nodes = []

    if 'dag' in st.session_state:
        fig = visualize_dag(st.session_state.dag)
        st.pyplot(fig)

        # Multi-select for nodes with performance issues
        all_nodes = list(st.session_state.dag.nodes)
        issue_nodes = st.multiselect("Select nodes with performance issues", all_nodes)

        if issue_nodes:
            st.session_state.issue_nodes = issue_nodes
            fig_issues = visualize_dag(st.session_state.dag, issue_nodes)
            st.pyplot(fig_issues)

            if st.button("Analyze Root Causes"):
                root_causes = analyze_root_cause(st.session_state.dag, issue_nodes)
                if root_causes:
                    st.write("### Potential Root Causes")
                    st.write("The following nodes are potential root causes of the performance issues, sorted by their occurrence in paths between issue nodes:")
                    for node, count in root_causes:
                        st.write(f"- Node **{node}**: Occurs in {count} path(s)")
                else:
                    st.write("No potential root causes could be identified. The selected issue nodes might be in disconnected parts of the graph or at the start of all paths.")

if __name__ == "__main__":
    main()