"""Flower adapter stub — optional, no hard dependency (Phase 2 roadmap).

The current trainer is an in-process FedAvg simulation. When independent
clients are in scope, adopt Flower (ClientApp/ServerApp) with node identity
and TLS instead of extending this stub. This module only exposes the seam:
converting validated ndarrays to/from Flower Parameters when `flwr` is
installed, and raising an actionable error otherwise.
"""

try:
    from flwr.common import Parameters, ndarrays_to_parameters, parameters_to_ndarrays
    _HAS_FLOWER = True
except Exception:  # flwr is optional; simulation must work without it
    Parameters = None  # type: ignore
    _HAS_FLOWER = False

    def ndarrays_to_parameters(ndarrays):  # type: ignore
        raise ImportError("flwr is not installed. Install flwr to use the Flower adapter.")

    def parameters_to_ndarrays(params):  # type: ignore
        raise ImportError("flwr is not installed. Install flwr to use the Flower adapter.")


def has_flower():
    return _HAS_FLOWER


def to_parameters(client_weights):
    """Wrap validated FedAvg weights for transport. Validates via weighted_fed_average rules first."""
    import numpy as np
    from src.federated import weighted_fed_average
    sizes = [1] * len(client_weights)
    # Reuse validation (shapes/finite) by averaging a single replica set.
    weighted_fed_average([client_weights], [1])
    return ndarrays_to_parameters([np.asarray(w) for w in client_weights])


def from_parameters(params):
    return parameters_to_ndarrays(params)
