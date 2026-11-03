import matplotlib.pyplot as plt
import math

def validate(value, min_val, max_val, var_name):
    if min_val <= value <= max_val:
        print(f"{var_name} = {value} is a great number")
        return True
    else:
        print(f"{var_name} = {value} is invalid (pick a number between {min_val}-{max_val})")
        return False


def input():
    print("\n" + "="*60)
    print("HYPOTENUSE CALCULATOR - User Input ")
    print("="*60)
    
    while True:
        try:
            x = float(input("Enter X coordinate (0-30): "))
            if not validate(x, 0, 30, "X"):
                continue
            
            y = float(input("Enter Y coordinate (0-15): "))
            if not validate(y, 0, 15, "Y"):
                continue
            
            return x, y
        except ValueError:
            print("Numbers are better than letters right now.\n")


def triangle_points(x, y):
    point_a = (x, y) 
    point_b = (8.42, 0) 
    point_c = (11.58, 0) 
    
    return {
        'A': point_a,
        'B': point_b,
        'C': point_c
    }


def distance(point1, point2, label=""):
    x1, y1 = point1
    x2, y2 = point2
    
    dx = x2 - x1
    dy = y2 - y1
    
    dx_squared = dx ** 2
    dy_squared = dy ** 2
    
    sum_squares = dx_squared + dy_squared
    distance = math.sqrt(sum_squares)
    
    return distance


def midpoint(point1, point2):
    x1, y1 = point1
    x2, y2 = point2
    
    midpoint_x = (x1 + x2) / 2
    midpoint_y = (y1 + y2) / 2
    
    return (midpoint_x, midpoint_y)


def vertex_angle(point_vertex, point_b, point_c):
    x_b, y_b = point_b
    x_c, y_c = point_c
    x_v, y_v = point_vertex
    
    side_a = math.sqrt((x_c - x_b)**2 + (y_c - y_b)**2)
    side_b = math.sqrt((x_v - x_c)**2 + (y_v - y_c)**2)
    side_c = math.sqrt((x_v - x_b)**2 + (y_v - y_b)**2)
    
    numerator = side_b**2 + side_c**2 - side_a**2
    denominator = 2 * side_b * side_c
    
    cos_angle = numerator / denominator
    
    angle_radians = math.acos(cos_angle)
    angle_degrees = math.degrees(angle_radians)
    
    return angle_degrees


def hypotenuse(x, y):
    points = triangle_points(x, y)
    
    mid = midpoint(points['B'], points['C'])
    
    median = distance(
        points['A'],
        mid
    )
    
    angle = vertex_angle(points['A'], points['B'], points['C'])
    
    return median, points, mid, angle


def visualize(x, y, median, points, midpoint, angle):
    plt.figure(figsize=(10, 8))
    
    point_a = points['A']
    point_b = points['B']
    point_c = points['C']
    
    triangle_x = [point_a[0], point_b[0], point_c[0], point_a[0]]
    triangle_y = [point_a[1], point_b[1], point_c[1], point_a[1]]
    plt.plot(triangle_x, triangle_y, 'b-', linewidth=2, label='Triangle')
    
    plt.plot([point_a[0], midpoint[0]], [point_a[1], midpoint[1]], 'r-', linewidth=3, label=f'Median ({median:.4f})')
    
    plt.plot(point_a[0], point_a[1], 'go', markersize=12, label=f'Vertex A (User Input): ({point_a[0]}, {point_a[1]})')
    plt.plot(point_b[0], point_b[1], 'bo', markersize=12, label=f'Base Point B: ({point_b[0]}, {point_b[1]})')
    plt.plot(point_c[0], point_c[1], 'co', markersize=12, label=f'Base Point C: ({point_c[0]}, {point_c[1]})')
    plt.plot(midpoint[0], midpoint[1], 'mo', markersize=10, label=f'Midpoint: ({midpoint[0]:.2f}, {midpoint[1]})')
    
    plt.text(point_a[0] + 0.3, point_a[1] + 0.5, f'A({point_a[0]}, {point_a[1]})\nAngle: {angle:.2f}°', fontsize=10, fontweight='bold')
    plt.text(point_b[0] - 1, point_b[1] - 0.8, f'B({point_b[0]}, {point_b[1]})', fontsize=10, fontweight='bold')
    plt.text(point_c[0] + 0.3, point_c[1] - 0.8, f'C({point_c[0]}, {point_c[1]})', fontsize=10, fontweight='bold')
    plt.text(midpoint[0] + 0.3, midpoint[1] + 0.5, f'M({midpoint[0]:.2f}, {midpoint[1]})', fontsize=9, fontweight='bold', color='purple')
    
    plt.xlabel('X Coordinate', fontsize=12, fontweight='bold')
    plt.ylabel('Y Coordinate', fontsize=12, fontweight='bold')
    plt.title(f'Triangle with Median Line and Vertex Angle = {angle:.2f}°', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right', fontsize=10)
    
    plt.xlim(-2, 32)
    plt.ylim(-2, 17)
    
    plt.tight_layout()
    plt.show()


def summarise(x, y, median, angle):
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Vertex Point A (Shooters Position):          ({x}, {y})")
    print(f"Point B:            (8.42, 0)")
    print(f"Point C:            (11.58, 0)")
    print(f"Median Line Length:      {median:.4f} units")
    print(f"Angle at Vertex A:       {angle:.4f}°")
    print("="*60 + "\n")


def main():
    x, y = input()
    median, points, midpoint, angle = hypotenuse(x, y)
    visualize(x, y, median, points, midpoint, angle)
    summarise(x, y, median, angle)


if __name__ == "__main__":
    main()
