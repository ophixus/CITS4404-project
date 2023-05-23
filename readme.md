## Project Overview
This project involves extracting and identifying targeted regions in images, determining their color, performing stereo depth estimation, and finally computing the 3D positions and camera pose of the identified targets. It follows these steps:

1. **Image Load and Preprocessing**: The image is loaded and preprocessed to create masks for potential target identification.

2. **Target Extraction**: Labeling and filtering are used to identify target regions in the image.

3. **Hexagonal Target Identification**: Hexagonal clusters in the image are identified using a KDTree and least squares fitting. The clusters are then displayed in the original image for verification.

4. **Target Group Processing**: Each target group is processed to determine the colors of the regions and create a binary string representation.

5. **Calculation of Weighted Centroids**: The weighted centroids of the targets are calculated by considering the color difference within the region. Morphological dilation is used for distance calculation.

6. **Stereo Depth Estimation**: Depth estimation is performed by comparing a stereo pair of images. This is done using OpenCV's StereoSGBM algorithm. A depth map is calculated from the disparity map and used for computing the 3D position of targets.

7. **Computation of 3D Positions**: The 3D position of each target is computed using the depth map and the weighted centroids.

8. **Camera Pose Estimation**: The PnP problem is solved using OpenCV's solvePnP function to estimate the camera pose in 3D.

9. **Pose Inversion**: The solutions obtained in the previous step are inverted to estimate the pose of each target in the camera frame.

10. **Initial Alignment of Cameras**: The estimated poses of the targets are used to align the other cameras, providing an initial estimate of the relative poses of all cameras.

11. **Refinement of Camera Parameters and 3D Target Positions**: A global bundle adjustment procedure is carried out to minimize the total reprojection error, refining the estimated camera parameters and 3D target positions.

12. **Computation of Depth Information**: The calibrated cameras are used to compute depth information, typically involving a process like stereo rectification and disparity map calculation.

## Running the Code

To run the code, you need Python 3.6 or above and the libraries OpenCV, NumPy, SciPy, skimage, and matplotlib. The scripts should be run in the order specified above, with the image file paths and camera parameters adjusted to match your setup. The color and area thresholds used for target extraction may need to be tuned for different images.

## Requirements

- Python 3.6 and above
- Libraries: OpenCV, NumPy, SciPy, skimage, matplotlib

## References

