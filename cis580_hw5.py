# -*- coding: utf-8 -*-
"""cis580_hw5.ipynb

Automatically generated by Colaboratory.


## CIS 580, Machine Perception, Spring 2023
### Homework 5
#### Due: Thursday April 27th 2023, 11:59pm ET

Instructions: Create a folder in your Google Drive and place inside this .ipynb file. Open the jupyter notebook with Google Colab. Refrain from using a GPU during implementing and testing the whole thing. You should switch to a GPU runtime only when performing the final training (of the 2D image or the NeRF) to avoid GPU usage runouts.

### Part 1: Fitting a 2D Image
"""

import numpy as np
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import time
import gdown

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

"""We first download the image from the web. We normalize the image so the pixels are in between the range of [0,1]."""

url = "https://drive.google.com/file/d/1-Cugk9WiFX2CPjWG5taX3868Gdd0PEVT/view?usp=share_link"
gdown.download(url=url, output='starry_night.jpg', quiet=False, fuzzy=True)

# Load painting image
painting = imageio.imread("starry_night.jpg")
painting = torch.from_numpy(np.array(painting, dtype=np.float32)/255.).to(device)
height_painting, width_painting = painting.shape[:2]

"""1.1 Complete the function positional_encoding()"""

from logging import raiseExceptions
def positional_encoding(x, num_frequencies=6, incl_input=True):

    """
    Apply positional encoding to the input.

    Args:
    x (torch.Tensor): Input tensor to be positionally encoded.
      The dimension of x is [N, D], where N is the number of input coordinates,
      and D is the dimension of the input coordinate.
    num_frequencies (optional, int): The number of frequencies used in
     the positional encoding (default: 6).
    incl_input (optional, bool): If True, concatenate the input with the
        computed positional encoding (default: True).

    Returns:
    (torch.Tensor): Positional encoding of the input tensor.
    """

    results = []
    if incl_input:
        results.append(x)
    #############################  TODO 1(a) BEGIN  ############################
    # encode input tensor and append the encoded tensor to the list of results.
    for i in range(num_frequencies):
      sin = torch.sin(results[0]*(2**i)*np.pi)
      results.append(sin)
      cos = torch.cos(results[0]*(2**i)*np.pi)
      results.append(cos)

    #############################  TODO 1(a) END  ##############################
    return torch.cat(results, dim=-1)

"""1.2 Complete the class model_2d() that will be used to fit the 2D image.

"""

class model_2d(nn.Module):

    """
    Define a 2D model comprising of three fully connected layers,
    two relu activations and one sigmoid activation.
    """

    def __init__(self, filter_size=128, num_frequencies=6):
        super().__init__()
        #############################  TODO 1(b) BEGIN  ############################
        self.input_fc = nn.Linear(2+(num_frequencies*2*2),filter_size)
        self.hidden_fc = nn.Linear(filter_size,filter_size)
        self.output_fc = nn.Linear(filter_size,3)

        #############################  TODO 1(b) END  ##############################

    def forward(self, x):
        #############################  TODO 1(b) BEGIN  ############################
        batch_size = x.shape[0]
        x = x.view(batch_size,-1)
        layer_in = F.relu(self.input_fc(x))
        layer_hidden = F.relu(self.hidden_fc(layer_in))
        layer_output = F.sigmoid(self.output_fc(layer_hidden))

        #############################  TODO 1(b) END  ##############################
        return layer_output

"""You need to complete 1.1 and 1.2 first before completing the train_2d_model function. Don't forget to transfer the completed functions from 1.1 and 1.2 to the part1.py file and upload it to the autograder.

Fill the gaps in the train_2d_model() function to train the model to fit the 2D image.
"""

