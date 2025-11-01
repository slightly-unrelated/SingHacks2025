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

# --- 1. Inductive GNN Model Definition ---
class InductiveGNN(Module):
    """
    This is a Graph-level classifier (a "Profiler").
    It classifies an entire subgraph as illicit or benign.
    """
    def __init__(self, num_node_features, hidden_dim, dropout=0.5):
        super(InductiveGNN, self).__init__()
        self.dropout_p = dropout
        
        self.conv1 = SAGEConv(num_node_features, hidden_dim)
        self.conv2 = SAGEConv(hidden_dim, hidden_dim)
        self.conv3 = SAGEConv(hidden_dim, hidden_dim)
        
        # After pooling, we have a classifier
        self.lin1 = Linear(hidden_dim, hidden_dim // 2)
        self.lin2 = Linear(hidden_dim // 2, 2) # 2 output classes

    def forward(self, x, edge_index, batch):
        # 1. Run GNN layers on all nodes
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = self.conv3(x, edge_index)
        x = F.relu(x)

        # 2. "Summarize" all nodes in each graph into one vector
        # The 'batch' tensor tells the pooler which nodes belong to which graph
        x_pooled = global_mean_pool(x, batch)

        # 3. Run the final classifier
        x = F.dropout(x_pooled, p=self.dropout_p, training=self.training)
        x = self.lin1(x)
        x = F.relu(x)
        x = self.lin2(x)
        
        return x

# --- 2. Training & Evaluation Logic ---
# These are different now, as they operate on a 'loader'

def train(model, loader, optimizer, criterion, device):
    model.train()
    total_loss = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        # The model now takes 'batch.batch'
        out = model(batch.x, batch.edge_index, batch.batch)
        loss = criterion(out, batch.y)
        
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
        
    return total_loss / len(loader.dataset)

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
    
    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, pos_label=1, average='binary', zero_division=0
    )
    
    print("\n--- Evaluation Results ---")
    print(f"  Accuracy:  {acc:.4f}")
    print(f"  Precision: {p:.4f}")
    print(f"  Recall:    {r:.4f}")
    print(f"  F1-Score:  {f1:.4f}")
    
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    print("  Confusion Matrix:")
    print(f"    TN: {cm[0][0]}  |  FP: {cm[0][1]}")
    print(f"    FN: {cm[1][0]}  |  TP: {cm[1][1]}")
    print("--------------------------")
    
    return f1

# --- 3. Main Execution ---
if __name__ == "__main__":
    
    # --- Config ---
    LEARNING_RATE = 0.001 # Start with a stable LR
    NUM_EPOCHS = 100
    BATCH_SIZE = 64
    HIDDEN_DIM = 128
    
    # --- Setup ---
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"--- Inductive GNN Trainer ---")
    print(f"Using device: {device}")

    # 1. Load Pre-processed Subgraph Datasets
    print("Loading subgraph datasets...")
    try:
        train_data_list = torch.load('inductive_train_dataset_V3.pt')
        test_data_list = torch.load('inductive_test_dataset_V3.pt')
    except FileNotFoundError:
        print("Error: Dataset files not found.")
        print("Please run 'create_subgraphs.py' first.")
        exit()
        
    # --- Create DataLoaders ---
    # This automatically batches the small graphs
    train_loader = DataLoader(train_data_list, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_data_list, batch_size=BATCH_SIZE, shuffle=False)
    
    print(f"Loaded {len(train_data_list)} training graphs and {len(test_data_list)} test graphs.")

    # 2. Initialize Model
    # We get num_node_features from the first graph in the dataset
    num_features = train_data_list[0].num_node_features
    
    model = InductiveGNN(
        num_node_features=num_features,
        hidden_dim=HIDDEN_DIM
    ).to(device)

    # 3. Setup Optimizer and Weighted Loss
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Calculate class weights from the *training dataset*
    num_benign = sum(1 for data in train_data_list if data.y == 0)
    num_illicit = sum(1 for data in train_data_list if data.y == 1)
    weight_illicit = num_benign / num_illicit
    class_weights = torch.tensor([1.0, weight_illicit], dtype=torch.float).to(device)
    
    print(f"Training set: {num_illicit} illicit, {num_benign} benign")
    print(f"Assigning pos_weight={weight_illicit:.2f} to illicit class in loss.")
    
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights)

    # --- Training Loop ---
    print("\nStarting Inductive GNN training...")
    best_test_f1 = 0.0
    
    for epoch in range(1, NUM_EPOCHS + 1):
        start_epoch_time = time.time()
        
        loss = train(model, train_loader, optimizer, criterion, device)
        
        epoch_time = time.time() - start_epoch_time
        print(f"Epoch {epoch:03d} | Train Loss: {loss:.4f} | Time: {epoch_time:.2f}s")

        # Evaluate on test set every 5 epochs
        if epoch % 5 == 0:
            print(f"--- Evaluating on Test Set (Epoch {epoch}) ---")
            test_f1 = evaluate(model, test_loader, device)
            
            if test_f1 > best_test_f1:
                best_test_f1 = test_f1
                # Save the "champion profiler"
                torch.save(model.state_dict(), 'inductive_model_champion_V3.pth')
                print(f"  ^ New best model saved (F1: {test_f1:.4f})")

    print("\n--- Training Finished ---")
    print(f"Best Test F1-Score: {best_test_f1:.4f}")
    print("Champion model saved to 'inductive_model_champion_V3.pth'")
 