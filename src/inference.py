import pandas as pd
import torch
import torch.nn.functional as F
from torch.nn import Module, Linear
import numpy as np
import pickle
import time
import os
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv, global_mean_pool
from torch_geometric.loader import DataLoader
from torch_geometric.utils import k_hop_subgraph
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple

# --- Configuration for Live Run ---
LIVE_DATA_FILE = 'dataset/transactions_mock_1000_for_participants.csv' # THIS IS THE INCOMING TRANSACTION
CHAMPION_MODEL_FILE = 'inductive_model_champion_V3.pth'
SCALER_FILE = 'scaler_V3.pkl' # MUST be the same one used for training
ACCOUNT_MAP_FILE = 'account_map_V3.pkl' # MUST be the same one used for training
ALERT_THRESHOLD = 0.85 # Risk score above which an alert is generated (Compliance/Risk defined)
INFERENCE_CONFIG = {
    "HIDDEN_DIM": 128,
    "NUM_HOPS": 2, # Must match the training configuration
    "BATCH_SIZE": 128
}

# --- 1. Universal Feature Maps (Copied from build_graph script) ---
PAYMENT_MAP = {
    'swift': 'feat_INTL_WIRE', 'sepa': 'feat_INTL_WIRE', 'rtgs': 'feat_INTL_WIRE',
    'fast (sg)': 'feat_DOMESTIC_FAST', 'fps (hk)': 'feat_DOMESTIC_FAST', 'cash': 'feat_CASH',
    'cheque': 'feat_LEGACY', 'cross-border': 'feat_INTL_WIRE', 'wire': 'feat_INTL_WIRE', 
    'cash deposit': 'feat_CASH', 'cash withdrawal': 'feat_CASH', 'ach': 'feat_DOMESTIC_FAST',
    'transfer': 'feat_DOMESTIC_FAST', 'credit card': 'feat_LEGACY', 'debit card': 'feat_LEGACY'
}
UNIVERSAL_FEATURES = ['feat_CASH', 'feat_INTL_WIRE', 'feat_DOMESTIC_FAST', 'feat_LEGACY']
# The full list of features created in your build_graph script:
FINAL_FEATURE_COLUMNS = [
    'total_sent', 'num_sent_tx', 'total_received', 'num_received_tx',
    'num_cross_border_tx_sent', 'num_cross_border_tx_received', 
    'num_night_tx_sent', 'num_night_tx_received', 'num_small_tx_sent', 
    'num_small_tx_received', 'avg_sent', 'avg_received', 'account_age_days', 
    'tx_frequency_per_day'
] + [f'sent_{f}' for f in UNIVERSAL_FEATURES] + [f'received_{f}' for f in UNIVERSAL_FEATURES]
# ---

# --- 2. Model Definition (Copied from validation script) ---
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

# --- 3. Prediction Function ---
@torch.no_grad()
def predict_and_score(model, loader, device) -> np.ndarray:
    """Runs the model and returns the raw prediction probability for the illicit class (1)."""
    model.eval()
    all_scores = []
    
    for batch in loader:
        batch = batch.to(device)
        out = model(batch.x, batch.edge_index, batch.batch)
        probs = F.softmax(out, dim=1)[:, 1] # Probability for the positive class (index 1)
        all_scores.append(probs.cpu())
        
    return torch.cat(all_scores).numpy()

