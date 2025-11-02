import torch
import torch.nn.functional as F
from torch.nn import Module, Linear
import numpy as np
import pandas as pd
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix
import time
import os

from torch_geometric.nn import SAGEConv, global_mean_pool
from torch_geometric.loader import DataLoader
from torch_geometric.data import Data
from torch_geometric.utils import k_hop_subgraph


def preprocess_hackathon_data(input_file):
    """
    Loads the hackathon data, renames/engineers columns to match our
    V2 training data format, and saves a new 'cleaned' CSV.
    """
    print(f"Loading hackathon data from '{input_file}'...")
    if not os.path.exists(input_file):
        print(f"Error: File not found at {input_file}")
        return

    df = pd.read_csv(input_file)
    print("Original columns:", df.columns.tolist())

    # --- 1. Define the "Adapter" Map ---
    # Maps (Their Column Name) -> (Our Column Name)
    column_map = {
        'originator_account': 'Sender_account',
        'beneficiary_account': 'Receiver_account',
        'amount': 'Amount',
        'booking_datetime': 'Timestamp', # We'll create Date/Time from this
        'originator_country': 'Sender_bank_location',
        'beneficiary_country': 'Receiver_bank_location',
        'channel': 'Payment_type',
        # We can map other columns if our V2 script uses them,
        # but these are the essentials.
    }

    # Rename columns
    df.rename(columns=column_map, inplace=True)

    # --- 2. Engineer the Label ---
    # Convert 'str_filed_datetime' to a 1/0 label
    # We assume 'not null' means it IS laundering
    if 'str_filed_datetime' in df.columns:
        df['Is_laundering'] = np.where(df['str_filed_datetime'].notnull(), 1, 0)
    else:
        # If no label, assume all are 0 (for final test data)
        df['Is_laundering'] = 0

    # --- 3. Engineer Date and Time columns ---
    # Our build_graph_v2.py script *expects* 'Date' and 'Time'
    if 'Timestamp' in df.columns:
        print("Parsing 'Timestamp' into 'Date' and 'Time'...")
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        df['Date'] = df['Timestamp'].dt.strftime('%Y-%m-%d')
        df['Time'] = df['Timestamp'].dt.strftime('%H:%M:%S')
    else:
        print("Error: Could not find 'booking_datetime' (renamed to 'Timestamp').")
        return

    # --- 4. Filter for *Only* the columns our script needs ---
    # This drops all the extra "golden" features we can't use
    required_columns = [
        'Time', 'Date', 'Sender_account', 'Receiver_account', 'Amount',
        'Payment_currency', 'Received_currency', 'Sender_bank_location',
        'Receiver_bank_location', 'Payment_type', 'Is_laundering'
    ]
    
    # Handle columns that might not exist in their data but are in ours
    # (e.g., Payment_currency, Received_currency)
    for col in required_columns:
        if col not in df.columns:
            print(f"Warning: Column '{col}' not found. Filling with 'NULL'.")
            # We map 'currency' to 'Payment_currency' as a fallback
            if col == 'Payment_currency' and 'currency' in df.columns:
                df['Payment_currency'] = df['currency']
            # We can't know received, so just copy payment
            elif col == 'Received_currency' and 'Payment_currency' in df.columns:
                 df['Received_currency'] = df['Payment_currency']
            else:
                df[col] = 'NULL' # Create a placeholder

    # Filter for *only* these columns
    df_cleaned = df[required_columns]

    return df_cleaned

