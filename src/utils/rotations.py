"""
Rotation utilities for 3D transformations.
"""

import numpy as np
from typing import Tuple


class RotationUtils:
    """Rotation matrix and transformation utilities."""

    @staticmethod
    def rotation_matrix_x(angle: float) -> np.ndarray:
        """Rotation matrix about X-axis (roll)."""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [1, 0, 0],
            [0, c, -s],
            [0, s, c]
        ])

    @staticmethod
    def rotation_matrix_y(angle: float) -> np.ndarray:
        """Rotation matrix about Y-axis (pitch)."""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [c, 0, s],
            [0, 1, 0],
            [-s, 0, c]
        ])

    @staticmethod
    def rotation_matrix_z(angle: float) -> np.ndarray:
        """Rotation matrix about Z-axis (yaw)."""
        c, s = np.cos(angle), np.sin(angle)
        return np.array([
            [c, -s, 0],
            [s, c, 0],
            [0, 0, 1]
        ])

    @staticmethod
    def euler_to_dcm(phi: float, theta: float, psi: float) -> np.ndarray:
        """
        Convert Euler angles to Direction Cosine Matrix (DCM).
        Uses ZYX (yaw-pitch-roll) convention (aerospace standard).

        Args:
            phi: Roll angle (radians)
            theta: Pitch angle (radians)
            psi: Yaw/heading angle (radians)

        Returns:
            3x3 DCM for body-to-inertial transformation
        """
        Rz = RotationUtils.rotation_matrix_z(psi)
        Ry = RotationUtils.rotation_matrix_y(theta)
        Rx = RotationUtils.rotation_matrix_x(phi)
        return Rz @ Ry @ Rx

    @staticmethod
    def transform_body_to_ned(
        body_vector: np.ndarray,
        phi: float,
        theta: float,
        psi: float
    ) -> np.ndarray:
        """Transform a vector from body frame to NED frame."""
        dcm = RotationUtils.euler_to_dcm(phi, theta, psi)
        return dcm @ body_vector

    @staticmethod
    def transform_ned_to_body(
        ned_vector: np.ndarray,
        phi: float,
        theta: float,
        psi: float
    ) -> np.ndarray:
        """Transform a vector from NED frame to body frame."""
        dcm = RotationUtils.euler_to_dcm(phi, theta, psi)
        return dcm.T @ ned_vector

    @staticmethod
    def create_aircraft_vertices(
        wingspan: float = 10.0,
        fuselage_length: float = 8.0,
        tail_span: float = 3.0
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create simple aircraft geometry vertices in body frame.

        Returns:
            vertices: (N, 3) array of vertex positions
            faces: List of vertex indices for each face
        """
        # Simplified aircraft geometry (nose pointing +X in body frame)
        w = wingspan / 2
        fl = fuselage_length
        ts = tail_span / 2

        vertices = np.array([
            # Fuselage (elongated diamond)
            [fl * 0.6, 0, 0],       # 0: Nose
            [-fl * 0.4, 0, 0],      # 1: Tail
            [0, 0, fl * 0.05],      # 2: Fuselage bottom
            [0, 0, -fl * 0.03],     # 3: Fuselage top

            # Main wing
            [0, w, 0],              # 4: Right wing tip
            [0, -w, 0],             # 5: Left wing tip
            [-fl * 0.1, w * 0.3, 0],   # 6: Right wing trailing
            [-fl * 0.1, -w * 0.3, 0],  # 7: Left wing trailing

            # Horizontal tail
            [-fl * 0.35, ts, 0],    # 8: Right tail tip
            [-fl * 0.35, -ts, 0],   # 9: Left tail tip

            # Vertical tail
            [-fl * 0.35, 0, -fl * 0.12],  # 10: Tail top
        ])

        # Define faces (triangles) by vertex indices
        faces = [
            # Fuselage sides
            [0, 2, 4], [0, 4, 3],
            [0, 5, 2], [0, 3, 5],
            [1, 4, 2], [1, 3, 4],
            [1, 2, 5], [1, 5, 3],

            # Main wing (simplified)
            [4, 6, 5], [5, 6, 7],

            # Horizontal tail
            [1, 8, 9],

            # Vertical tail
            [1, 10, 3],
        ]

        return vertices, faces

    @staticmethod
    def transform_aircraft_geometry(
        vertices: np.ndarray,
        position: np.ndarray,
        phi: float,
        theta: float,
        psi: float,
        scale: float = 1.0
    ) -> np.ndarray:
        """
        Transform aircraft vertices to world coordinates.

        Args:
            vertices: (N, 3) body-frame vertices
            position: (3,) position in NED frame [N, E, D]
            phi, theta, psi: Euler angles (radians)
            scale: Scaling factor for aircraft size

        Returns:
            (N, 3) vertices in NED frame
        """
        dcm = RotationUtils.euler_to_dcm(phi, theta, psi)
        transformed = (dcm @ (vertices.T * scale)).T
        transformed += position
        return transformed
