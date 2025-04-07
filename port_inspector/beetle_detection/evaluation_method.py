"""
Method that takes in a user input image or set of user images and runs them through 
the loaded trained models and creates a combined classification output
"""
import sys
import os
import json
from torchvision import transforms
import torch

class EvaluationMethod:
    """
    Takes image input and creates a classification by running the image through
    loaded CNN models
    """

    def __init__(self, height_filename, models_dict, eval_method, species_filename):
        """
        Load the trained models for usage and have the class prepared for user input.
        During testing phases, determining which evaluation method defined below will 
        be chosen here as well
        """
        self.use_method = eval_method     #1 = heaviest, 2 = weighted, 3 = stacked

        #weights for use in weighted eval. Can be tweaked later to optimize evaluation accuracy
        self.weights = [0.25, 0.25, 0.25, 0.25]
        self.trained_models = models_dict

        self.species_idx_dict = self.open_class_dictionary(species_filename)

        self.height = None
        with open(height_filename, 'r', encoding='utf-8') as file:
            self.height = int(file.readline().strip())

        # initialize the size of how many classifications you want outputted by the evaluation
        self.k = 5

    def open_class_dictionary(self, filename):
        """
        Open and save the class dictionary for use in the evaluation method 
        to convert the model's index to a string species classification

        Returns: dictionary defined by file
        """
        with open(filename, 'r', encoding='utf-8') as json_file:
            class_dict = json.load(json_file)

        # Convert string keys to integers(because of how the dictionary was saved with json)
        class_dict = {int(key): value for key, value in class_dict.items()}

        return class_dict

    def evaluate_image(self, late=None, dors=None, fron=None, caud=None):
        """
        Create an evaluation of the input image(s) by running each given image through
        its respective model and then run the output of the models through the evaluation method
        and returns the top classifications

        Returns: List of tuples [(species_name, confidence_score), ...]
            sorted by confidence(index 0 being the highest).
            A return of None, -1 indicates an error
        """
        device = torch.device('mps' if torch.backends.mps.is_built() else 'cpu')

        #define variables outside the if statements so they can be used in other method calls
        predictions = {
            "late" : {"scores" : 0, "species" : None},
            "dors" : {"scores" : 0, "species" : None},
            "fron" : {"scores" : 0, "species" : None},
            "caud" : {"scores" : 0, "species" : None},
        }

        if late:
            late_image = self.transform_input(late).to(device)

            with torch.no_grad():
                late_output = self.trained_models["late"].to(device)(late_image)

            # Get the predicted top 5 species(or less if not enough outputs) and their indices
            softmax_scores = torch.nn.functional.softmax(late_output, dim=1)[0]
            top5_scores, top5_species = torch.topk(softmax_scores, self.k)

            # Store top 5 confidence and species as a list to the correct dictionary entry
            # Index 0 is the highest and 4 is the lowest
            predictions["late"]["scores"] = top5_scores.tolist()
            predictions["late"]["species"] = top5_species.tolist()

        if dors:
            # Mirrors above usage but for the dors angle
            dors_image = self.transform_input(dors).to(device)

            with torch.no_grad():
                dors_output = self.trained_models["dors"].to(device)(dors_image)

            softmax_scores = torch.nn.functional.softmax(dors_output, dim=1)[0]
            top5_scores, top5_species = torch.topk(softmax_scores, self.k)

            predictions["dors"]["scores"] = top5_scores.tolist()
            predictions["dors"]["species"] = top5_species.tolist()

        if fron:
            # Mirrors above usage but for the fron angle
            fron_image = self.transform_input(fron).to(device)

            with torch.no_grad():
                fron_output = self.trained_models["fron"].to(device)(fron_image)

            softmax_scores = torch.nn.functional.softmax(fron_output, dim=1)[0]
            top5_scores, top5_species = torch.topk(softmax_scores, self.k)

            predictions["fron"]["scores"] = top5_scores.tolist()
            predictions["fron"]["species"] = top5_species.tolist()

        if caud:
            # Mirrors above usage but for the caud angle
            caud_image = self.transform_input(caud).to(device)

            with torch.no_grad():
                caud_output = self.trained_models["caud"].to(device)(caud_image)

            softmax_scores = torch.nn.functional.softmax(caud_output, dim=1)[0]
            top5_scores, top5_species = torch.topk(softmax_scores, self.k)

            predictions["caud"]["scores"] = top5_scores.tolist()
            predictions["caud"]["species"] = top5_species.tolist()

        # Create a nested list with each angles top scores(scores_list) and species(species_list)
        scores_list = [predictions[key]["scores"]
                       for key in ["fron", "dors", "late", "caud"]]
        species_list = [predictions[key]["species"]
                        for key in ["fron", "dors", "late", "caud"]]


        if self.use_method == 1:
            # Match uses the index returned from the method to decide which prediction to return
            return self.heaviest_is_best(scores_list, species_list)

        if self.use_method == 2:
            return self.weighted_eval(scores_list, species_list)

        if self.use_method == 3:
            return self.stacked_eval()

        return None, -1

    def heaviest_is_best(self, conf_scores, species_predictions):
        """
        Takes the certainties of the models and returns the top 5 most certain predictions
        from the models based on which scores were the highest throughout the 4 models.

        Returns: List of tuples [(species_name, confidence_score), ...]
            sorted by confidence(index 0 being the highest).
        """

        top_species_scores = {}

        for i in range(4):
            if species_predictions[i] is not None:  # Ensure predictions exist
                for rank in range(self.k):  # Loop over the top 5 species per angle
                    species_idx = species_predictions[i][rank]
                    score = conf_scores[i][rank]

                    if species_idx in top_species_scores:
                        top_species_scores[species_idx] = max(
                            top_species_scores[species_idx], score)
                    else:
                        top_species_scores[species_idx] = score

        # Create sorted list using sorted method (list with tuples nested inside(key, value))
        sorted_scores = sorted(top_species_scores.items(), key=lambda item: item[1], reverse=True)
        # Change key from index to correct species name
        top_5 = []
        for key, value in sorted_scores:
            if key in self.species_idx_dict:
                top_5.append((self.species_idx_dict[key], value))
            else:
                top_5.append(("Unknown Species", value))

        return top_5


    def weighted_eval(self, conf_scores, species_predictions):
        """
        Takes the classifications of the models and combines them based on programmer determined
        weights to create a list of tuples containing the top 5 species(from the weighted algorithm)

        Returns: List of tuples [(species_name, confidence_score), ...]
            sorted by confidence(index 0 being the highest).
        """
        top_species_scores = {}
        # Iterate through each model and perform the weighted algorithm on their top scores
        for i in range(4):
            if species_predictions[i] is not None:
                for rank in range(self.k):
                    species_idx = species_predictions[i][rank]
                    weighted_score = self.weights[i] * conf_scores[i][rank]

                    if species_idx in top_species_scores:
                        top_species_scores[species_idx] += weighted_score

                    else:
                        top_species_scores[species_idx] = weighted_score

        # Create sorted list using sorted method (list with tuples nested inside(key, value))
        sorted_scores = sorted(top_species_scores.items(), key=lambda item: item[1], reverse=True)
        # Change key from index to correct species name
        top_5 = []
        for key, value in sorted_scores:
            if key in self.species_idx_dict:
                top_5.append((self.species_idx_dict[key], value))
            else:
                top_5.append(("Unknown Species", value))

        return top_5

    def stacked_eval(self):
        """
        Takes the classifications of the models and runs them through another model that determines
        the overall output

        REACH CASE/STUB FOR SPRINT 3

        Returns: classification of combined models
        """

    def transform_input(self, image_input):
        """
        Takes the app side's image and transforms it to fit our model

        Returns: transformed image for classification
        """
        transformation = transforms.Compose([
            transforms.Resize((self.height, self.height)), #ResNet expects 224x224 images
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        transformed_image = transformation(image_input)
        transformed_image = transformed_image.unsqueeze(0)

        return transformed_image
