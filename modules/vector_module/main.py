# main.py
from typing import Optional, List

from fastapi import FastAPI
from vector_module.quantum_vector_manager import QuantumVectorManager
from vector_module.transaction_protocol import TransactionProtocol
from vector_module.transaction_matrix import TransactionMatrix

app = FastAPI()

# Initialize QuantumVectorManager and TransactionProtocol
vector_manager = QuantumVectorManager()
transaction_matrix = TransactionMatrix(["Time"], ["Create", "Update"])
transaction_protocol = TransactionProtocol(vector_manager, transaction_matrix)

# API Endpoints
@app.post("/create_vector/")
def create_vector(vector_id: str, coordinates: List[float]):
    vector = vector_manager.create_vector(vector_id, coordinates)
    return {"vector_id": vector_id, "layers": vector.get_all_layers()}

@app.put("/update_vector/")
def update_vector(vector_id: str, new_coordinates: List[float], new_state: dict):
    success = vector_manager.update_vector(vector_id, new_coordinates, new_state)
    return {"success": success}

@app.post("/create_transaction/")
def create_transaction(tx_type: str, sender: str, vector_data: Optional[List[float]] = None):
    transaction = transaction_protocol.create_transaction(tx_type, sender, vector_data=vector_data)
    return {"tx_id": transaction["tx_id"], "tx_type": transaction["tx_type"]}

@app.post("/process_transactions/")
def process_transactions():
    transaction_protocol.process_transactions()
    return {"message": "Transactions processed"}