def train_2d_model(test_img, num_frequencies, device, model=model_2d, positional_encoding=positional_encoding, show=True):

    # Optimizer parameters
    lr = 5e-4
    iterations = 10000
    height, width = test_img.shape[:2]

    # Number of iters after which stats are displayed
    display = 2000

    # Define the model and initialize its weights.
    model2d = model(num_frequencies=num_frequencies)
    model2d.to(device)

    def weights_init(m):
        if isinstance(m, nn.Linear):
            torch.nn.init.xavier_uniform_(m.weight)

    model2d.apply(weights_init)

    #############################  TODO 1(c) BEGIN  ############################
    # Define the optimizer
    optimizer = torch.optim.Adam(model2d.parameters())
    #############################  TODO 1(c) END  ############################

    # Seed RNG, for repeatability
    seed = 5670
    torch.manual_seed(seed)
    np.random.seed(seed)

    # Lists to log metrics etc.
    psnrs = []
    iternums = []

    t = time.time()
    t0 = time.time()

    #############################  TODO 1(c) BEGIN  ############################
    # Create the 2D normalized coordinates, and apply positional encoding to them

    # Normalize
    x = torch.linspace(0, 1, height)
    y = torch.linspace(0, 1, width)
    x_grid, y_grid = torch.meshgrid(x, y)
    points = torch.stack((x_grid.reshape(-1), y_grid.reshape(-1)), dim=1)

    # Get encoded values
    encoded = positional_encoding(points, num_frequencies=num_frequencies, incl_input=True)

    #############################  TODO 1(c) END  ############################

    for i in range(iterations+1):

        optimizer.zero_grad()

        #############################  TODO 1(c) BEGIN  ############################
        # Run one iteration


        # Compute mean-squared error between the predicted and target images. Backprop!
        pred = model2d(encoded)
        pred = torch.reshape(pred, (height, width, 3))
        loss = F.mse_loss(pred, test_img)
        loss.backward()
        optimizer.step()
        #############################  TODO 1(c) END  ############################

        # Display images/plots/stats
        if i % display == 0 and show:
            #############################  TODO 1(c) BEGIN  ############################
            # Calculate psnr
            psnr = 10*torch.log10(torch.max(pred)**2/loss)
            # print(psnr.shape)
            #############################  TODO 1(c) END  ############################

            print("Iteration %d " % i, "Loss: %.4f " % loss.item(), "PSNR: %.2f" % psnr.item(), \
                "Time: %.2f secs per iter" % ((time.time() - t) / display), "%.2f secs in total" % (time.time() - t0))
            t = time.time()

            psnrs.append(psnr.item())
            iternums.append(i)

            plt.figure(figsize=(13, 4))
            plt.subplot(131)
            plt.imshow(pred.detach().cpu().numpy())
            plt.title(f"Iteration {i}")
            plt.subplot(132)
            plt.imshow(test_img.cpu().numpy())
            plt.title("Target image")
            plt.subplot(133)
            plt.plot(iternums, psnrs)
            plt.title("PSNR")
            plt.show()

    print('Done!')
    return pred.detach().cpu()

"""Train the model to fit the given image without applying positional encoding to the input, and by applying positional encoding of two different frequencies to the input; L = 2 and L = 6."""

_ = train_2d_model(test_img=painting, num_frequencies=6, device=device)

"""### Part 2: Fitting a 3D Image"""

import os
import gdown
import numpy as np
import torch
import torch.nn as nn
import matplotlib.pyplot as plt
import torch.nn.functional as F
import time

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)

url = "https://drive.google.com/file/d/15W2EK8LooxTMfD0v5vo2BnBMse5ZzlVj/view?usp=share_link"
gdown.download(url=url, output='lego_data.npz', quiet=False, fuzzy=True)

"""Here, we load the data that is comprised by the images, the R and T matrices of each camera position with respect to the world coordinates and the intrinsics parameters K of the camera."""

# Load input images, poses, and intrinsics
data = np.load("lego_data.npz")

# Images
images = data["images"]

# Height and width of each image
height, width = images.shape[1:3]

# Camera extrinsics (poses)
poses = data["poses"]
poses = torch.from_numpy(poses).to(device)

# Camera intrinsics
intrinsics = data["intrinsics"]
intrinsics = torch.from_numpy(intrinsics).to(device)

# Hold one image out (for test).
test_image, test_pose = images[101], poses[101]
test_image = torch.from_numpy(test_image).to(device)

# Map images to device
images = torch.from_numpy(images[:100, ..., :3]).to(device)

plt.imshow(test_image.detach().cpu().numpy())
plt.show()

"""2.1 Complete the following function that calculates the rays that pass through all the pixels of an HxW image"""

