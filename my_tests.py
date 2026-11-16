import numpy as np
import fastlab

def test_sum_ok():
    assert fastlab.sum_two_args(2, 2) == 4

def test_sum_float():
    assert fastlab.sum_two_args(2.0001, 2) == 4.0001

def test_chessboard_even_cells_white():
    arr = np.zeros((40, 40, 3), dtype=np.uint8)
    out = fastlab.chessboard(arr, cell_percent=25)
    assert out[0, 0, 0] == 0
    assert out[0, 15, 0] == 255

def test_chessboard_shape_preserved():
    arr = np.zeros((30, 30, 3), dtype=np.uint8)
    out = fastlab.chessboard(arr, cell_percent=10)
    assert out.shape == arr.shape