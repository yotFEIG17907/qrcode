"""
These commands report barcodes
"""
from dataclasses import dataclass


@dataclass
class BarcodeReport(object):
    # Report the barcode as a string
    payload: str
