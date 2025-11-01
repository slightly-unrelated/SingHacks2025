import pandas as pd
import torch
import torch.nn.functional as F
from torch.nn import Module, Linear
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
import time
import os
import argparse

# --- Torch Geometric Imports ---
from torch_geometric.nn import SAGEConv, global_mean_pool
from torch_geometric.loader import DataLoader
from torch_geometric.data import Data
from torch_geometric.utils import k_hop_subgraph

# --- 
# SECTION 1: PREPROCESSING LOGIC
# ---

PAYMENT_MAP = {
    'swift': 'feat_INTL_WIRE', 'sepa': 'feat_INTL_WIRE', 'rtgs': 'feat_INTL_WIRE',
    'fast (sg)': 'feat_DOMESTIC_FAST', 'fps (hk)': 'feat_DOMESTIC_FAST',
    'cash': 'feat_CASH', 'cheque': 'feat_LEGACY', 'cross-border': 'feat_INTL_WIRE',
    'wire': 'feat_INTL_WIRE', 'cash deposit': 'feat_CASH', 'cash withdrawal': 'feat_CASH',
    'ach': 'feat_DOMESTIC_FAST', 'transfer': 'feat_DOMESTIC_FAST',
    'credit card': 'feat_LEGACY', 'debit card': 'feat_LEGACY'
}
UNIVERSAL_FEATURES = ['feat_CASH', 'feat_INTL_WIRE', 'feat_DOMESTIC_FAST', 'feat_LEGACY']

# --- CRUCIAL FX RATES for standardization (UK/GBP focus) ---
FX_RATES = {
    'GBP': 1.0, 'USD': 0.82, 'EUR': 0.87, 'SGD': 0.60, 'HKD': 0.10, 'NULL': 1.0 
}
TARGET_CURRENCY = 'GBP'
# -----------------------------------------------------------

def _rename_and_engineer_columns(df):
    """
    Adapts the incoming hackathon CSV chunk to match the V3 feature expectation.
    This replaces the need for a separate 'preprocess_hackathon_data' script.
    """
    # 1. Define the "Adapter" Map
    column_map = {
        'originator_account': 'Sender_account',
        'beneficiary_account': 'Receiver_account',
        'amount': 'Amount',
        'booking_datetime': 'Timestamp',
        'originator_country': 'Sender_bank_location',
        'beneficiary_country': 'Receiver_bank_location',
        'channel': 'Payment_type',
        'currency': 'Payment_currency' # Assume 'currency' is the payment currency
    }

    # Rename columns that exist in the chunk
    df.rename(columns={k: v for k, v in column_map.items() if k in df.columns}, inplace=True)
    
    # 2. Engineer Date/Time for V3's internal logic
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        # We don't need Date/Time columns anymore because V3 auto-detects 'booking_datetime'
        # but the original logic still looks for them in Pass 2 if 'Date_Time' mode is set.
        # We'll stick to 'booking_datetime' equivalent ('Timestamp' here)
    
    # 3. Currency Standardization (FX Conversion) - CRUCIAL FIX
    if 'Payment_currency' in df.columns and 'Amount' in df.columns:
        df['Payment_currency'] = df['Payment_currency'].fillna('NULL').str.upper()
        df['FX_Rate'] = df['Payment_currency'].map(FX_RATES).fillna(1.0)
        df['Amount'] = df['Amount'] * df['FX_Rate']
    else:
        # Fallback for missing currency columns to prevent crash
        df['Payment_currency'] = 'NULL'
        
    # 4. Fill missing required columns
    # We must ensure all columns expected by the V3 script's feature engine exist
    if 'Received_currency' not in df.columns and 'Payment_currency' in df.columns:
        df['Received_currency'] = df['Payment_currency']
    
    # This function returns the modified DataFrame chunk, which then proceeds to Pass 2.
    return df


def auto_detect_columns(df_columns):
    # This function is now simplified because the new preprocessor has standardized the names.
    col_map = {}
    if 'Sender_account' in df_columns:
        col_map['sender_acct'] = 'Sender_account'
        col_map['receiver_acct'] = 'Receiver_account'
    if 'Payment_type' in df_columns:
        col_map['payment_type'] = 'Payment_type'
    if 'Sender_bank_location' in df_columns:
        col_map['sender_loc'] = 'Sender_bank_location'
        col_map['receiver_loc'] = 'Receiver_bank_location'
    if 'Amount' in df_columns:
        col_map['amount'] = 'Amount'
    if 'Timestamp' in df_columns:
        col_map['time_mode'] = 'booking_datetime' # Now always use the unified 'booking_datetime' logic
    
    # Assume no labels for inference
    col_map['label_mode'] = 'none' 

    return col_map


