import torch
import torch.nn.functional as F
from torch.nn import Module, Linear
import numpy as np
import pandas as pd
import pickle
from sklearn.metrics import precision_recall_fscore_support, accuracy_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import time
import os

# We need both models in this file
from torch_geometric.nn import GCNConv, GATConv 

# --- 1A. GCN Model Definition ---
class GCN_AML(Module):
    def __init__(self, num_node_features, hidden_dim, num_classes, dropout=0.5):
        super(GCN_AML, self).__init__()
        self.dropout_p = dropout
        self.conv1 = GCNConv(num_node_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, num_classes)

    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout_p, training=self.training)
        x = self.conv2(x, edge_index)
        return x

# --- 1B. GAT Model Definition ---
class GAT_AML(Module):
    def __init__(self, num_node_features, hidden_dim, num_classes, heads=8, dropout=0.6):
        super(GAT_AML, self).__init__()
        self.dropout_p = dropout
        self.conv1 = GATConv(num_node_features, hidden_dim, heads=heads, dropout=dropout)
        self.conv2 = GATConv(hidden_dim * heads, num_classes, heads=1, concat=False, dropout=dropout)

    def forward(self, x, edge_index):
        x = F.dropout(x, p=self.dropout_p, training=self.training)
        x = self.conv1(x, edge_index)
        x = F.elu(x) 
        x = F.dropout(x, p=self.dropout_p, training=self.training)
        x = self.conv2(x, edge_index)
        return x

# --- 2. Training & Evaluation Logic --- (Identical to before)
def train(model, data, optimizer, criterion):
    model.train()
    optimizer.zero_grad()
    out = model(data.x, data.edge_index)
    loss = criterion(out[data.train_mask], data.y[data.train_mask])
    loss.backward()
    optimizer.step()
    return loss.item()

@torch.no_grad()
def evaluate(model, data):
    model.eval()
    out = model(data.x, data.edge_index)
    pred = out.argmax(dim=1)
    results = {}
    for mask_name, mask in [('train', data.train_mask), ('val', data.val_mask), ('test', data.test_mask)]:
        y_true = data.y[mask].cpu().numpy(); y_pred = pred[mask].cpu().numpy()
        if len(y_true) == 0: continue
        acc = accuracy_score(y_true, y_pred)
        p, r, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, pos_label=1, average='binary', zero_division=0
        )
        results[mask_name] = {'acc': acc, 'precision': p, 'recall': r, 'f1': f1}
    return results

# --- 3. CSV Logging ---
def log_results(config, val_results, test_results, total_time, best_epoch):
    log_file = 'master_tuning_log.csv' 
    
    config.setdefault('GAT_HEADS', None)
    config.setdefault('DROPOUT', 0.5) # Default dropout for GCN
        
    log_data = {
        'run_name': config['RUN_NAME'],
        'model_type': config['MODEL_TYPE'],
        'data_file': config['DATA_FILE'],
        'val_f1': val_results['f1'],
        'test_f1': test_results['f1'],
        'test_precision': test_results['precision'],
        'test_recall': test_results['recall'],
        'best_epoch': best_epoch,
        'total_time_sec': total_time,
        'lr': config['LEARNING_RATE'],
        'hidden_dim': config['HIDDEN_DIM'],
        'pos_weight_mult': config['POS_WEIGHT_MULTIPLIER'],
        'gat_heads': config['GAT_HEADS'],
        'dropout': config['DROPOUT']
    }
    df_log = pd.DataFrame([log_data])
    if not os.path.exists(log_file):
        df_log.to_csv(log_file, index=False, header=True)
    else:
        df_log.to_csv(log_file, index=False, header=False, mode='a')
    print(f"Results logged to '{log_file}'")

def print_summary():
    log_file = 'master_tuning_log.csv'
    if not os.path.exists(log_file):
        print("\nNo 'master_tuning_log.csv' file found to summarize.")
        return
    print("\n--- Master Tuning Log Summary ---")
    df = pd.read_csv(log_file)
    df_sorted = df.sort_values(by='val_f1', ascending=False)
    cols_to_show = [
        'run_name', 'model_type', 'data_file', 'val_f1', 'test_f1', 
        'test_precision', 'test_recall', 'best_epoch', 'lr', 'hidden_dim', 'pos_weight_mult', 'gat_heads'
    ]
    cols_to_show = [col for col in cols_to_show if col in df_sorted.columns]
    print(df_sorted[cols_to_show].to_string(index=False))
    print("\n'val_f1' is the score we use to pick the best model.")
    print("--------------------------")