def get_rays(height, width, intrinsics, Rcw, Tcw): # Rwc, Twc

    """
    Compute the origin and direction of rays passing through all pixels of an image (one ray per pixel).

    Args:
    height: the height of an image.
    width: the width of an image.
    intrinsics: camera intrinsics matrix of shape (3, 3).
    Rcw: Rotation matrix of shape (3,3) from camera to world coordinates.
    Tcw: Translation vector of shape (3,1) that transforms

    Returns:
    ray_origins (torch.Tensor): A tensor of shape (height, width, 3) denoting the centers of
      each ray. Note that desipte that all ray share the same origin, here we ask you to return
      the ray origin for each ray as (height, width, 3).
    ray_directions (torch.Tensor): A tensor of shape (height, width, 3) denoting the
      direction of each ray.
    """

    device = intrinsics.device
    ray_directions = torch.zeros((height, width, 3), device=device)  # placeholder
    ray_origins = torch.zeros((height, width, 3), device=device)  # placeholder

    #############################  TODO 2.1 BEGIN  ##########################
    x = torch.linspace(0, height-1, height)
    y = torch.linspace(0, width-1, width)
    x_grid, y_grid = torch.meshgrid(x, y, indexing='ij')
    points = torch.stack((y_grid.reshape(-1), x_grid.reshape(-1)), dim=1)
    one = torch.ones(points.shape[0])
    one  = torch.reshape(one,(points.shape[0],1))
    points = torch.hstack((points,one))
    points = points.to(device)
    Tcw = torch.reshape(Tcw,(1,1,3))
    ray_origins = Tcw.repeat(height,width,3)
    ray_origins = ray_origins[:,:,0:3]

    ray_directions = (torch.linalg.inv(intrinsics)@(points.T)).T@Rcw.T
    ray_directions = torch.reshape(ray_directions,(height,width,3))
    #############################  TODO 2.1 END  ############################

    return ray_origins, ray_directions

"""Complete the next function to visualize how is the dataset created. You will be able to see from which point of view each image has been captured for the 3D object. What we want to achieve here, is to being able to interpolate between these given views and synthesize new realistic views of the 3D object."""

# def plot_all_poses(poses):

#     #############################  TODO 2.1 BEGIN  ############################
#     # origins, directions = get_rays()

#     #############################  TODO 2.1 END  ############################

#     ax = plt.figure(figsize=(12, 8)).add_subplot(projection='3d')
#     _ = ax.quiver(origins[..., 0].flatten(),
#                   origins[..., 1].flatten(),
#                   origins[..., 2].flatten(),
#                   directions[..., 0].flatten(),
#                   directions[..., 1].flatten(),
#                   directions[..., 2].flatten(), length=0.12, normalize=True)
#     ax.set_xlabel('X')
#     ax.set_ylabel('Y')
#     ax.set_zlabel('z')
#     plt.show()

# plot_all_poses(data['poses'])

"""2.2 Complete the following function to implement the sampling of points along a given ray."""

def stratified_sampling(ray_origins, ray_directions, near, far, samples):

    """
    Sample 3D points on the given rays. The near and far variables indicate the bounds of sampling range.

    Args:
    ray_origins: Origin of each ray in the "bundle" as returned by the
      get_rays() function. Shape: (height, width, 3).
    ray_directions: Direction of each ray in the "bundle" as returned by the
      get_rays() function. Shape: (height, width, 3).
    near: The 'near' extent of the bounding volume.
    far:  The 'far' extent of the bounding volume.
    samples: Number of samples to be drawn along each ray.

    Returns:
    ray_points: Query 3D points along each ray. Shape: (height, width, samples, 3).
    depth_points: Sampled depth values along each ray. Shape: (height, width, samples).
    """

    #############################  TODO 2.2 BEGIN  ############################
    height = ray_directions.shape[0]
    width  = ray_directions.shape[1]
    depth_points = torch.linspace(near, far, samples, device=ray_origins.device)

    # r = o + dt
    ray_points = ray_origins[...,None, :] + ray_directions[...,None, :] * depth_points[...,None]


    #############################  TODO 2.2 END  ############################
    return ray_points, depth_points

"""2.3 Define the network architecture of NeRF along with a function that divided data into chunks to avoid memory leaks during training."""

