from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import numpy as np

from SoraWatermarkCleaner.sorawm.cleaner.e2fgvi_hq_cleaner import E2FGVIHDCleaner
from SoraWatermarkCleaner.sorawm.cleaner.lama_cleaner import LamaCleaner
from SoraWatermarkCleaner.sorawm.schemas import CleanerType


class WaterMarkCleaner:
    def __new__(cls, cleaner_type: CleanerType):
        """
        Create and return an instance of the specified cleaner implementation.
        
        Parameters:
            cleaner_type (CleanerType): The cleaner implementation to create.
        
        Returns:
            An instance of the corresponding cleaner class (for example, `LamaCleaner` or `E2FGVIHDCleaner`).
        
        Raises:
            ValueError: If `cleaner_type` is not a recognized CleanerType.
        """
        match cleaner_type:
            case CleanerType.LAMA:
                return LamaCleaner()
            case CleanerType.E2FGVI_HQ:
                return E2FGVIHDCleaner()
            case _:
                raise ValueError(f"Invalid cleaner type: {cleaner_type}")