# --- 4. Standalone Graph Building Logic (Adapted from create_graph_from_log_v3) ---
def auto_detect_columns(df_columns: List[str]) -> Dict[str, str]:
    """Detects which column names to use (Ours vs. Theirs) - Logic MUST be identical to train script."""
    col_map = {}
    
    if 'Sender_account' in df_columns:
        col_map.update({'sender_acct': 'Sender_account', 'receiver_acct': 'Receiver_account'})
    elif 'originator_account' in df_columns:
        col_map.update({'sender_acct': 'originator_account', 'receiver_acct': 'beneficiary_account'})
    else: raise ValueError("Could not find sender/receiver account columns!")
        
    if 'Payment_type' in df_columns: col_map['payment_type'] = 'Payment_type'
    elif 'channel' in df_columns: col_map['payment_type'] = 'channel'
    else: raise ValueError("Could not find payment type/channel column!")

    if 'Sender_bank_location' in df_columns:
        col_map.update({'sender_loc': 'Sender_bank_location', 'receiver_loc': 'Receiver_bank_location'})
    elif 'originator_country' in df_columns:
        col_map.update({'sender_loc': 'originator_country', 'receiver_loc': 'beneficiary_country'})
    else: raise ValueError("Could not find location/country columns!")
        
    if 'Amount' in df_columns: col_map['amount'] = 'Amount'
    elif 'amount' in df_columns: col_map['amount'] = 'amount'
    else: raise ValueError("Could not find amount column!")
        
    if 'Date' in df_columns and 'Time' in df_columns: col_map['time_mode'] = 'Date_Time'
    elif 'booking_datetime' in df_columns: col_map['time_mode'] = 'booking_datetime'
    else: raise ValueError("Could not find time/date columns!")
    
    # Label logic is skipped or set to 'none' for live inference
    col_map['label_mode'] = 'none' 
    return col_map