class nerf_model(nn.Module):

    """
    Define a NeRF model comprising eight fully connected layers and following the
    architecture described in the NeRF paper.
    """

    def __init__(self, filter_size=256, num_x_frequencies=6, num_d_frequencies=3):
        super().__init__()

        #############################  TODO 2.3 BEGIN  ############################
        self.input_fc    = nn.Linear((2*num_x_frequencies*3 + 3),filter_size)
        self.hidden_fc_1 = nn.Linear(filter_size,filter_size)
        self.hidden_fc_2 = nn.Linear(filter_size,filter_size)
        self.hidden_fc_3 = nn.Linear(filter_size,filter_size)
        self.hidden_fc_4 = nn.Linear(filter_size,filter_size)
        self.hidden_fc_5 = nn.Linear(filter_size + (2*num_x_frequencies*3 + 3),filter_size)
        self.hidden_fc_6 = nn.Linear(filter_size,filter_size)
        self.hidden_fc_7 = nn.Linear(filter_size,filter_size)
        self.sigma_out   = nn.Linear(filter_size,1)
        self.hidden_fc_8 = nn.Linear(filter_size,filter_size)
        self.hidden_fc_9 = nn.Linear(filter_size + (2*num_d_frequencies*3 + 3),int(filter_size/2))
        self.output_fc   = nn.Linear(int(filter_size/2),3)

        #############################  TODO 2.3 END  ############################

    def forward(self, x, d):
        #############################  TODO 2.3 BEGIN  ############################
        batch_size_x = x.shape[0]
        # x = x.view(batch_size_x,-1)

        batch_size_d = d.shape[0]
        # d = d.view(batch_size_d,-1)

        layer_in       = F.relu(self.input_fc(x))
        layer_hidden_1 = F.relu(self.hidden_fc_1(layer_in))
        layer_hidden_2 = F.relu(self.hidden_fc_2(layer_hidden_1))
        layer_hidden_3 = F.relu(self.hidden_fc_3(layer_hidden_2))
        layer_hidden_4 = F.relu(self.hidden_fc_4(layer_hidden_3))
        layer_hidden_4x = torch.cat([layer_hidden_4, x], dim=-1)
        layer_hidden_5 = F.relu(self.hidden_fc_5(layer_hidden_4x))
        layer_hidden_6 = F.relu(self.hidden_fc_6(layer_hidden_5))
        layer_hidden_7 = F.relu(self.hidden_fc_7(layer_hidden_6))
        sigma          = self.sigma_out(layer_hidden_7)
        layer_hidden_8 = self.hidden_fc_8(layer_hidden_7)
        layer_hidden_8d = torch.cat([layer_hidden_8, d], dim=-1)
        layer_hidden_9 = F.relu(self.hidden_fc_9(layer_hidden_8d))
        rgb            = torch.sigmoid(self.output_fc(layer_hidden_9))

        #############################  TODO 2.3 END  ############################
        return rgb, sigma

def get_batches(ray_points, ray_directions, num_x_frequencies, num_d_frequencies):
    """
    ray_points: [H,W,n_samples,3]
    ray_direction: [H,W,3]
    """
    def get_chunks(inputs, chunksize = 2**15):
      return [inputs[i:i + chunksize] for i in range(0, inputs.shape[0], chunksize)]

    """
    This function returns chunks of the ray points and directions to avoid memory errors with the
    neural network. It also applies positional encoding to the input points and directions before
    dividing them into chunks, as well as normalizing and populating the directions.
    """

    def positional_encoding(x, num_frequencies, incl_input=True):
      results = []
      if incl_input:
          results.append(x)
    ############################  TODO 1(a) BEGIN  ############################
    # encode input tensor and append the encoded tensor to the list of results.
      for i in range(num_frequencies):
        sin = torch.sin(results[0]*(2**i)*np.pi)
        results.append(sin)
        cos = torch.cos(results[0]*(2**i)*np.pi)
        results.append(cos)
    #############################  TODO 1(a) END  ##############################
      return torch.cat(results, dim=-1)


    #############################  TODO 2.3 BEGIN  ############################
    ray_directions = ray_directions/torch.linalg.norm(ray_directions,dim=-1,keepdim=True)
    ray_directions = ray_directions.flatten(start_dim=0, end_dim=1).unsqueeze(1)
    ray_directions = ray_directions.repeat(1,ray_points.shape[2],1)
    ray_directions = ray_directions.flatten(start_dim=0, end_dim=1)
    ray_directions = positional_encoding(ray_directions, num_frequencies=num_d_frequencies)
    ray_directions_batches = get_chunks(ray_directions)

    ray_points = ray_points.flatten(start_dim=0, end_dim=2)
    ray_points = positional_encoding(ray_points, num_frequencies=num_x_frequencies)
    ray_points_batches = get_chunks(ray_points)
    #############################  TODO 2.3 END  ############################
    return ray_points_batches, ray_directions_batches

