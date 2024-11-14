from scipy.linalg import logm, eigvals
import numpy as np
from .entanglement_interface import EntanglementInterface


class EntanglementEntropy(EntanglementInterface):
    def regularized_density_matrix(self, density_matrix: np.ndarray, epsilon: float = 1e-5,
                                   threshold: float = 1e-9) -> np.ndarray:
        """
        Regularize the density matrix to avoid singular or near-singular values by eigenvalue thresholding.

        Parameters:
            density_matrix (np.ndarray): The original density matrix.
            epsilon (float): Initial small positive value for regularization.
            threshold (float): Minimum eigenvalue threshold for stability.

        Returns:
            np.ndarray: The regularized density matrix.
        """
        # Initial regularization with epsilon
        regularized_matrix = density_matrix + np.eye(density_matrix.shape[0]) * epsilon

        # Eigenvalue thresholding and adjustment
        eigenvalues, eigenvectors = np.linalg.eigh(regularized_matrix)
        min_eigenvalue = np.min(np.abs(eigenvalues))

        # Increase epsilon dynamically if min eigenvalue is below threshold
        if min_eigenvalue < threshold:
            scaling_factor = threshold / min_eigenvalue
            regularized_matrix += np.eye(density_matrix.shape[0]) * (epsilon * scaling_factor)

        # Apply a minimum threshold to eigenvalues directly
        eigenvalues = np.where(eigenvalues < threshold, threshold, eigenvalues)
        regularized_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T

        # Clamp to avoid extreme values after regularization
        regularized_matrix = np.clip(regularized_matrix, -1e10, 1e10)

        # Replace any remaining NaNs or Infs
        regularized_matrix = np.nan_to_num(regularized_matrix, nan=epsilon, posinf=epsilon, neginf=epsilon)

        return regularized_matrix

    def calculate_entropy(self, density_matrix):
        regularized_matrix = self.regularized_density_matrix(density_matrix, epsilon=1e-5)  # Increased epsilon
        eigenvalues = np.clip(np.real(np.linalg.eigvals(regularized_matrix)), 1e-10, None)
        entropy = -np.sum(eigenvalues * np.log(eigenvalues))
        return entropy
