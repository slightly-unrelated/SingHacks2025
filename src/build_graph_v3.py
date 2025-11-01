import pandas as pd
import torch
from torch_geometric.data import Data
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
import pickle
import time
import os

# --- 1. Our New "Universal Feature Map" ---
PAYMENT_MAP = {
    # Their values (lowercase)
    'swift': 'feat_INTL_WIRE',
    'sepa': 'feat_INTL_WIRE',
    'rtgs': 'feat_INTL_WIRE',
    'fast (sg)': 'feat_DOMESTIC_FAST',
    'fps (hk)': 'feat_DOMESTIC_FAST',
    'cash': 'feat_CASH',
    'cheque': 'feat_LEGACY',
    
    # Our values (lowercase)
    'cross-border': 'feat_INTL_WIRE',
    'wire': 'feat_INTL_WIRE', # Adding this as a fallback
    'cash deposit': 'feat_CASH',
    'cash withdrawal': 'feat_CASH',
    'ach': 'feat_DOMESTIC_FAST',
    'transfer': 'feat_DOMESTIC_FAST',
    'credit card': 'feat_LEGACY',
    'debit card': 'feat_LEGACY'
}
UNIVERSAL_FEATURES = ['feat_CASH', 'feat_INTL_WIRE', 'feat_DOMESTIC_FAST', 'feat_LEGACY']
# ---

def auto_detect_columns(df_columns):
    """
    Detects which column names to use (Ours vs. Theirs)
    """
    col_map = {}
    
    # --- Account IDs ---
    if 'Sender_account' in df_columns:
        col_map['sender_acct'] = 'Sender_account'
        col_map['receiver_acct'] = 'Receiver_account'
    elif 'originator_account' in df_columns:
        col_map['sender_acct'] = 'originator_account'
        col_map['receiver_acct'] = 'beneficiary_account'
    else:
        raise ValueError("Could not find sender/receiver account columns!")
        
    # --- Payment Type ---
    if 'Payment_type' in df_columns:
        col_map['payment_type'] = 'Payment_type'
    elif 'channel' in df_columns:
        col_map['payment_type'] = 'channel'
    else:
        raise ValueError("Could not find payment type/channel column!")

    # --- Location ---
    if 'Sender_bank_location' in df_columns:
        col_map['sender_loc'] = 'Sender_bank_location'
        col_map['receiver_loc'] = 'Receiver_bank_location'
    elif 'originator_country' in df_columns:
        col_map['sender_loc'] = 'originator_country'
        col_map['receiver_loc'] = 'beneficiary_country'
    else:
        raise ValueError("Could not find location/country columns!")
        
    # --- Amount ---
    if 'Amount' in df_columns:
        col_map['amount'] = 'Amount'
    elif 'amount' in df_columns:
        col_map['amount'] = 'amount'
    else:
        raise ValueError("Could not find amount column!")
        
    # --- Time & Date ---
    if 'Date' in df_columns and 'Time' in df_columns:
        col_map['time_mode'] = 'Date_Time'
    elif 'booking_datetime' in df_columns:
        col_map['time_mode'] = 'booking_datetime'
    else:
        raise ValueError("Could not find time/date columns!")
        
    # --- Label ---
    if 'Is_laundering' in df_columns:
        col_map['label_mode'] = 'Is_laundering'
    elif 'str_filed_datetime' in df_columns:
        col_map['label_mode'] = 'str_filed_datetime'
    else:
        print("Warning: No label column found. Defaulting 'Is_laundering' to 0.")
        col_map['label_mode'] = 'none'

    print(f"Auto-detected columns: {col_map}")
    return col_map