"""2.4 Compute the compositing weights of samples on camera ray and then complete the volumetric rendering procedure to reconstruct a whole RGB image from the sampled points and the outputs of the neural network."""

def volumetric_rendering(rgb, s, depth_points):

    """
    Differentiably renders a radiance field, given the origin of each ray in the
    "bundle", and the sampled depth values along them.

    Args:
    rgb: RGB color at each query location (X, Y, Z). Shape: (height, width, samples, 3).
    sigma: Volume density at each query location (X, Y, Z). Shape: (height, width, samples).
    depth_points: Sampled depth values along each ray. Shape: (height, width, samples).

    Returns:
    rec_image: The reconstructed image after applying the volumetric rendering to every pixel.
    Shape: (height, width, 3)
    """
    #############################  TODO 2.4 BEGIN  ############################
    del_i = torch.diff(depth_points, dim=-1)
    last_value = torch.ones_like(del_i[..., :1])*1e9
    del_i = torch.cat((del_i, last_value), dim=-1)
    s     = F.relu(s)
    T_i   = torch.cumprod(torch.exp(-s*del_i),dim=-1)
    T_i   = torch.roll(T_i, shifts=1, dims=-1)
    C_hat_no_color = T_i*(1-torch.exp(-s*del_i))
    C_hat_color = C_hat_no_color[..., None]*rgb
    rec_image = C_hat_color.sum(dim=-2)
    #############################  TODO 2.4 END  ############################
    return rec_image

"""2.5 Combine everything together. Given the pose position of a camera, compute the camera rays and sample the 3D points along these rays. Divide those points into batches and feed them to the neural network. Concatenate them and use them for the volumetric rendering to reconstructed the final image."""

def one_forward_pass(height, width, intrinsics, pose, near, far, samples, model, num_x_frequencies, num_d_frequencies):

    #############################  TODO 2.5 BEGIN  ############################
    intrinsics = intrinsics.to(device)
    pose = pose.to(device)

    #compute all the rays from the image
    ray_origins, ray_directions = get_rays(height, width, intrinsics, pose[0:3,0:3], pose[0:3,-1])

    ray_origins = ray_origins.to(device)
    ray_directions = ray_directions.to(device)

    #sample the points from the rays
    ray_points, depth_points = stratified_sampling(ray_origins, ray_directions, near, far, samples)

    ray_points = ray_points.to(device)
    depth_points = depth_points.to(device)

    #divide data into batches to avoid memory errors
    ray_points_batches, ray_directions_batches = get_batches(ray_points, ray_directions, num_x_frequencies, num_d_frequencies)

    #forward pass the batches and concatenate the outputs at the end
    final_colors    = []
    final_densities = []
    for i in range(len(ray_points_batches)):
      rgb, sigma = model(ray_points_batches[i] ,ray_directions_batches[i])
      final_colors.append(rgb)
      final_densities.append(sigma)

    final_rgb = torch.concat(final_colors).reshape((height, width, samples,3))
    final_sigma = torch.concat(final_densities).reshape((height, width, samples))


    # Apply volumetric rendering to obtain the reconstructed image
    rec_image = volumetric_rendering(final_rgb,final_sigma,depth_points)

    #############################  TODO 2.5 END  ############################

    return rec_image

"""If you manage to pass the autograder for all the previous functions, then it is time to train a NeRF! We provide the hyperparameters for you, we initialize the NeRF model and its weights, and we define a couple lists that will be needed to store results."""

num_x_frequencies = 10
num_d_frequencies = 4
learning_rate  = 5e-4
iterations = 3000
samples = 64
display = 25
near = 0.667
far = 2

model = nerf_model(num_x_frequencies=num_x_frequencies,num_d_frequencies=num_d_frequencies).to(device)

def weights_init(m):
    if isinstance(m, torch.nn.Linear):
        torch.nn.init.xavier_uniform_(m.weight)
model.apply(weights_init)

optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

psnrs = []
iternums = []

t = time.time()
t0 = time.time()