def build_inference_graph(log_csv_path: str, scaler_path: str, account_map_path: str, chunksize: int = 100000) -> Tuple[Data, Dict[str, int]]:
    """Builds the graph, but crucially uses the existing training scaler and account map."""
    print(f"Starting Graph Building for Live Inference on {log_csv_path}...")
    
    # --- Check for essential files ---
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Missing SCALER file: {scaler_path}. Cannot proceed without training scaler.")
    if not os.path.exists(account_map_path):
        raise FileNotFoundError(f"Missing ACCOUNT MAP file: {account_map_path}. Cannot map new accounts.")

    # --- Load Training-Time Assets ---
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
        
    with open(account_map_path, 'rb') as f:
        training_account_map = pickle.load(f)
    
    print(f"Loaded existing Scaler and Account Map ({len(training_account_map)} nodes).")
    
    # --- Pass 1: Discover all nodes and illicits (Only to get new nodes) ---
    all_accounts = set()
    try:
        df_head = pd.read_csv(log_csv_path, nrows=10)
    except Exception as e:
        print(f"Error reading {log_csv_path}: {e}"); return None, None
        
    col_map = auto_detect_columns(df_head.columns)
    
    # NOTE: The current graph logic re-maps ALL accounts. We will use the saved map for old accounts.
    
    # This loop is simplified: we only need to discover all accounts in the new log.
    for i, chunk in enumerate(pd.read_csv(log_csv_path, chunksize=chunksize, iterator=True)):
        all_accounts.update(chunk[col_map['sender_acct']])
        all_accounts.update(chunk[col_map['receiver_acct']])
        if (i + 1) % 5 == 0: print(f"  ...processed chunk {i+1} (Pass 1)")
    
    # --- Initialization using combined node list ---
    new_accounts = all_accounts.difference(set(training_account_map.keys()))
    print(f"Found {len(new_accounts)} NEW accounts for profiling.")
    
    # Create the final, combined node map: Old nodes first, then new nodes
    sorted_old_accounts = sorted(training_account_map.keys())
    sorted_new_accounts = sorted(list(new_accounts))
    
    final_account_list = sorted_old_accounts + sorted_new_accounts
    final_account_map = {acc_id: i for i, acc_id in enumerate(final_account_list)}
    num_nodes = len(final_account_list)
    
    # Feature matrix initialized with zeros for all nodes
    df_features = pd.DataFrame(0.0, index=final_account_list, columns=FINAL_FEATURE_COLUMNS)
    df_features['first_tx_timestamp'] = pd.to_datetime('2100-01-01')
    df_features['last_tx_timestamp'] = pd.to_datetime('1900-01-01')
    unique_edges = set()

    # --- Pass 2: Aggregate features and build edge list (Identical to training logic) ---
    print("--- Pass 2: Aggregating features and building edge list ---")
    
    for i, chunk in enumerate(pd.read_csv(log_csv_path, chunksize=chunksize, iterator=True)):
        
        # --- Time/Date Processing (Universal) ---
        if col_map['time_mode'] == 'Date_Time':
            chunk['timestamp'] = pd.to_datetime(chunk['Date'] + ' ' + chunk['Time'], errors='coerce')
        else: # 'booking_datetime'
            chunk['timestamp'] = pd.to_datetime(chunk[col_map['time_mode']], errors='coerce')
            
        chunk = chunk.dropna(subset=['timestamp'])
        chunk['hour_of_day'] = chunk['timestamp'].dt.hour
        chunk['is_night_tx'] = (chunk['hour_of_day'] >= 0) & (chunk['hour_of_day'] <= 5)
        chunk['is_small_tx'] = chunk[col_map['amount']] < 500 # Small TX threshold is hardcoded in your script

        # --- Aggregation Logic (Copied exactly from your create_graph_from_log_v3) ---
        # 1. Build edge list
        src = chunk[col_map['sender_acct']].map(final_account_map)
        dst = chunk[col_map['receiver_acct']].map(final_account_map)
        valid_edges = pd.concat([src, dst], axis=1).dropna()
        for edge_tuple in valid_edges.itertuples(index=False, name=None):
            if edge_tuple[0] != edge_tuple[1]: unique_edges.add(edge_tuple)

        # 2. Aggregate Amount/Count features
        sent_stats = chunk.groupby(col_map['sender_acct'])[col_map['amount']].agg(['sum', 'count'])
        df_features.loc[sent_stats.index, 'total_sent'] += sent_stats['sum']
        df_features.loc[sent_stats.index, 'num_sent_tx'] += sent_stats['count']
        received_stats = chunk.groupby(col_map['receiver_acct'])[col_map['amount']].agg(['sum', 'count'])
        df_features.loc[received_stats.index, 'total_received'] += received_stats['sum']
        df_features.loc[received_stats.index, 'num_received_tx'] += received_stats['count']
        
        # ... (Include all other aggregation steps: Payment, Cross-Border, Night/Small, Timestamps)
        # Note: For brevity in this response, I'll assume you would copy the full feature aggregation logic here.

        # 3. V3 Universal Payment Features
        payment_col = chunk[col_map['payment_type']]
        mapped_payments = payment_col.astype(str).str.lower().map(PAYMENT_MAP)
        payment_dummies = pd.get_dummies(mapped_payments)
        for feat in UNIVERSAL_FEATURES:
            if feat not in payment_dummies.columns: payment_dummies[feat] = 0
        payment_dummies = payment_dummies[UNIVERSAL_FEATURES]
        sender_dummies = payment_dummies.copy(); sender_dummies['Sender_account'] = chunk[col_map['sender_acct']]
        sender_payment_features = sender_dummies.groupby('Sender_account').sum()
        receiver_dummies = payment_dummies.copy(); receiver_dummies['Receiver_account'] = chunk[col_map['receiver_acct']]
        receiver_payment_features = receiver_dummies.groupby('Receiver_account').sum()
        df_features.loc[sender_payment_features.index, [f'sent_{f}' for f in UNIVERSAL_FEATURES]] += sender_payment_features.values
        df_features.loc[receiver_payment_features.index, [f'received_{f}' for f in UNIVERSAL_FEATURES]] += receiver_payment_features.values

        # 4. V3.1 Cross-Border Features
        chunk['is_cross_border'] = (chunk[col_map['sender_loc']] != chunk[col_map['receiver_loc']]).astype(int)
        sent_cross_border = chunk.groupby(col_map['sender_acct'])['is_cross_border'].sum()
        df_features.loc[sent_cross_border.index, 'num_cross_border_tx_sent'] += sent_cross_border
        received_cross_border = chunk.groupby(col_map['receiver_acct'])['is_cross_border'].sum()
        df_features.loc[received_cross_border.index, 'num_cross_border_tx_received'] += received_cross_border
        
        # 5. Time-Based Features (Night/Small)
        sent_night_tx = chunk[chunk['is_night_tx'] == True].groupby(col_map['sender_acct'])['is_night_tx'].count()
        df_features.loc[sent_night_tx.index, 'num_night_tx_sent'] += sent_night_tx
        received_night_tx = chunk[chunk['is_night_tx'] == True].groupby(col_map['receiver_acct'])['is_night_tx'].count()
        df_features.loc[received_night_tx.index, 'num_night_tx_received'] += received_night_tx
        sent_small_tx = chunk[chunk['is_small_tx'] == True].groupby(col_map['sender_acct'])['is_small_tx'].count()
        df_features.loc[sent_small_tx.index, 'num_small_tx_sent'] += sent_small_tx
        received_small_tx = chunk[chunk['is_small_tx'] == True].groupby(col_map['receiver_acct'])['is_small_tx'].count()
        df_features.loc[received_small_tx.index, 'num_small_tx_received'] += received_small_tx
        
        # 6. Update min/max timestamps
        sender_first_tx = chunk.groupby(col_map['sender_acct'])['timestamp'].min()
        sender_last_tx = chunk.groupby(col_map['sender_acct'])['timestamp'].max()
        receiver_first_tx = chunk.groupby(col_map['receiver_acct'])['timestamp'].min()
        receiver_last_tx = chunk.groupby(col_map['receiver_acct'])['timestamp'].max()
        all_first = pd.concat([sender_first_tx, receiver_first_tx]).groupby(level=0).min()
        all_last = pd.concat([sender_last_tx, receiver_last_tx]).groupby(level=0).max()
        df_features.loc[all_first.index, 'first_tx_timestamp'] = pd.concat([df_features.loc[all_first.index, 'first_tx_timestamp'], all_first], axis=1).min(axis=1)
        df_features.loc[all_last.index, 'last_tx_timestamp'] = pd.concat([df_features.loc[all_last.index, 'last_tx_timestamp'], all_last], axis=1).max(axis=1)
        
        if (i + 1) % 5 == 0: print(f"  ...processed chunk {i+1} (Pass 2)")

    # --- Final Feature Calculation (Copied exactly) ---
    df_features['avg_sent'] = df_features['total_sent'] / (df_features['num_sent_tx'] + 1e-6)
    df_features['avg_received'] = df_features['total_received'] / (df_features['num_received_tx'] + 1e-6)
    account_lifespan_seconds = (df_features['last_tx_timestamp'] - df_features['first_tx_timestamp']).dt.total_seconds()
    account_lifespan_seconds = account_lifespan_seconds.replace(0, 86400.0) 
    df_features['account_age_days'] = account_lifespan_seconds / 86400.0
    total_tx = df_features['num_sent_tx'] + df_features['num_received_tx']
    df_features['tx_frequency_per_day'] = total_tx / (df_features['account_age_days'] + 1e-6)
    
    df_features = df_features.reindex(columns=FINAL_FEATURE_COLUMNS).fillna(0.0)
    df_features = df_features.loc[final_account_list]
    
    # --- SCALING ---
    x_features = scaler.transform(df_features.values) # ONLY TRANSFORM, NEVER FIT
    x = torch.tensor(x_features, dtype=torch.float)
    
    # --- GRAPH FINALIZATION ---
    if not unique_edges: edge_index = torch.empty((2, 0), dtype=torch.long)
    else: edge_index = torch.tensor(np.array(list(unique_edges), dtype=np.int64).T, dtype=torch.long)
    
    # y=None is used for live inference as we have no labels
    data = Data(x=x, edge_index=edge_index, y=None) 
    data.num_classes = 2
    
    print(f"Feature matrix (x) shape: {x.shape}")
    return data, final_account_map

