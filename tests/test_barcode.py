import cv2
import numpy as np
import pytest

from app import barcode

L = ["0001101", "0011001", "0010011", "0111101", "0100011", "0110001", "0101111", "0111011", "0110111", "0001011"]
G = ["0100111", "0110011", "0011011", "0100001", "0011101", "0111001", "0000101", "0010001", "0001001", "0010111"]
R = ["1110010", "1100110", "1101100", "1000010", "1011100", "1001110", "1010000", "1000100", "1001000", "1110100"]
PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG", "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]


def ean13_image(code: str) -> bytes:
    d = [int(c) for c in code]
    bits = "101" + "".join((L if p == "L" else G)[x] for p, x in zip(PARITY[d[0]], d[1:7]))
    bits += "01010" + "".join(R[x] for x in d[7:]) + "101"
    row = np.repeat(np.array([0 if b == "1" else 255 for b in bits], np.uint8), 3)
    img = np.tile(row, (120, 1))
    img = cv2.copyMakeBorder(img, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)
    img = cv2.GaussianBlur(img, (3, 3), 0)  # come una foto reale
    return cv2.imencode(".png", img)[1].tobytes()


def test_valid_ean():
    assert barcode.valid_ean("8076800195057")
    assert not barcode.valid_ean("8076800195058")
    assert not barcode.valid_ean("abc")


def test_decode_synthetic_ean13():
    assert barcode.decode(ean13_image("8076800195057")) == "8076800195057"


def test_decode_no_barcode():
    assert barcode.decode(cv2.imencode(".png", np.full((100, 100), 255, np.uint8))[1].tobytes()) is None


@pytest.mark.parametrize("tags,cat", [
    (["en:dairies", "en:milks"], "latticini"),
    (["it:formaggi-stagionati"], "formaggio_stagionato"),
    (["en:unknown"], None),
])
def test_map_category(tags, cat):
    assert barcode.map_category(tags) == cat