# --- 4. Main Execution ---
def run_experiment(config, data, device):
    start_run_time = time.time()
    print(f"\n--- Starting Experiment: {config['RUN_NAME']} ---")
    print(f"  Model: {config['MODEL_TYPE']}, Data: {config['DATA_FILE']}")
    print(f"  Config: {config}")

    # --- Select Model ---
    if config['MODEL_TYPE'] == 'GCN':
        model = GCN_AML(
            num_node_features=data.num_node_features,
            hidden_dim=config['HIDDEN_DIM'],
            num_classes=data.num_classes,
            dropout=config.get('DROPOUT', 0.5)
        ).to(device)
    elif config['MODEL_TYPE'] == 'GAT':
        model = GAT_AML(
            num_node_features=data.num_node_features,
            hidden_dim=config['HIDDEN_DIM'],
            num_classes=data.num_classes,
            heads=config['GAT_HEADS'],
            dropout=config.get('DROPOUT', 0.6)
        ).to(device)
    else:
        raise ValueError(f"Unknown model_type: {config['MODEL_TYPE']}")

    optimizer = torch.optim.Adam(model.parameters(), 
                                 lr=config['LEARNING_RATE'], 
                                 weight_decay=config.get('WEIGHT_DECAY', 5e-4))
    
    num_benign = (data.y[data.train_mask] == 0).sum().item()
    num_illicit = (data.y[data.train_mask] == 1).sum().item()
    base_weight_illicit = num_benign / num_illicit
    weight_illicit = base_weight_illicit * config['POS_WEIGHT_MULTIPLIER']
    class_weights = torch.tensor([1.0, weight_illicit], dtype=torch.float).to(device)
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights)
    print(f"  Final pos_weight: {weight_illicit:.2f}")

    best_val_f1 = 0.0
    best_epoch = 0
    model_save_path = f"best_model_{config['RUN_NAME']}.pth"
    
    for epoch in range(1, config['NUM_EPOCHS'] + 1):
        try:
            loss = train(model, data, optimizer, criterion)
        except torch.cuda.OutOfMemoryError:
            print(f"  Epoch {epoch:03d} | FATAL: CUDA Out of Memory. Skipping this run.")
            torch.cuda.empty_cache(); return
        
        if epoch % 10 == 0:
            eval_results = evaluate(model, data)
            val_f1 = eval_results['val']['f1']
            if val_f1 > best_val_f1 or epoch % 50 == 0:
                print(f"  Epoch {epoch:03d} | Loss: {loss:.4f} | "
                      f"Val F1: {val_f1:.4f} | "
                      f"Val Recall: {eval_results['val']['recall']:.4f} | "
                      f"Val Prc: {eval_results['val']['precision']:.4f}")
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_epoch = epoch
                torch.save(model.state_dict(), model_save_path)
                print(f"    ^ New best model saved (F1: {val_f1:.4f})")

    total_time = time.time() - start_run_time
    print(f"  Training finished in {total_time:.2f} seconds.")
    if best_val_f1 == 0.0:
        print("  Model did not improve. Logging empty results."); empty_res = {'f1': 0, 'precision': 0, 'recall': 0, 'acc': 0}
        log_results(config, empty_res, empty_res, total_time, 0)
        print(f"--- Finished Experiment: {config['RUN_NAME']} (FAILED) ---"); return

    print("  Loading best model and evaluating on Test Set...")
    model.load_state_dict(torch.load(model_save_path))
    final_results = evaluate(model, data); test_res, val_res = final_results['test'], final_results['val']
    print(f"  --- Test Set Results (Best Model, Epoch {best_epoch}) ---")
    print(f"    F1-Score:  {test_res['f1']:.4f}"); print(f"    Precision: {test_res['precision']:.4f}"); print(f"    Recall:    {test_res['recall']:.4f}")
    print("  ---------------------------------------")
    log_results(config, val_res, test_res, total_time, best_epoch)
    print(f"--- Finished Experiment: {config['RUN_NAME']} ---")


if __name__ == "__main__":
    
    # --- 1. SETUP ---
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Master script using device: {device}")

    print("Loading all datasets into memory...")
    try:
        # We only need the V2 data now, since we know it's better.
        data_v2 = torch.load('my_graph_data_v2.pt', weights_only=False).to(device)
    except FileNotFoundError as e:
        print(f"Error: Could not load data file. {e}")
        print("Please run 'build_graph_v2.py' first.")
        exit()
    
    datasets = {
        'v2': data_v2
    }
    print("All datasets loaded.")

    # --- 2. DEFINE OUR GRAND STRATEGY ---
    
    # This is our "New Champion" config from your last run
    gcn_champ_config = {
        "MODEL_TYPE": "GCN",
        "NUM_EPOCHS": 500,
        "LEARNING_RATE": 0.005,
        "HIDDEN_DIM": 128,
        "POS_WEIGHT_MULTIPLIER": 0.5,
        "DROPOUT": 0.5
    }
    
    # This is our "Stable GAT" config
    gat_stable_config = {
        "MODEL_TYPE": "GAT",
        "NUM_EPOCHS": 600,
        "LEARNING_RATE": 0.001,       # STABLE LR
        "HIDDEN_DIM": 64,
        "GAT_HEADS": 2,               # Memory-safe
        "POS_WEIGHT_MULTIPLIER": 0.5, # Our best "dragnet" setting
        "DROPOUT": 0.6
    }
    
    parameter_grid = [
        # Test 1: Re-run our new GCN Champion (to log it)
        {**gcn_champ_config,
         "RUN_NAME": "Final_GCN_on_V2_Data",
         "DATA_FILE": 'v2'
        },
        
        # Test 2: Stable GAT vs. V2 Data (The "F1 Engine" test)
        {**gat_stable_config,
         "RUN_NAME": "Final_GAT_Stable_on_V2_Data",
         "DATA_FILE": 'v2'
        },
    ]
    
    # --- 3. RUN ALL EXPERIMENTS ---
    for config in parameter_grid:
        current_data = datasets[config['DATA_FILE']]
        run_experiment(config, current_data, device)
        
    # --- 4. SHOW FINAL REPORT ---
    print_summary()

