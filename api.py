import io
import time
import os
import pickle
import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
from torch.nn import Module, Linear
from torch_geometric.data import Data
from torch_geometric.nn import SAGEConv, global_mean_pool
from torch_geometric.loader import DataLoader
from torch_geometric.utils import k_hop_subgraph
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Tuple
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# --- Configuration for Live Run ---
# NOTE: The actual file is uploaded, so LIVE_DATA_FILE is mostly ignored here.
# These paths must exist and contain the files created during training.
CHAMPION_MODEL_FILE = 'inductive_model_champion_V3.pth'
SCALER_FILE = 'scaler_V3.pkl' 
ACCOUNT_MAP_FILE = 'account_map_V3.pkl'
ALERT_THRESHOLD = 0.85 
INFERENCE_CONFIG = {
    "HIDDEN_DIM": 128,
    "NUM_HOPS": 2, 
    "BATCH_SIZE": 128
}

# --- Global Variables for Assets (Loaded once at startup) ---
GLOBAL_ASSETS = {}

# --- 1. Universal Feature Maps ---
# (Must be copied here for the graph builder to access them)
PAYMENT_MAP = {
    'swift': 'feat_INTL_WIRE', 'sepa': 'feat_INTL_WIRE', 'rtgs': 'feat_INTL_WIRE',
    'fast (sg)': 'feat_DOMESTIC_FAST', 'fps (hk)': 'feat_DOMESTIC_FAST', 'cash': 'feat_CASH',
    'cheque': 'feat_LEGACY', 'cross-border': 'feat_INTL_WIRE', 'wire': 'feat_INTL_WIRE', 
    'cash deposit': 'feat_CASH', 'cash withdrawal': 'feat_CASH', 'ach': 'feat_DOMESTIC_FAST',
    'transfer': 'feat_DOMESTIC_FAST', 'credit card': 'feat_LEGACY', 'debit card': 'feat_LEGACY'
}
UNIVERSAL_FEATURES = ['feat_CASH', 'feat_INTL_WIRE', 'feat_DOMESTIC_FAST', 'feat_LEGACY']
FINAL_FEATURE_COLUMNS = [
    'total_sent', 'num_sent_tx', 'total_received', 'num_received_tx',
    'num_cross_border_tx_sent', 'num_cross_border_tx_received', 
    'num_night_tx_sent', 'num_night_tx_received', 'num_small_tx_sent', 
    'num_small_tx_received', 'avg_sent', 'avg_received', 'account_age_days', 
    'tx_frequency_per_day'
] + [f'sent_{f}' for f in UNIVERSAL_FEATURES] + [f'received_{f}' for f in UNIVERSAL_FEATURES]
# ---

