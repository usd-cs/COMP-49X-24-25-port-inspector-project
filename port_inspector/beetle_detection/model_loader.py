""" model_loader.py """

from torchvision import models
import torch

class ModelLoader:
    """
    Initializes and loads four models with the designated pretrained weights for
    the different image angles.
    """
    def __init__(self, weights_file_paths, num_classes = 15, test = False):
        """
        Initializes the TrainedModels class.

        Args:
            weights_file_paths (dict): A dictionary mapping model keys to their weight file paths.
            test (bool, optional): If True, skips model initialization for testing purposes.
        """
        self.weights_file_paths = weights_file_paths
        self.num_classes = num_classes

        self.models = {
            "caud" : None, 
            "dors" : None,
            "fron" : None,
            "late" : None
        }

        # use CPU to allow general usability and Metal Performance Shader if user has Apple Silicon
        self.device = torch.device("mps" if torch.backends.mps.is_built() else "cpu")

        if not test:
            self.model_initializer()

    def model_initializer(self):
        """
        Initializes ResNet50 models for each key in self.models and replaces the fully connected
        layer to output 15 classes. Lastly, loads pretrained weights into the initialized
        model with load_model_weights(key).

        Returns:
            None
        """
        for key in self.models:
            # Initialize a fresh model with weights = None, so there are no weights
            self.models[key] = models.resnet50(weights=None)

            # Initialize the models to have 15 outputs(~number of species to be identified)
            num_features = self.models[key].fc.in_features
            self.models[key].fc = torch.nn.Linear(num_features, self.num_classes)

            self.models[key] = self.models[key].to(self.device)

            self.load_model_weights(key)

    def load_model_weights(self, key):
        """
        Loads the specified model with the pre-trained weights.

        This method retrieves the file path from the self.weights_file_paths for the model weights 
        based on the provided key and loads them into the model instance loacated at key in the
        self.models dictionary. If no weight file paths are provided, it prompts the user for input.

        Args:
            key (str): The identifier for the model and the corresponding weights to be loaded.

        Returns:
            None
        """

        weights_file_path = self.weights_file_paths[key]

        # Load weights from file path into the model
        try:
            self.models[key].load_state_dict(
                torch.load(weights_file_path, map_location=self.device, weights_only=True))
        except FileNotFoundError:
            print(f"Weights File for {key} Model Does Not Exist. {weights_file_path}")

    def get_models(self):
        """
        Returns:
            dict: A dictionary containing all models(ResNet).
        """
        return self.models

    def get_model(self, key):
        """
        Args:
            key (str): The key identifying the desired model.

        Returns:
            torch.nn.Module: The corresponding ResNet model.
        """
        return self.models[key]
