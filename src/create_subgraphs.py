import torch
import numpy as np
import time
from torch_geometric.data import Data
from torch.utils.data import random_split
from torch_geometric.utils import k_hop_subgraph
import pickle

def create_subgraph_dataset(data_path='train_graph_V3.pt', num_hops=2, num_neg_samples_per_pos=3):
    """
    V2 - LEAK-PROOF
    Loads the full V3 graph, splits the NODES into train/test,
    and *then* extracts subgraphs to prevent data leakage.
    """
    print(f"Starting LEAK-PROOF inductive dataset creation from {data_path}...")
    start_time = time.time()
    
    # --- 1. Load the full graph (on CPU) ---
    try:
        data = torch.load(data_path, weights_only=False, map_location='cpu')
    except FileNotFoundError:
        print(f"Error: Data file {data_path} not found.")
        print("Please run 'build_graph_V3_UNIVERSAL.py' first.")
        return
    except Exception as e:
        print(f"Error loading data: {e}")
        return
        
    print("Full V3 graph data loaded successfully.")
    
    # --- 2. Identify Positive and Negative Node Indices ---
    all_nodes = torch.arange(data.num_nodes)
    pos_nodes = all_nodes[data.y == 1]
    neg_nodes_all = all_nodes[data.y == 0]
    
    num_pos = pos_nodes.size(0)
    
    if num_pos == 0:
        print("Error: No positive (illicit) nodes found in the dataset. Cannot create subgraphs.")
        return
        
    # --- 3. THIS IS THE FIX: Split NODES before creating subgraphs ---
    print("Splitting nodes into Train/Test sets (80/20 split)...")
    
    # Shuffle positive nodes
    pos_perm = torch.randperm(pos_nodes.size(0))
    pos_split_idx = int(num_pos * 0.8)
    train_pos_nodes = pos_nodes[pos_perm[:pos_split_idx]]
    test_pos_nodes = pos_nodes[pos_perm[pos_split_idx:]]
    
    # Sample and shuffle negative nodes
    num_neg_total = num_pos * num_neg_samples_per_pos
    if num_neg_total > neg_nodes_all.size(0):
        print("Warning: Not enough negative nodes. Using all.")
        num_neg_total = neg_nodes_all.size(0)
        
    neg_perm = torch.randperm(neg_nodes_all.size(0))
    neg_nodes_sampled = neg_nodes_all[neg_perm[:num_neg_total]]
    
    neg_split_idx = int(num_neg_total * 0.8)
    train_neg_nodes = neg_nodes_sampled[:neg_split_idx]
    test_neg_nodes = neg_nodes_sampled[neg_split_idx:]
    
    print(f"  Training set: {train_pos_nodes.size(0)} illicit, {train_neg_nodes.size(0)} benign")
    print(f"  Test set:     {test_pos_nodes.size(0)} illicit, {test_neg_nodes.size(0)} benign")

    # --- 4. Helper function to extract subgraphs for a given set of nodes ---
    def extract_subgraphs(target_nodes, labels, graph_x, graph_edge_index, num_hops):
        subgraph_list = []
        for i in range(target_nodes.size(0)):
            target_node_idx = target_nodes[i]
            subset, sub_edge_index, _, _ = k_hop_subgraph(
                node_idx=target_node_idx.item(),
                num_hops=num_hops,
                edge_index=graph_edge_index,
                relabel_nodes=True,
            )
            sub_x = graph_x[subset]
            sub_y = labels[i]
            subgraph_list.append(Data(x=sub_x, edge_index=sub_edge_index, y=sub_y))
        return subgraph_list
    # ---

    # --- 5. Extract Subgraphs for TRAIN and TEST sets separately ---
    print(f"Extracting {num_hops}-hop subgraphs for TRAIN set...")
    train_nodes = torch.cat([train_pos_nodes, train_neg_nodes])
    train_labels = torch.cat([
        torch.ones(train_pos_nodes.size(0), dtype=torch.long),
        torch.zeros(train_neg_nodes.size(0), dtype=torch.long)
    ])
    train_dataset = extract_subgraphs(train_nodes, train_labels, data.x, data.edge_index, num_hops)
    print("Train subgraph extraction complete.")

    print(f"Extracting {num_hops}-hop subgraphs for TEST set...")
    test_nodes = torch.cat([test_pos_nodes, test_neg_nodes])
    test_labels = torch.cat([
        torch.ones(test_pos_nodes.size(0), dtype=torch.long),
        torch.zeros(test_neg_nodes.size(0), dtype=torch.long)
    ])
    test_dataset = extract_subgraphs(test_nodes, test_labels, data.x, data.edge_index, num_hops)
    print("Test subgraph extraction complete.")

    # --- 6. Save the New, LEAK-PROOF Datasets ---
    output_path_train = 'inductive_train_dataset_V3.pt'
    output_path_test = 'inductive_test_dataset_V3.pt'
    
    torch.save(train_dataset, output_path_train)
    torch.save(test_dataset, output_path_test)
    
    end_time = time.time()
    print("\n--- LEAK-PROOF Inductive Dataset Creation Success! ---")
    print(f"  Total time: {end_time - start_time:.2f} seconds")
    print(f"  Training set: {len(train_dataset)} subgraphs (saved to '{output_path_train}')")
    print(f"  Test set:     {len(test_dataset)} subgraphs (saved to '{output_path_test}')")
    print("---------------------------------------------")

if __name__ == "__main__":
    create_subgraph_dataset(data_path='train_graph_V3.pt')