- [OpenCV StereoSGBM](https://docs.opencv.org/master/d2/d85/classcv_1_1StereoSGBM.html)
- [OpenCV solvePnP](https://docs.opencv.org/2.4/modules/calib3d/doc/camera_calibration_and_3d_reconstruction.html#cv2.solvePnP)


## Project Steps 

## Step 1: Load the Image
Firstly, we load the image using OpenCV's imread function and then convert the image from BGR to RGB format.

```python
import cv2

# Load image
image = cv2.imread('your_image.png')

# Convert the image from BGR to RGB
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
```



## Step 2: Image Preprocessing
In this step, we create a mask based on specific color and size criteria to highlight potential targets in the image. The code function create_mask takes an image and thresholds as inputs and returns filtered components based on the conditions. The function performs connected components analysis and filters out components based on the min and max area.

```python
from skimage.measure import label, regionprops

def create_mask(image):
    # Apply thresholds and perform connected components analysis
    # ...

filtered_components = create_mask(image)
```

## Step 3: Identify Potential Targets
Next, we identify potential target regions in the image using a KDTree and least squares fitting. The find_target_components function takes filtered components as input and returns components that are likely to be targets based on the residual error from the least squares fitting.

```python
from scipy.spatial import KDTree
from scipy.linalg import lstsq

def find_target_components(filtered_components):
    # Use a KDTree and least squares fitting to identify targets
    # ...

target_components = find_target_components(filtered_components)
```


## Step 4: Process Target Groups
Process the target groups identified in the image. This step calculates the mean color of each region in the group, determines its binary representation, and orders the groups.

```python
def process_target_groups(target_groups):
    # Initialize processed targets list
    # Iterate through target groups
        # Initialize target color list and binary string
        # Iterate through each region
            # Compute the mean color and correct for camera color temperature
            # Determine the color name and add to binary string
        # Ignore targets without exactly one blue region
        # Determine index of blue region and reorder regions/colors/binary string
        # Sort remaining regions in clockwise order
        # Remove 'x' from binary string and add processed target to list
    # Return processed targets

processed_targets_ZED = process_target_groups(target_group)
```


## Step 5: Calculate Weighted Centroids
Calculate the weighted centroids of each region in the processed targets. The centroid is weighted by the distance of each pixel in the region from the mean color of the region.

```python
def calculate_weighted_centroids(processed_targets, image):
    # Initialize list of weighted centroids
    # Iterate over targets
        # Iterate over regions
            # Get pixel values in the image for the region
            # Calculate the mean color of the region
            # Initialize the weighted sum and sum of weights
            # Calculate maximum distance
            # Iterate over each pixel in the region
                # Calculate weight of pixel
                # Update weighted sum and sum of weights
            # Calculate weighted centroid and append to list
    # Return list of weighted centroids
    
weighted_centroids,processed_targets_ZED = calculate_weighted_centroids(processed_targets_ZED, image)
```

## Step 6,7:Stereo Depth Estimation and Compute 3D Positions
Calculate the 3D positions of each region in the processed targets. To do this, we will compute a disparity map using stereo images and then convert this into a depth map, which allows us to find the depth (z-coordinate) of each point.

```python
def compute_3d_positions(processed_targets, img_left_path, img_right_path, f=640, B=120):
    # Load the left and right images
    # Get the shape of the image
    # Create StereoSGBM object
    # Compute the disparity map
    # Calculate the depth map
    # Initialize list to hold 3D points
    # For each weighted centroid, get the z value from the depth map and append the 3D point to your list
    # Print the 3D coordinates of the targets
    # Return the 3D points, processed targets, and depth map


```

This will give you the 3D coordinates for each region of the reference camera's targets.


## Step 8: Get Camera Parameters and Solve PnP
Firstly, choose a reference camera. Get the camera parameters from a JSON file, and then solve the perspective-n-point (PnP) problem to find the position and orientation of the camera relative to the targets. PnP is a problem in computer vision where the goal is to determine the position and orientation of a camera given a set of 3D points in the real world and their corresponding 2D projections in the image.

```python
def get_camera_params_and_solve_pnp(left_json_file, weighted_centroids, points_3D):
    # Load the JSON file
    # Extract the camera parameters
    # Build the camera matrix
    # Extract the distortion coefficients
    # Define the image points and object points
    # Solve the PnP problem
    # Return the rotation vector and the translation vector

rvec_left, tvec_left = get_camera_params_and_solve_pnp('path', weighted_centroids, points_3D)
```

The function returns two items: the rotation vector (`rvec`) and the translation vector (`tvec`). These represent the orientation and position of the camera, respectively.


## Step 9: Invert the Rotation and Translation Vectors
For some applications, it might be more useful to know the pose of the targets relative to the camera, rather than the pose of the camera relative to the targets. This can be obtained by inverting the rotation and translation vectors.

```python
# Convert the rotation vector to a rotation matrix.
R, _ = cv2.Rodrigues(rvec)

# Invert the rotation matrix.
R_inv = np.transpose(R)

# Invert the translation vector.
tvec_inv = -np.dot(R_inv, tvec)
```

The function `cv2.Rodrigues` converts a rotation vector to a rotation matrix. Then the rotation matrix is inverted by transposing it (since rotation matrices are orthogonal). Finally, the translation vector is inverted by multiplying it with the negative of the inverted rotation matrix.

## Step 10: Align Other Cameras Using PnP Solver

This step helps establish the initial estimate of the relative poses of all cameras in the system. By repeating the previous steps, utilize the PnP (Perspective-n-Point) solver to estimate the pose of each camera relative to the reference camera which can align the other RealSense cameras with the ZED camera and obtain the pose of each camera relative to the common world coordinate system established by the ZED camera


