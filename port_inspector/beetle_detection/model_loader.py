# flake8: noqa
""" model_loader.py """

import json
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
        # Set device to a CUDA-compatible gpu
        # Else use CPU to allow general usability and MPS if user has Apple Silicon
        self.device = torch.device("mps" if torch.backends.mps.is_built() else "cpu")
        self.device = torch.device(
            'cuda' if torch.cuda.is_available()
            else 'mps' if torch.backends.mps.is_built()
            else 'cpu')

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

            # set models to evaluation mode
            self.models[key].eval()

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
            print(f"Weights File for {key} Model Does Not Exist.")

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

    def load_stack_model(self, label, df, dict_file):
        """
        Args:
            label: "Genus" or "Species" depending on which is being loaded
            df: pandas dataframe used for finding proper model dimensions
            dict_file: associated dictionary filename to find the output dimension
        Returns:                torch.nn.Module: stack model loaded from input file
        """
        with open("src/models/" + dict_file, 'r', encoding='utf-8') as json_file:
            class_dict = json.load(json_file)

        #generate dataframe is needed for getting proper dimensions for the model
        x = df.drop(columns=[label]).values
        input_dim = x.shape[1]
        output_dim = len(class_dict)
        model = torch.nn.Linear(input_dim, output_dim)
        model.load_state_dict(torch.load(f"src/models/{label}_meta.pth"))
        model.eval()

        return model