# --- 1. Inductive GNN Model Definition ---
# This class MUST be identical to the one in train_inductive_model_V3.py
class InductiveGNN(Module):
    def __init__(self, num_node_features, hidden_dim, dropout=0.5):
        super(InductiveGNN, self).__init__()
        self.dropout_p = dropout
        self.conv1 = SAGEConv(num_node_features, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.conv3 = SAGEConv(hidden_dim, hidden_dim)
        self.lin1 = Linear(hidden_dim, hidden_dim // 2)
        self.lin2 = Linear(hidden_dim // 2, 2)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index); x = F.relu(x)
        x = self.conv2(x, edge_index); x = F.relu(x)
        x = self.conv3(x, edge_index); x = F.relu(x)
        x_pooled = global_mean_pool(x, batch)
        x = F.dropout(x_pooled, p=self.dropout_p, training=self.training)
        x = self.lin1(x); x = F.relu(x)
        x = self.lin2(x)
        return x

# --- 2. Evaluation Function ---
# This is our standard 'evaluate' function
@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    all_preds = []
    all_true = []
    
    for batch in loader:
        batch = batch.to(device)
        out = model(batch.x, batch.edge_index, batch.batch)
        pred = out.argmax(dim=1)
        
        all_preds.append(pred.cpu())
        all_true.append(batch.y.cpu())
        
    y_true = torch.cat(all_true).numpy()
    y_pred = torch.cat(all_preds).numpy()
    
    if len(y_true) == 0:
        print("Error: No data to evaluate.")
        return 0.0

    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, pos_label=1, average='binary', zero_division=0
    )
    
    print("\n--- Hackathon Sample 'Cheat Sheet' Results ---")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {p:.4f}")
    print(f"  Recall:    {r:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    print("  Confusion Matrix:")
    print(f"    TN: {cm[0][0]}  |  FP: {cm[0][1]}")
    print(f"    FN: {cm[1][0]}  |  TP: {cm[1][1]}")
    print("------------------------------------------")
    
    return f1

# --- 3. Main "Validation" Function ---
def validate_on_hackathon_data(hackathon_graph_path, champion_model_path, config):
    print("--- Starting Final Validation on Hackathon Sample ---")
    start_time = time.time()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    # --- 1. Load the Hackathon's Graph ---
    print(f"Loading hackathon graph from '{hackathon_graph_path}'...")
    try:
        data = torch.load(hackathon_graph_path, weights_only=False, map_location='cpu')
    except FileNotFoundError:
        print(f"Error: {hackathon_graph_path} not found.")
        print("Please run 'build_graph_V3_UNIVERSAL.py' first.")
        return
    
    # --- 2. Create Subgraphs from their data ---
    # We only care about nodes that have a label (0 or 1)
    all_nodes = torch.arange(data.num_nodes)
    pos_nodes = all_nodes[data.y == 1]
    neg_nodes = all_nodes[data.y == 0]
    
    target_nodes = torch.cat([pos_nodes, neg_nodes])
    target_labels = torch.cat([
        torch.ones(pos_nodes.size(0), dtype=torch.long),
        torch.zeros(neg_nodes.size(0), dtype=torch.long)
    ])
    
    if target_nodes.size(0) == 0:
        print("Error: The hackathon graph file has no labeled nodes (y=0 or y=1).")
        return
        
    print(f"Extracting subgraphs for {target_nodes.size(0)} labeled nodes...")
    subgraph_list = []
    for i in range(target_nodes.size(0)):
        subset, sub_edge_index, _, _ = k_hop_subgraph(
            node_idx=target_nodes[i].item(),
            num_hops=config['NUM_HOPS'],
            edge_index=data.edge_index,
            relabel_nodes=True,
        )
        subgraph_list.append(Data(x=data.x[subset], edge_index=sub_edge_index, y=target_labels[i]))
    
    print("Subgraph extraction complete.")
    
    # --- 3. Load the Champion "Profiler" Model ---
    print(f"Loading champion model from '{champion_model_path}'...")
    num_features = data.num_node_features
    
    model = InductiveGNN(
        num_node_features=num_features,
        hidden_dim=config['HIDDEN_DIM']
    ).to(device)
    
    try:
        model.load_state_dict(torch.load(champion_model_path, map_location=device))
    except FileNotFoundError:
        print(f"Error: Champion model file not found at '{champion_model_path}'")
        return

    # --- 4. Run Evaluation ---
    # Create a DataLoader for their subgraphs
    hackathon_loader = DataLoader(subgraph_list, batch_size=config['BATCH_SIZE'], shuffle=False)
    
    final_f1_score = evaluate(model, hackathon_loader, device)
    
    print("\n--- Validation Complete! ---")
    print(f"  Total time: {time.time() - start_time:.2f} seconds")
    print(f"  Final F1-Score on Hackathon Data: {final_f1_score:.4f}")
    print("---------------------------------")

if __name__ == "__main__":
    
    
    # --- Configuration ---
    # This is the graph you created from their 1000-row sample
    HACKATHON_GRAPH_FILE = 'hackathon_graph_V3.pt'
    
    # This is the champion model you just trained
    CHAMPION_MODEL_FILE = 'inductive_model_champion_V3.pth'
    
    CHAMPION_CONFIG = {
        "HIDDEN_DIM": 128,
        "NUM_HOPS": 2, # Must match the num_hops from create_subgraphs.py
        "BATCH_SIZE": 128
    }
    
    validate_on_hackathon_data(HACKATHON_GRAPH_FILE, CHAMPION_MODEL_FILE, CHAMPION_CONFIG)