def create_graph_from_log_v3(log_csv_path, chunksize=100000, small_tx_threshold=500, scaler_path=None):
    print(f"Starting V3.2 UNIVERSAL processing of {log_csv_path}...")
    start_time = time.time()

    # --- Pass 1: Discover all nodes ---
    print("--- Pass 1: Discovering all nodes ---")
    all_accounts = set()
    
    # Peek at head to get columns
    try: 
        df_head = pd.read_csv(log_csv_path, nrows=10)
    except Exception as e: 
        print(f"Error reading {log_csv_path}: {e}"); return
    
    # The auto-detect needs the *renamed* columns, so we run the renamer first on the head
    df_head = _rename_and_engineer_columns(df_head)
    col_map = auto_detect_columns(df_head.columns)

    for i, chunk in enumerate(pd.read_csv(log_csv_path, chunksize=chunksize, iterator=True)):
        # --- NEW STEP: PREPROCESS EACH CHUNK ---
        chunk = _rename_and_engineer_columns(chunk)
        # -------------------------------------
        
        all_accounts.update(chunk[col_map['sender_acct']])
        all_accounts.update(chunk[col_map['receiver_acct']])
    print(f"Pass 1 complete. Found {len(all_accounts)} nodes.")
    
    print("--- Initializing feature matrices ---")
    sorted_accounts = sorted(list(all_accounts))
    account_map = {acc_id: i for i, acc_id in enumerate(sorted_accounts)}
    num_nodes = len(sorted_accounts)

    y = torch.zeros(num_nodes, dtype=torch.long) 

    base_features = [
        'total_sent', 'num_sent_tx', 'total_received', 'num_received_tx',
        'num_cross_border_tx_sent', 'num_cross_border_tx_received',
        'num_night_tx_sent', 'num_night_tx_received',
        'num_small_tx_sent', 'num_small_tx_received'
    ]
    payment_features = [f'sent_{f}' for f in UNIVERSAL_FEATURES] + [f'received_{f}' for f in UNIVERSAL_FEATURES]
    feature_columns = base_features + payment_features
    df_features = pd.DataFrame(0.0, index=account_map.keys(), columns=feature_columns)
    df_features['first_tx_timestamp'] = pd.to_datetime('2100-01-01')
    df_features['last_tx_timestamp'] = pd.to_datetime('1900-01-01')
    unique_edges = set()

    print("--- Pass 2: Aggregating features and building edge list ---")
    for i, chunk in enumerate(pd.read_csv(log_csv_path, chunksize=chunksize, iterator=True)):
        # --- NEW STEP: PREPROCESS EACH CHUNK ---
        chunk = _rename_and_engineer_columns(chunk)
        # -------------------------------------

        # --- Time/Date Processing ---
        chunk['timestamp'] = chunk['Timestamp'] # Use the renamed/parsed 'Timestamp' column
        chunk = chunk.dropna(subset=['timestamp'])
        chunk['hour_of_day'] = chunk['timestamp'].dt.hour
        chunk['is_night_tx'] = (chunk['hour_of_day'] >= 0) & (chunk['hour_of_day'] <= 5)
        chunk['is_small_tx'] = chunk[col_map['amount']] < small_tx_threshold
        
        # --- The rest of the feature aggregation remains the same ---
        src = chunk[col_map['sender_acct']].map(account_map)
        dst = chunk[col_map['receiver_acct']].map(account_map)
        valid_edges = pd.concat([src, dst], axis=1).dropna()
        for edge_tuple in valid_edges.itertuples(index=False, name=None):
            if edge_tuple[0] != edge_tuple[1]: unique_edges.add(edge_tuple)

        sent_stats = chunk.groupby(col_map['sender_acct'])[col_map['amount']].agg(['sum', 'count'])
        df_features.loc[sent_stats.index, 'total_sent'] += sent_stats['sum']
        df_features.loc[sent_stats.index, 'num_sent_tx'] += sent_stats['count']
        received_stats = chunk.groupby(col_map['receiver_acct'])[col_map['amount']].agg(['sum', 'count'])
        df_features.loc[received_stats.index, 'total_received'] += received_stats['sum']
        df_features.loc[received_stats.index, 'num_received_tx'] += received_stats['count']

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

        chunk['is_cross_border'] = (chunk[col_map['sender_loc']] != chunk[col_map['receiver_loc']]).astype(int)
        sent_cross_border = chunk.groupby(col_map['sender_acct'])['is_cross_border'].sum()
        df_features.loc[sent_cross_border.index, 'num_cross_border_tx_sent'] += sent_cross_border
        received_cross_border = chunk.groupby(col_map['receiver_acct'])['is_cross_border'].sum()
        df_features.loc[received_cross_border.index, 'num_cross_border_tx_received'] += received_cross_border
        
        sent_night_tx = chunk[chunk['is_night_tx'] == True].groupby(col_map['sender_acct'])['is_night_tx'].count()
        df_features.loc[sent_night_tx.index, 'num_night_tx_sent'] += sent_night_tx
        received_night_tx = chunk[chunk['is_night_tx'] == True].groupby(col_map['receiver_acct'])['is_night_tx'].count()
        df_features.loc[received_night_tx.index, 'num_night_tx_received'] += received_night_tx
        sent_small_tx = chunk[chunk['is_small_tx'] == True].groupby(col_map['sender_acct'])['is_small_tx'].count()
        df_features.loc[sent_small_tx.index, 'num_small_tx_sent'] += sent_small_tx
        received_small_tx = chunk[chunk['is_small_tx'] == True].groupby(col_map['receiver_acct'])['is_small_tx'].count()
        df_features.loc[received_small_tx.index, 'num_small_tx_received'] += received_small_tx

        sender_first_tx = chunk.groupby(col_map['sender_acct'])['timestamp'].min()
        sender_last_tx = chunk.groupby(col_map['sender_acct'])['timestamp'].max()
        receiver_first_tx = chunk.groupby(col_map['receiver_acct'])['timestamp'].min()
        receiver_last_tx = chunk.groupby(col_map['receiver_acct'])['timestamp'].max()
        all_first = pd.concat([sender_first_tx, receiver_first_tx]).groupby(level=0).min()
        all_last = pd.concat([sender_last_tx, receiver_last_tx]).groupby(level=0).max()
        df_features.loc[all_first.index, 'first_tx_timestamp'] = pd.concat([df_features.loc[all_first.index, 'first_tx_timestamp'], all_first], axis=1).min(axis=1)
        df_features.loc[all_last.index, 'last_tx_timestamp'] = pd.concat([df_features.loc[all_last.index, 'last_tx_timestamp'], all_last], axis=1).max(axis=1)

    print("Pass 2 complete.")
    print("--- Finalizing features and graph ---")
    
    df_features['avg_sent'] = df_features['total_sent'] / (df_features['num_sent_tx'] + 1e-6)
    df_features['avg_received'] = df_features['total_received'] / (df_features['num_received_tx'] + 1e-6)
    account_lifespan_seconds = (df_features['last_tx_timestamp'] - df_features['first_tx_timestamp']).dt.total_seconds()
    account_lifespan_seconds = account_lifespan_seconds.replace(0, 86400.0) 
    df_features['account_age_days'] = account_lifespan_seconds / 86400.0
    total_tx = df_features['num_sent_tx'] + df_features['num_received_tx']
    df_features['tx_frequency_per_day'] = total_tx / (df_features['account_age_days'] + 1e-6)
    final_feature_columns = base_features + ['avg_sent', 'avg_received', 'account_age_days', 'tx_frequency_per_day'] + payment_features
    df_features = df_features.reindex(columns=final_feature_columns).fillna(0.0)
    df_features = df_features.loc[sorted_accounts]

    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler file not found at {scaler_path}. Please provide the correct path.")
    
    print(f"Loading existing scaler from {scaler_path}...")
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    x_features = scaler.transform(df_features.values)
    
    x = torch.tensor(x_features, dtype=torch.float)
    if not unique_edges:
        print("Warning: No valid edges found."); edge_index = torch.empty((2, 0), dtype=torch.long)
    else:
        edge_array = np.array(list(unique_edges), dtype=np.int64).T
        edge_index = torch.tensor(edge_array, dtype=torch.long)
    
    data = Data(x=x, edge_index=edge_index, y=y)
    data.num_classes = 2
    
    print(f"Total processing time: {(time.time() - start_time):.2f} seconds")
    
    return data, account_map