# --- 5. Main Inference Execution ---
def run_live_inference():
    """Main function to execute the full AML inference pipeline."""
    print(f"--- 🚨 Starting Live AML Inference Run on {LIVE_DATA_FILE} 🚨 ---")
    start_time = time.time()
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # --- STEP 1: Build the Graph from the Live Data ---
    live_graph, account_map = build_inference_graph(
        log_csv_path=LIVE_DATA_FILE,
        scaler_path=SCALER_FILE,
        account_map_path=ACCOUNT_MAP_FILE
    )
    
    if live_graph is None:
        print("Inference aborted due to graph building errors.")
        return

    # --- STEP 2: Load the Champion Model ---
    num_features = live_graph.num_node_features
    model = InductiveGNN(
        num_node_features=num_features,
        hidden_dim=INFERENCE_CONFIG['HIDDEN_DIM']
    ).to(device)
    
    try:
        model.load_state_dict(torch.load(CHAMPION_MODEL_FILE, map_location=device))
        print(f"Successfully loaded champion model from {CHAMPION_MODEL_FILE}.")
    except FileNotFoundError:
        print(f"Fatal Error: Champion model file not found at '{CHAMPION_MODEL_FILE}'. Exiting.")
        return

    # --- STEP 3: Define Target Nodes and Create Subgraphs ---
    # We profile ALL nodes (old and new) in the graph as a comprehensive check
    target_nodes_indices = torch.arange(live_graph.num_nodes)
    
    node_to_account_id = {v: k for k, v in account_map.items()}
    
    print(f"Extracting subgraphs for {target_nodes_indices.size(0)} nodes...")
    subgraph_list = []
    
    for node_idx in target_nodes_indices.tolist():
        subset, sub_edge_index, _, _ = k_hop_subgraph(
            node_idx=node_idx,
            num_hops=INFERENCE_CONFIG['NUM_HOPS'],
            edge_index=live_graph.edge_index,
            relabel_nodes=True,
        )
        
        # Attach the account ID and original index for post-processing
        subgraph_list.append(Data(
            x=live_graph.x[subset], 
            edge_index=sub_edge_index,
            account_id=node_to_account_id.get(node_idx, "Unknown"),
            original_node_idx=node_idx
        ))
    
    # --- STEP 4: Run Prediction ---
    inference_loader = DataLoader(subgraph_list, batch_size=INFERENCE_CONFIG['BATCH_SIZE'], shuffle=False)
    risk_scores = predict_and_score(model, inference_loader, device)

    # --- STEP 5: Generate Alert Output ---
    account_ids = [s.account_id for s in subgraph_list]
    
    alert_df = pd.DataFrame({
        'originator_account': account_ids,
        'Risk_Score': risk_scores
    })

    # Filter and sort for actionable alerts
    high_risk_alerts = alert_df[alert_df['Risk_Score'] >= ALERT_THRESHOLD].sort_values(
        'Risk_Score', ascending=False
    )
    
    # Save/Transmit alerts to the Case Management System
    if not high_risk_alerts.empty:
        output_file = f'aml_alerts_{time.strftime("%Y%m%d_%H%M%S")}.csv'
        high_risk_alerts.to_csv(output_file, index=False)
        print(f"\n✅ SUCCESS: {len(high_risk_alerts)} Alerts written to {output_file}")
    else:
        print("\n✅ SUCCESS: No high-risk alerts found above the threshold.")
    
    print(f"--- Inference Complete! Total time: {(time.time() - start_time):.2f} seconds ---")
    
    return high_risk_alerts

if __name__ == "__main__":
    # --- Create a dummy file for demonstration if it doesn't exist ---
    run_live_inference()