def create_graph_from_log_v3(log_csv_path, chunksize=100000, small_tx_threshold=500, scaler_path=None):
    """
    V3.1: Reads any log, auto-detects columns, builds graph with
    V2 Time Features AND V3 Universal Payment Features.
    
    NEW in V3.1:
    - Uses scaler_path to load/save the StandardScaler.
    - Uses robust "is_cross_border" feature instead of "domestic_location".
    """
    print(f"Starting V3.1 UNIVERSAL processing of {log_csv_path}...")
    start_time = time.time()

    # --- Pass 1: Discover all nodes and illicit accounts ---
    print("--- Pass 1: Discovering all nodes and illicit accounts ---")
    all_accounts = set()
    illicit_accounts = set()
    
    try:
        df_head = pd.read_csv(log_csv_path, nrows=10)
    except Exception as e:
        print(f"Error reading {log_csv_path}: {e}"); return
        
    col_map = auto_detect_columns(df_head.columns)
    
    for i, chunk in enumerate(pd.read_csv(log_csv_path, chunksize=chunksize, iterator=True)):
        all_accounts.update(chunk[col_map['sender_acct']])
        all_accounts.update(chunk[col_map['receiver_acct']])
        
        if col_map['label_mode'] == 'Is_laundering':
            illicit_senders = chunk[chunk['Is_laundering'] == 1][col_map['sender_acct']]
            illicit_receivers = chunk[chunk['Is_laundering'] == 1][col_map['receiver_acct']]
        elif col_map['label_mode'] == 'str_filed_datetime':
            illicit_senders = chunk[chunk['str_filed_datetime'].notnull()][col_map['sender_acct']]
            illicit_receivers = chunk[chunk['str_filed_datetime'].notnull()][col_map['receiver_acct']]
        else:
            illicit_senders, illicit_receivers = [], []
            
        illicit_accounts.update(illicit_senders)
        illicit_accounts.update(illicit_receivers)
        
        if (i + 1) % 5 == 0:
             print(f"  ...processed chunk {i+1} (Pass 1)")

    print(f"Pass 1 complete. Found {len(all_accounts)} nodes.")
    
    # --- Initialization ---
    print("--- Initializing feature matrices and labels ---")
    sorted_accounts = sorted(list(all_accounts))
    account_map = {acc_id: i for i, acc_id in enumerate(sorted_accounts)}
    num_nodes = len(sorted_accounts)

    y = torch.zeros(num_nodes, dtype=torch.long)
    illicit_node_indices = [account_map[acc] for acc in illicit_accounts if acc in account_map]
    y[illicit_node_indices] = 1
    print(f"Created label vector. {y.sum().item()} nodes marked as 'illicit'.")

    # --- NEW: V3.1 Universal Feature List ---
    base_features = [
        'total_sent', 'num_sent_tx', 'total_received', 'num_received_tx',
        'num_cross_border_tx_sent', 'num_cross_border_tx_received', # <-- RENAMED
        'num_night_tx_sent', 'num_night_tx_received',
        'num_small_tx_sent', 'num_small_tx_received'
    ]
    payment_features = [f'sent_{f}' for f in UNIVERSAL_FEATURES] + \
                       [f'received_{f}' for f in UNIVERSAL_FEATURES]
    feature_columns = base_features + payment_features
    
    df_features = pd.DataFrame(0.0, index=account_map.keys(), columns=feature_columns)
    df_features['first_tx_timestamp'] = pd.to_datetime('2100-01-01')
    df_features['last_tx_timestamp'] = pd.to_datetime('1900-01-01')
    unique_edges = set()

    # --- Pass 2: Aggregate features and build edge list ---
    print("--- Pass 2: Aggregating features and building edge list ---")
    
    for i, chunk in enumerate(pd.read_csv(log_csv_path, chunksize=chunksize, iterator=True)):
        
        # --- Time/Date Processing (Universal) ---
        if col_map['time_mode'] == 'Date_Time':
            chunk['timestamp'] = pd.to_datetime(chunk['Date'] + ' ' + chunk['Time'], errors='coerce')
        else: # 'booking_datetime'
            chunk['timestamp'] = pd.to_datetime(chunk['booking_datetime'], errors='coerce')
            
        chunk = chunk.dropna(subset=['timestamp'])
        chunk['hour_of_day'] = chunk['timestamp'].dt.hour
        chunk['is_night_tx'] = (chunk['hour_of_day'] >= 0) & (chunk['hour_of_day'] <= 5)
        chunk['is_small_tx'] = chunk[col_map['amount']] < small_tx_threshold
        
        # a) Build edge list
        src = chunk[col_map['sender_acct']].map(account_map)
        dst = chunk[col_map['receiver_acct']].map(account_map)
        valid_edges = pd.concat([src, dst], axis=1).dropna()
        for edge_tuple in valid_edges.itertuples(index=False, name=None):
            if edge_tuple[0] != edge_tuple[1]: unique_edges.add(edge_tuple)

        # b) Aggregate Amount/Count features
        sent_stats = chunk.groupby(col_map['sender_acct'])[col_map['amount']].agg(['sum', 'count'])
        df_features.loc[sent_stats.index, 'total_sent'] += sent_stats['sum']
        df_features.loc[sent_stats.index, 'num_sent_tx'] += sent_stats['count']
        received_stats = chunk.groupby(col_map['receiver_acct'])[col_map['amount']].agg(['sum', 'count'])
        df_features.loc[received_stats.index, 'total_received'] += received_stats['sum']
        df_features.loc[received_stats.index, 'num_received_tx'] += received_stats['count']

        # --- c) Aggregate V3 Universal Payment Features ---
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

        # --- d) Aggregate V3.1 Cross-Border Features ---
        chunk['is_cross_border'] = (chunk[col_map['sender_loc']] != chunk[col_map['receiver_loc']]).astype(int)
        
        sent_cross_border = chunk.groupby(col_map['sender_acct'])['is_cross_border'].sum()
        df_features.loc[sent_cross_border.index, 'num_cross_border_tx_sent'] += sent_cross_border
        
        received_cross_border = chunk.groupby(col_map['receiver_acct'])['is_cross_border'].sum()
        df_features.loc[received_cross_border.index, 'num_cross_border_tx_received'] += received_cross_border
        
        # e) Aggregate Time-Based Features (Night/Small)
        sent_night_tx = chunk[chunk['is_night_tx'] == True].groupby(col_map['sender_acct'])['is_night_tx'].count()
        df_features.loc[sent_night_tx.index, 'num_night_tx_sent'] += sent_night_tx
        received_night_tx = chunk[chunk['is_night_tx'] == True].groupby(col_map['receiver_acct'])['is_night_tx'].count()
        df_features.loc[received_night_tx.index, 'num_night_tx_received'] += received_night_tx
        sent_small_tx = chunk[chunk['is_small_tx'] == True].groupby(col_map['sender_acct'])['is_small_tx'].count()
        df_features.loc[sent_small_tx.index, 'num_small_tx_sent'] += sent_small_tx
        received_small_tx = chunk[chunk['is_small_tx'] == True].groupby(col_map['receiver_acct'])['is_small_tx'].count()
        df_features.loc[received_small_tx.index, 'num_small_tx_received'] += received_small_tx

        # f) Update min/max timestamps
        sender_first_tx = chunk.groupby(col_map['sender_acct'])['timestamp'].min()
        sender_last_tx = chunk.groupby(col_map['sender_acct'])['timestamp'].max()
        receiver_first_tx = chunk.groupby(col_map['receiver_acct'])['timestamp'].min()
        receiver_last_tx = chunk.groupby(col_map['receiver_acct'])['timestamp'].max()
        all_first = pd.concat([sender_first_tx, receiver_first_tx]).groupby(level=0).min()
        all_last = pd.concat([sender_last_tx, receiver_last_tx]).groupby(level=0).max()
        df_features.loc[all_first.index, 'first_tx_timestamp'] = pd.concat([df_features.loc[all_first.index, 'first_tx_timestamp'], all_first], axis=1).min(axis=1)
        df_features.loc[all_last.index, 'last_tx_timestamp'] = pd.concat([df_features.loc[all_last.index, 'last_tx_timestamp'], all_last], axis=1).max(axis=1)
        
        if (i + 1) % 5 == 0:
            print(f"  ...processed chunk {i+1} (Pass 2)")

    print("Pass 2 complete.")
    
    # --- Final Processing ---
    print("--- Finalizing features and graph ---")
    
    df_features['avg_sent'] = df_features['total_sent'] / (df_features['num_sent_tx'] + 1e-6)
    df_features['avg_received'] = df_features['total_received'] / (df_features['num_received_tx'] + 1e-6)
    
    account_lifespan_seconds = (df_features['last_tx_timestamp'] - df_features['first_tx_timestamp']).dt.total_seconds()
    account_lifespan_seconds = account_lifespan_seconds.replace(0, 86400.0) 
    df_features['account_age_days'] = account_lifespan_seconds / 86400.0
    total_tx = df_features['num_sent_tx'] + df_features['num_received_tx']
    df_features['tx_frequency_per_day'] = total_tx / (df_features['account_age_days'] + 1e-6)
    
    final_feature_columns = base_features + ['avg_sent', 'avg_received'] + \
                            ['account_age_days', 'tx_frequency_per_day'] + payment_features
    df_features = df_features.reindex(columns=final_feature_columns).fillna(0.0)
    df_features = df_features.loc[sorted_accounts]

    # --- SCALER FIX ---
    # Load/save the scaler to prevent data leakage
    if scaler_path and os.path.exists(scaler_path):
        print(f"Loading existing scaler from {scaler_path}...")
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        x_features = scaler.transform(df_features.values)
    else:
        print("Fitting new scaler...")
        scaler = StandardScaler()
        x_features = scaler.fit_transform(df_features.values)
        if scaler_path:
            with open(scaler_path, 'wb') as f:
                pickle.dump(scaler, f)
            print(f"Saved new scaler to {scaler_path}")
    
    x = torch.tensor(x_features, dtype=torch.float)
    
    print(f"Feature engineering V3.1 complete. Created feature matrix (x) with shape: {x.shape}")
    print(f"  Universal features: {UNIVERSAL_FEATURES}")
    print(f"  Cross-border features: ['num_cross_border_tx_sent', 'num_cross_border_tx_received']")

    if not unique_edges:
        print("Warning: No valid edges found."); edge_index = torch.empty((2, 0), dtype=torch.long)
    else:
        edge_array = np.array(list(unique_edges), dtype=np.int64).T
        edge_index = torch.tensor(edge_array, dtype=torch.long)
    
    data = Data(x=x, edge_index=edge_index, y=y)
    data.num_classes = 2
    
    print("\nData object V3.1 created successfully:")
    print(data)
    
    print(f"\nTotal processing time: {(time.time() - start_time):.2f} seconds")
    
    # --- Save the account map ---
    # This is critical for mapping predictions back
    map_filename = 'account_map_V3.pkl'
    if scaler_path is None: # Only save the map from the training data
        with open(map_filename, 'wb') as f:
            pickle.dump(account_map, f)
        print(f"Saved account map to '{map_filename}'")
    
    return data, df_features.columns.tolist()

