from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Statevector, DensityMatrix
from qiskit.circuit import QuantumRegister, ClassicalRegister
from datetime import datetime
import numpy as np
import json
import logging
from joblib import Parallel, delayed

# Configure logging to file
logging.basicConfig(filename="simulation_log.json", level=logging.INFO, format="%(message)s")


# Custom function to convert numpy types to native Python types for JSON serialization
def convert_numpy(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


# Validation calculation function without Numba
def calculate_validation_metrics(dm_data):
    trace_check = np.isclose(np.trace(dm_data), 1.0)
    eigenvalues = np.linalg.eigvalsh(dm_data)
    eigenvalue_range = np.all((eigenvalues >= 0) & (eigenvalues <= 1))
    purity = np.real(np.trace(dm_data @ dm_data))
    entropy = -np.sum(eigenvalues * np.log2(eigenvalues + 1e-10))  # Stability with epsilon
    sparsity_ratio = 1.0 - np.count_nonzero(dm_data) / dm_data.size
    return trace_check, eigenvalue_range, purity, entropy, sparsity_ratio


# Automated validation function (parallelized with joblib)
def validate_layer(dm, layer):
    trace_check, eigenvalue_range, purity, entropy, sparsity_ratio = calculate_validation_metrics(dm.data)
    result = {
        "layer": layer + 1,
        "num_qubits": int(np.log2(dm.data.shape[0])),
        "trace_check": trace_check,
        "eigenvalue_range": "Pass" if eigenvalue_range else "Fail",
        "purity": purity,
        "entropy": entropy,
        "sparsity_ratio": sparsity_ratio
    }
    return result


def automated_validation_parallel(density_matrices):
    # Use joblib to parallelize validation across density matrix layers
    validation_results = Parallel(n_jobs=-1)(delayed(validate_layer)(dm, i) for i, dm in enumerate(density_matrices))
    # Log results to file
    with open("quantum_validation_logs.json", "a") as f:
        for result in validation_results:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                **result
            }
            json.dump(log_entry, f, default=convert_numpy)
            f.write("\n")
    return validation_results


# Quantum Circuit Setup
num_transactions = 4
num_vector_layers = 4

# Initialize Registers and Quantum Circuit
transaction_regs = [QuantumRegister(num_transactions, f'tx_{i}') for i in range(num_vector_layers)]
classical_regs = [ClassicalRegister(num_transactions, f'cr_{i}') for i in range(num_vector_layers)]
measured_qc = QuantumCircuit(*transaction_regs, *classical_regs)

# Apply Hadamard and CNOT gates for entanglement
for i in range(num_vector_layers):
    measured_qc.h(transaction_regs[i][0])
    for j in range(1, num_transactions):
        measured_qc.cx(transaction_regs[i][0], transaction_regs[i][j])

# Entangle layers
for i in range(num_vector_layers - 1):
    measured_qc.cx(transaction_regs[i][-1], transaction_regs[i + 1][0])

# Add Measurements
for i in range(num_vector_layers):
    measured_qc.measure(transaction_regs[i], classical_regs[i])

# Compile and Run the Circuit
simulator = AerSimulator()
compiled_circuit = transpile(measured_qc, simulator)
result = simulator.run(compiled_circuit, shots=1024).result()

# Retrieve Measurement Counts with Error Handling
try:
    counts = result.get_counts()
    print("Measurement Counts:", counts)
except Exception as e:
    print(f"Error retrieving counts: {e}")
    counts = {}

# Process each layer individually to avoid large density matrix issues
density_matrices = []
for i in range(num_vector_layers):
    single_layer_qc = QuantumCircuit(transaction_regs[i])
    single_layer_qc.h(transaction_regs[i][0])
    for j in range(1, num_transactions):
        single_layer_qc.cx(transaction_regs[i][0], transaction_regs[i][j])

    # Create the density matrix for this layer
    state = Statevector(single_layer_qc)
    density_matrices.append(DensityMatrix(state))

# Run automated validation on individual layer density matrices using joblib for parallel processing
validation_results = automated_validation_parallel(density_matrices)

# Save validation results to a JSON file
with open("validation_results.json", "w") as file:
    json.dump(validation_results, file, indent=4, default=convert_numpy)

print("Validation complete. Results saved to 'validation_results.json'.")