# --- 
# SECTION 2: GNN MODEL DEFINITION
# ---

class InductiveGNN(Module):
    # ... (Model Definition is the same as before) ...
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

# --- 
# SECTION 3: INFERENCE LOGIC
# ---

def run_inference(input_csv, output_csv, model_path, scaler_path):
    """
    Runs the full inference pipeline on a new CSV file.
    """
    start_time = time.time()
    
    # --- 1. Process new data and build graph ---
    print("--- 1. Processing new data and building graph ---")
    if not os.path.exists(input_csv):
        raise FileNotFoundError(f"Input file not found at {input_csv}")
        
    # The core change: create_graph_from_log_v3 now handles the column renaming internally
    data, account_map = create_graph_from_log_v3(input_csv, scaler_path=scaler_path)
    rev_account_map = {idx: acc for acc, idx in account_map.items()}
    
    # --- 2. Extract subgraphs for ALL nodes ---
    print(f"--- 2. Extracting subgraphs for {data.num_nodes} nodes ---")
    subgraph_list = []
    node_id_map = [] 
    
    for node_idx in range(data.num_nodes):
        subset, sub_edge_index, _, _ = k_hop_subgraph(
            node_idx=node_idx,
            num_hops=2, # Must match your training config
            edge_index=data.edge_index,
            relabel_nodes=True,
        )
        subgraph = Data(x=data.x[subset], edge_index=sub_edge_index, y=0)
        subgraph_list.append(subgraph)
        node_id_map.append(node_idx) 
    
    print("Subgraph extraction complete.")
    
    # --- 3. Load champion model ---
    print(f"--- 3. Loading champion model from {model_path} ---")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")

    num_features = data.num_node_features
    model = InductiveGNN(
        num_node_features=num_features,
        hidden_dim=128 # Must match your training config
    ).to(device)
    
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval() 
    
    # --- 4. Run predictions ---
    print("--- 4. Running predictions ---")
    loader = DataLoader(subgraph_list, batch_size=128, shuffle=False)
    
    all_preds = []
    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)
            out = model(batch.x, batch.edge_index, batch.batch)
            pred = out.argmax(dim=1)
            all_preds.append(pred.cpu())
            
    final_preds = torch.cat(all_preds).numpy()
    
    # --- 5. Map predictions and save results ---
    print("--- 5. Mapping predictions and saving results ---")
    results = []
    for i in range(len(final_preds)):
        original_node_idx = node_id_map[i]
        account_id = rev_account_map[original_node_idx]
        prediction = final_preds[i] # 0 or 1
        
        results.append({
            'account_id': account_id,
            'is_laundering_prediction': prediction
        })
        
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_csv, index=False)
    
    print("\n--- Inference Complete! ---")
    print(f"  Total accounts processed: {len(df_results)}")
    print(f"  Alerts generated (pred=1): {df_results['is_laundering_prediction'].sum()}")
    print(f"  Results saved to: {output_csv}")
    print(f"  Total time: {time.time() - start_time:.2f} seconds")

# --- 
# SECTION 4: MAIN EXECUTION
# ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GNN inference for AML.")
    
    parser.add_argument(
        '--input_csv', 
        type=str, 
        required=True, 
        help="Path to the new transaction log CSV file."
    )
    parser.add_argument(
        '--output_csv', 
        type=str, 
        default='predictions.csv', 
        help="Path to save the output predictions CSV. (default: predictions.csv)"
    )
    parser.add_argument(
        '--model_path', 
        type=str, 
        default='inductive_model_champion_V3.pth',
        help="Path to the trained .pth model file. (default: inductive_model_champion_V3.pth)"
    )
    parser.add_argument(
        '--scaler_path', 
        type=str, 
        default='scaler_V3.pkl',
        help="Path to the saved .pkl scaler file. (default: scaler_V3.pkl)"
    )
    
    args = parser.parse_args()
    
    run_inference(
        input_csv=args.input_csv,
        output_csv=args.output_csv,
        model_path=args.model_path,
        scaler_path=args.scaler_path
    )