if __name__ == "__main__":
    
    # --- Configuration ---
    OUR_DATA_FILE = 'dataset/AML_dataset.csv'
    HACKATHON_DATA_FILE = 'dataset/hackathon_sample_CLEANED.csv'
    
    # --- FIX: Define file paths for reusable components ---
    TRAIN_GRAPH_FILE = 'train_graph_V3.pt'
    HACKATHON_GRAPH_FILE = 'hackathon_graph_V3.pt'
    SCALER_FILE = 'scaler_V3.pkl' # <-- This is the key
    
    # --- 1. Process Our Large Training Data ---
    print("--- Processing Our Large Training Data ---")
    our_data, feature_names = create_graph_from_log_v3(
        OUR_DATA_FILE, 
        scaler_path=SCALER_FILE # Pass path to SAVE the new scaler
    )
    torch.save(our_data, TRAIN_GRAPH_FILE)
    print(f"Saved our training graph to '{TRAIN_GRAPH_FILE}'")
    print("\nEngineered Feature List (V3.1):")
    for i, name in enumerate(feature_names):
        print(f"  Feature {i}: {name}")
        
    # --- 2. Process Their Small Sample Data (for validation) ---
    print("\n--- Processing Hackathon Sample Data ---")
        
    hackathon_data, _ = create_graph_from_log_v3(
        HACKATHON_DATA_FILE,
        scaler_path=SCALER_FILE # Pass path to LOAD the existing scaler
    )
    torch.save(hackathon_data, HACKATHON_GRAPH_FILE)
    print(f"Saved hackathon graph to '{HACKATHON_GRAPH_FILE}'")

    print("\n--- V3.1 Data Processing Complete ---")
    print("You are now ready to run 'create_subgraphs.py' and 'train_inductive_model.py'")