# for i in range(iterations+1):
#     #############################  TODO 2.6 BEGIN  ############################

#     #choose randomly a picture for the forward pass
#     random_value = torch.randint(0,100, (1,))
#     train_image = images[random_value]
#     train_image = train_image[0].float()
#     pose = poses[random_value]
#     pose = pose[0].float()
#     height = train_image.shape[0]
#     width = train_image.shape[1]

#     # Run one iteration of NeRF and get the rendered RGB image.
#     pred = one_forward_pass(height, width, intrinsics, pose, near, far, samples, model, num_x_frequencies, num_d_frequencies)

#     # Compute mean-squared error between the predicted and target images. Backprop!
#     loss = F.mse_loss(pred, train_image)
#     optimizer.zero_grad()
#     loss.backward()
#     optimizer.step()

#     #############################  TODO 2.6 END  ############################

#     # Display images/plots/stats
#     if i % display == 0:
#         with torch.no_grad():
#         #############################  TODO 2.6 BEGIN  ############################
#             # Render the held-out view
#             test_rec_image = one_forward_pass(height, width, intrinsics, pose, near, far, samples, model, num_x_frequencies, num_d_frequencies)

#         #calculate the loss and the psnr between the original test image and the reconstructed one.
#             loss_test = F.mse_loss(test_rec_image, test_image)
#             psnr = 10*torch.log10(1/loss_test)

#         #############################  TODO 2.6 END  ############################

#         print("Iteration %d " % i, "Loss: %.4f " % loss.item(), "PSNR: %.2f " % psnr.item(), \
#                 "Time: %.2f secs per iter, " % ((time.time() - t) / display), "%.2f mins in total" % ((time.time() - t0)/60))

#         t = time.time()
#         psnrs.append(psnr.item())
#         iternums.append(i)

#         plt.figure(figsize=(16, 4))
#         plt.subplot(141)
#         plt.imshow(test_rec_image.detach().cpu().numpy())
#         plt.title(f"Iteration {i}")
#         plt.subplot(142)
#         plt.imshow(test_image.detach().cpu().numpy())
#         plt.title("Target image")
#         plt.subplot(143)
#         plt.plot(iternums, psnrs)
#         plt.title("PSNR")
#         plt.show()

# print('Done!')

for i in range(iterations+1):

    #############################  TODO 2.6 BEGIN  ############################
    #choose randomly a picture for the forward pass
    # torch.cuda.empty_cache()
    idx=torch.randint(low=0,high=100,size=(1,))
    pose=poses[idx].squeeze(0).float()
    img=images[idx].squeeze(0).float()
    height, width=img.shape[:2]
    test_recw=one_forward_pass(height, width, intrinsics, pose, near, far, samples, model, num_x_frequencies, num_d_frequencies)
    loss = F.mse_loss(test_recw, img)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
    #############################  TODO 2.6 END  ############################

    # Display images/plots/stats
    if i % display == 0:
        with torch.no_grad():
        #############################  TODO 2.6 BEGIN  ############################
            # Render the held-out view
            # R=pred.max()
            # R_MSE=(R**2)/loss
            # psnr=10 * torch.log10(R_MSE)
            test_rec_image=one_forward_pass(height, width, intrinsics, test_pose, near, far, samples, model, num_x_frequencies, num_d_frequencies)
            test_loss=F.mse_loss(test_rec_image, test_image)
            psnr=10*torch.log10(1/test_loss)

        #calculate the loss and the psnr between the original test image and the reconstructed one.


        #############################  TODO 2.6 END  ############################

        print("Iteration %d " % i, "Loss: %.4f " % loss.item(), "PSNR: %.2f " % psnr.item(), \
                "Time: %.2f secs per iter, " % ((time.time() - t) / display), "%.2f mins in total" % ((time.time() - t0)/60))

        t = time.time()
        psnrs.append(psnr.item())
        iternums.append(i)

        plt.figure(figsize=(16, 4))
        plt.subplot(141)
        plt.imshow(test_rec_image.detach().cpu().numpy())
        plt.title(f"Iteration {i}")
        plt.subplot(142)
        plt.imshow(test_image.detach().cpu().numpy())
        plt.title("Target image")
        plt.subplot(143)
        plt.plot(iternums, psnrs)
        plt.title("PSNR")
        plt.show()

print('Done!')
