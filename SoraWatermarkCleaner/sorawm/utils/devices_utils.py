from functools import lru_cache
import os

import torch
from loguru import logger


@lru_cache()
def get_device():
    # Force CPU on Cloud Run or when explicitly requested
    force_cpu = os.getenv('FORCE_CPU', '').lower() in ('1', 'true', 'yes')
    is_cloud_run = os.getenv('K_SERVICE') is not None or os.getenv('GAE_ENV') is not None
    
    if force_cpu or is_cloud_run:
        logger.info("Forcing CPU device (Cloud Run environment detected)")
        return torch.device("cpu")
    
    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
    if torch.backends.mps.is_available():
        device = "mps"
    logger.debug(f"Using device: {device}")
    return torch.device(device)