# --- 2. Model Definition ---
class InductiveGNN(Module):
    def __init__(self, num_node_features, hidden_dim, dropout=0.5):
        super(InductiveGNN, self).__init__()
        # ... (GNN layer initialization remains the same)
        self.dropout_p = dropout
        self.conv1 = SAGEConv(num_node_features, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.conv3 = SAGEConv(hidden_dim, hidden_dim)
        self.lin1 = Linear(hidden_dim, hidden_dim // 2)
        self.lin2 = Linear(hidden_dim // 2, 2)
    def forward(self, x, edge_index, batch):
        # ... (forward pass remains the same)
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
        probs = F.softmax(out, dim=1)[:, 1]
        all_scores.append(probs.cpu())
        
    return torch.cat(all_scores).numpy()

# --- 4. Standalone Graph Building Logic (Modified to take DataFrame directly) ---
def auto_detect_columns(df_columns: List[str]) -> Dict[str, str]:
    # ... (column detection logic remains the same)
    col_map = {}
    if 'Sender_account' in df_columns or 'originator_account' in df_columns:
        col_map.update({'sender_acct': 'Sender_account', 'receiver_acct': 'Receiver_account'} if 'Sender_account' in df_columns else {'sender_acct': 'originator_account', 'receiver_acct': 'beneficiary_account'})
    else: raise ValueError("Could not find sender/receiver account columns!")
    if 'Payment_type' in df_columns or 'channel' in df_columns:
        col_map['payment_type'] = 'Payment_type' if 'Payment_type' in df_columns else 'channel'
    else: raise ValueError("Could not find payment type/channel column!")
    if 'Sender_bank_location' in df_columns or 'originator_country' in df_columns:
        col_map.update({'sender_loc': 'Sender_bank_location', 'receiver_loc': 'Receiver_bank_location'} if 'Sender_bank_location' in df_columns else {'sender_loc': 'originator_country', 'receiver_loc': 'beneficiary_country'})
    else: raise ValueError("Could not find location/country columns!")
    if 'Amount' in df_columns or 'amount' in df_columns:
        col_map['amount'] = 'Amount' if 'Amount' in df_columns else 'amount'
    else: raise ValueError("Could not find amount column!")
    if ('Date' in df_columns and 'Time' in df_columns) or 'booking_datetime' in df_columns:
        col_map['time_mode'] = 'Date_Time' if ('Date' in df_columns and 'Time' in df_columns) else 'booking_datetime'
    else: raise ValueError("Could not find time/date columns!")
    col_map['label_mode'] = 'none' 
    return col_map

def build_inference_graph_from_df(df_input: pd.DataFrame, scaler: StandardScaler, training_account_map: Dict[str, int]) -> Tuple[Data, Dict[str, int]]:
    """
    MODIFIED: Takes DataFrame and pre-loaded assets directly. 
    Returns: PyTorch Geometric Data object and the final account map.
    """
    chunksize = 100000 # Used for internal logic, but we process the whole df here
    
    df_head = df_input.head(10)
    col_map = auto_detect_columns(df_head.columns)

    # --- Pass 1: Discover all nodes (simplified, as we have the whole DF) ---
    all_accounts = set(df_input[col_map['sender_acct']]) | set(df_input[col_map['receiver_acct']])
    
    # --- Initialization using combined node list ---
    new_accounts = all_accounts.difference(set(training_account_map.keys()))
    sorted_old_accounts = sorted(training_account_map.keys())
    sorted_new_accounts = sorted(list(new_accounts))
    
    final_account_list = sorted_old_accounts + sorted_new_accounts
    final_account_map = {acc_id: i for i, acc_id in enumerate(final_account_list)}
    num_nodes = len(final_account_list)
    
    df_features = pd.DataFrame(0.0, index=final_account_list, columns=FINAL_FEATURE_COLUMNS)
    df_features['first_tx_timestamp'] = pd.to_datetime('2100-01-01')
    df_features['last_tx_timestamp'] = pd.to_datetime('1900-01-01')
    unique_edges = set()

    # --- Pass 2: Aggregate features and build edge list ---
    chunk = df_input.copy() # The whole dataframe is our single chunk
    
    # --- Time/Date Processing (Universal) ---
    if col_map['time_mode'] == 'Date_Time':
        chunk['timestamp'] = pd.to_datetime(chunk['Date'] + ' ' + chunk['Time'], errors='coerce')
    else: 
        chunk['timestamp'] = pd.to_datetime(chunk[col_map['time_mode']], errors='coerce')
        
    chunk = chunk.dropna(subset=['timestamp'])
    chunk['hour_of_day'] = chunk['timestamp'].dt.hour
    chunk['is_night_tx'] = (chunk['hour_of_day'] >= 0) & (chunk['hour_of_day'] <= 5)
    chunk['is_small_tx'] = chunk[col_map['amount']] < 500 

    # --- Aggregation Logic (The long section copied exactly) ---
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
    
    # --- Final Feature Calculation ---
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
    x_features = scaler.transform(df_features.values)
    x = torch.tensor(x_features, dtype=torch.float)
    
    # --- GRAPH FINALIZATION ---
    if not unique_edges: edge_index = torch.empty((2, 0), dtype=torch.long)
    else: edge_index = torch.tensor(np.array(list(unique_edges), dtype=np.int64).T, dtype=torch.long)
    
    data = Data(x=x, edge_index=edge_index, y=None) 
    data.num_classes = 2
    
    # Return the unscaled features DF as well (needed for final JSON output)
    return data, final_account_map, df_features 

# --- 5. Application Lifecycle & Setup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads the model and assets globally at startup."""
    try:
        print("--- Loading Global ML Assets ---")
        # 1. Load Scaler and Account Map
        with open(SCALER_FILE, 'rb') as f:
            GLOBAL_ASSETS['scaler'] = pickle.load(f)
        with open(ACCOUNT_MAP_FILE, 'rb') as f:
            GLOBAL_ASSETS['account_map'] = pickle.load(f)

        # 2. Load Model
        num_features = len(FINAL_FEATURE_COLUMNS) # Feature count is fixed
        GLOBAL_ASSETS['device'] = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        model = InductiveGNN(
            num_node_features=num_features, 
            hidden_dim=INFERENCE_CONFIG['HIDDEN_DIM']
        ).to(GLOBAL_ASSETS['device'])
        
        model.load_state_dict(torch.load(CHAMPION_MODEL_FILE, map_location=GLOBAL_ASSETS['device']))
        model.eval()
        GLOBAL_ASSETS['model'] = model
        print("Global Assets loaded successfully. API Ready.")

    except FileNotFoundError as e:
        print(f"FATAL ERROR: Asset file not found: {e}. Check paths: {CHAMPION_MODEL_FILE}, {SCALER_FILE}, {ACCOUNT_MAP_FILE}")
        GLOBAL_ASSETS['model'] = None # Mark as failed
        raise
        
    yield
    print("--- API Shutdown ---")

app = FastAPI(
    title="AML GNN Batch Inference Service",
    version="V3.1",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 6. API Endpoint ---
@app.post("/api/v1/infer_batch")
async def infer_aml_batch(
    file: UploadFile = File(..., description="CSV file containing a batch of transactions.")
):
    """
    Accepts a CSV file, runs GNN inference, and returns high-risk account features and scores as JSON.
    """
    if GLOBAL_ASSETS.get('model') is None:
        raise HTTPException(status_code=503, detail="Service unavailable: ML Model failed to load on startup.")
    
    start_time = time.time()
    
    # --- 1. Read Uploaded File into Pandas (In-Memory) ---
    try:
        contents = await file.read()
        buffer = io.StringIO(contents.decode('utf-8'))
        raw_df = pd.read_csv(buffer)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {e}")

    # --- 2. Run the Full Inference Pipeline (Preprocess + Graph + Score) ---
    try:
        # Pass the DataFrame, scaler, and map directly to the modified graph builder
        live_graph, account_map, df_features_unscaled = build_inference_graph_from_df(
            df_input=raw_df,
            scaler=GLOBAL_ASSETS['scaler'],
            training_account_map=GLOBAL_ASSETS['account_map']
        )
        
        # --- 3. Run GNN Scoring ---
        node_to_account_id = {v: k for k, v in account_map.items()}
        target_nodes_indices = torch.arange(live_graph.num_nodes)
        
        subgraph_list = []
        for node_idx in target_nodes_indices.tolist():
            subset, sub_edge_index, _, _ = k_hop_subgraph(
                node_idx=node_idx, num_hops=INFERENCE_CONFIG['NUM_HOPS'],
                edge_index=live_graph.edge_index, relabel_nodes=True,
            )
            subgraph_list.append(Data(
                x=live_graph.x[subset], edge_index=sub_edge_index,
                account_id=node_to_account_id.get(node_idx, "Unknown"),
            ))
        
        inference_loader = DataLoader(subgraph_list, batch_size=INFERENCE_CONFIG['BATCH_SIZE'], shuffle=False)
        risk_scores = predict_and_score(GLOBAL_ASSETS['model'], inference_loader, GLOBAL_ASSETS['device'])
        account_ids = [s.account_id for s in subgraph_list]
        
        # DataFrame containing every profiled account and its score
        all_account_scores = pd.DataFrame({
            'Account_ID': account_ids,
            'Risk_Score': risk_scores
        }).set_index('Account_ID')

        # --- 4. Merge Score onto Feature Matrix (X) and Filter ---
        final_output_df = df_features_unscaled.copy()
        final_output_df = final_output_df.join(all_account_scores, how='left')
        
        # Filter the final output to only show accounts that exceed the ALERT_THRESHOLD
        final_alert_df = final_output_df[
            final_output_df['Risk_Score'] >= ALERT_THRESHOLD
        ].sort_values('Risk_Score', ascending=False)

        # --- 5. Return JSON ---
        if final_alert_df.empty:
            return {"status": "success", "alerts_found": 0, "message": "No high-risk accounts detected."}
        
        # Convert DataFrame to JSON (orient='records' is the list of objects format)
        json_output = final_alert_df.reset_index().rename(columns={'index': 'Account_ID'}).to_dict(orient='records')
        
        print(f"Inference complete in {time.time() - start_time:.2f} seconds. Alerts: {len(json_output)}")
        
        return {
            "status": "success",
            "alerts_found": len(json_output),
            "alerts": json_output
        }

    except Exception as e:
        print(f"INFERENCE ERROR: {e}")
        # Return a non-blocking 500 error
        raise HTTPException(status_code=500, detail=f"Internal server error during GNN processing: {e}")

# --- 7. Execution ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)