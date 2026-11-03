from pytest import approx
import pytest
import math
from hypotenuse_calculator import (
    validate,
    triangle_points,
    distance,
    midpoint,
    vertex_angle,
    hypotenuse
)


def test_validate():
    assert validate(15, 0, 30, "X") == True
    assert validate(7.5, 0, 15, "Y") == True
    assert validate(0, 0, 30, "X") == True
    assert validate(30, 0, 30, "X") == True
    assert validate(-1, 0, 30, "X") == False
    assert validate(31, 0, 30, "X") == False


def test_triangle_points():
    points = triangle_points(10, 5)

    assert 'A' in points
    assert 'B' in points
    assert 'C' in points
    
    assert points['A'] == (10, 5)
    assert points['B'] == (8.42, 0)
    assert points['C'] == (11.58, 0)


def test_distance():
    assert distance((5, 5), (5, 5)) == 0
    assert distance((0, 0), (3, 0)) == 3
    assert distance((0, 0), (0, 4)) == 4
    assert distance((0, 0), (3, 4)) == 5
    assert distance((0, 0), (5, 12)) == 13
    assert distance((-3, -4), (0, 0)) == 5


def test_midpoint():
    assert midpoint((0, 0), (2, 2)) == (1, 1)
    assert midpoint((0, 5), (10, 5)) == (5, 5)
    assert midpoint((5, 0), (5, 10)) == (5, 5)
    
    # Test base points midpoint
    mid = midpoint((8.42, 0), (11.58, 0))
    assert mid[0] == approx(10, abs=0.01)
    assert mid[1] == 0
    assert midpoint((-2, -2), (2, 2)) == (0, 0)


def test_vertex_angle():
    angle = vertex_angle((0, 0), (3, 0), (0, 4))
    assert angle == approx(90, abs=1)
    
    vertex = (1, math.sqrt(3))
    angle = vertex_angle(vertex, (0, 0), (2, 0))
    assert angle == approx(60, abs=1)
    
    angle = vertex_angle((10, 5), (8.42, 0), (11.58, 0))
    assert 0 < angle < 180
    
    angle = vertex_angle((15, 12), (8.42, 0), (11.58, 0))
    assert 0 < angle < 180


def test_hypotenuse():
    result = hypotenuse(15, 10)
    
    assert len(result) == 4
    median, points, midpoint, angle = result
    
    assert median > 0
    
    assert points['A'] == (15, 10)
    assert points['B'] == (8.42, 0)
    assert points['C'] == (11.58, 0)
    
    assert midpoint[1] == 0
    assert midpoint[0] == approx(10, abs=0.01)
    
    assert 0 < angle < 180
    
    result_min = hypotenuse(0, 0)
    assert result_min[0] > 0
    
    result_max = hypotenuse(30, 15)
    assert result_max[0] > 0


pytest.main(["-v", "--tb=line", "-rN", __file__])