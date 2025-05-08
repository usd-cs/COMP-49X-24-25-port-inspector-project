""" transformation_classes.py """
import math
from PIL import ImageOps
import torch.nn.functional as F
import torch
from torchvision import transforms

# Edge Detection function in transformation
class SobelEdgeDetection():
    """
    Transformation class to transform image tensor using 
    Sobel Edge Detection and focusing on shape and contours
    Arguments: None
    """
    def __init__(self):
        """
        Initialize values
        """
        # Define Sobel kernels
        self.sobel_x = torch.tensor([[-1, 0, 1],
            [-2, 0, 2],
            [-1, 0, 1]], dtype=torch.float32).view(1, 1, 3, 3)

        self.sobel_y = torch.tensor([[-1, -2, -1],
            [ 0,  0,  0],
            [ 1,  2,  1]], dtype=torch.float32).view(1, 1, 3, 3)

    def __call__(self, tensor):
        """
        Return: modified tensor
        """
        # Ensure the kernel is on the same device as the input tensor
        sobel_x = self.sobel_x.to(tensor.device)
        sobel_y = self.sobel_y.to(tensor.device)

        # Initialize output tensors
        grad_x = torch.zeros_like(tensor)
        grad_y = torch.zeros_like(tensor)

        # Apply Sobel operator to each channel
        for i in range(tensor.size(0)):
            grad_x[i:i+1] = F.conv2d(tensor[i:i+1].unsqueeze(0), sobel_x, padding=1)
            grad_y[i:i+1] = F.conv2d(tensor[i:i+1].unsqueeze(0), sobel_y, padding=1)

        # Compute gradient magnitude
        edge_magnitude = torch.sqrt(grad_x**2 + grad_y**2)

        # Normalize to [0, 1]
        edge_magnitude = edge_magnitude / edge_magnitude.max()

        return edge_magnitude.squeeze(0)

class HistogramEqualization():
    """
    Transformation class to transform image tensor using Histogram Equalization,
    which enhances the contrast of the image.
    Arguments: None
    """

    def __call__(self, tensor):
        """
        Return: modified tensor
        """
        # Ensure image is in PIL format
        if isinstance(tensor, torch.Tensor):
            tensor = transforms.ToPILImage()(tensor)

        # Apply histogram equalization on image
        transformed_img = ImageOps.equalize(tensor)

        # Convert transformed image back to tensor
        transformed_tensor = transforms.ToTensor()(transformed_img)

        return transformed_tensor

class DCTTransform:
    """
    Apply 2D Discrete Cosine Transform as a preprocessing step.
    Can be used in a transforms.Compose pipeline.
    """
    def dct_2d(self, x: torch.Tensor) -> torch.Tensor:
        """Apply 2D DCT to input tensor"""
        B, C, H, W = x.shape
        device = x.device

        # Compute 1D DCT basis
        def get_dct_matrix(N, dtype=torch.float32):
            n = torch.arange(N, dtype=dtype)
            k = torch.arange(N, dtype=dtype).unsqueeze(1)

            dct_m = torch.cos(math.pi * k * (n + 0.5) / N)
            dct_m[0, :] *= 1 / math.sqrt(2)

            dct_m *= math.sqrt(2 / N)
            dct_m[0, :] *= 1 / math.sqrt(2)

            return dct_m.to(device)

        # Get DCT matrices
        dct_h = get_dct_matrix(H)
        dct_w = get_dct_matrix(W)

        # Apply DCT to each channel
        result = torch.zeros_like(x)
        for b in range(B):
            for c in range(C):
                # Apply DCT to rows (height dimension)
                tmp = torch.matmul(dct_h, x[b, c])
                # Apply DCT to columns (width dimension)
                result[b, c] = torch.matmul(tmp, dct_w.T)

        return result

    def __call__(self, x: torch.Tensor) -> torch.Tensor:
        """
        Return: modified tensor
        """
        # Add batch dimension if needed
        if x.dim() == 3:
            x = x.unsqueeze(0)

        # Apply DCT
        x_dct = self.dct_2d(x)

        # Remove batch dimension if we added it
        if x.dim() == 4 and x.size(0) == 1:
            x_dct = x_dct.squeeze(0)

        return x_dct
