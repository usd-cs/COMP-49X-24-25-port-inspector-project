# flake8: noqa
"""
Method that takes in a user input image or set of user images and runs them through 
the loaded trained models and creates a combined classification output
"""
import sys
import os
import json
import torch
import dill
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class GenusEvaluationMethod:
    """
    Takes image input and creates a classification by running the image through
    loaded CNN models
    """

    def __init__(self, height_filename, models_dict, eval_method,
                 genus_filename, accuracies_filename=None):
        """
        Load the trained models for usage and have the class prepared for user input.
        During testing phases, determining which evaluation method defined below will 
        be chosen here as well
        """
        self.use_method = eval_method     #1 = heaviest, 2 = weighted, 3 = stacked

        self.accuracies_filename = accuracies_filename

        self.trained_models = models_dict

        self.genus_idx_dict = self.open_class_dictionary(genus_filename)

        self.height = None
        with open(height_filename, 'r', encoding='utf-8') as file:
            self.height = int(file.readline().strip())

        #load transformations to a list for use in the program
        self.transformations = self.get_transformations()

    def open_class_dictionary(self, filename):
        """
        Open and save the class dictionary for use in the evaluation method 
        to convert the model's index to a string species classification

        Returns: dictionary defined by file
        """
        with open(filename, 'r', encoding='utf-8') as json_file:
            class_dict_read = json.load(json_file)

        #Convert string keys to integers(keys automatically switched by json save)
        #Undoes issues created by json saving
        class_dict = {}

        for key, value in class_dict_read.items():
            class_dict[int(key)] = value

        return class_dict

    def get_transformations(self):
        """
        Create and return a list of transformations for each angle using
        the pre-made transformation files

        Returns: list of transformations
        """
        transformations = []

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "caud_transformation.pth"), "rb") as f:
            transformations.append(dill.load(f))

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "dors_transformation.pth"), "rb") as f:
            transformations.append(dill.load(f))

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fron_transformation.pth"), "rb") as f:
            transformations.append(dill.load(f))

        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "late_transformation.pth"), "rb") as f:
            transformations.append(dill.load(f))

        return transformations

    def evaluate_image(self, late=None, dors=None, fron=None, caud=None):
        """
        Create an evaluation of the input image(s) by running each given image through
        its respective model and then run the output of the models through the evaluation method
        and return the classification

        Returns: Classification of input images and confidence score. 
                A return of None, -1 indicates an error
        """
        # Set device to a CUDA-compatible gpu
        # Else use CPU to allow general usability and MPS if user has Apple Silicon
        device = torch.device(
            'cuda' if torch.cuda.is_available() 
            else 'mps' if torch.backends.mps.is_built()
            else 'cpu')

        #define variables outside the if statements so they can be used in other method calls
        predictions = {
            "late" : {"score" : 0, "genus" : None},
            "dors" : {"score" : 0, "genus" : None},
            "fron" : {"score" : 0, "genus" : None},
            "caud" : {"score" : 0, "genus" : None},
        }

        view_count = 0

        if late:
            view_count += 1
            late_image = self.transform_input(late, self.transformations[3]).to(device)

            with torch.no_grad():
                late_output = self.trained_models["late"].to(device)(late_image)

            # Get the predicted class and confidence score
            _, predicted_index = torch.max(late_output, 1)
            predictions["late"]["score"] = torch.nn.functional.softmax(
                late_output, dim=1)[0, predicted_index].item()
            predictions["late"]["genus"] = predicted_index.item()

        if dors:
            view_count += 1
            #mirrors above usage but for the dors angle
            dors_image = self.transform_input(dors, self.transformations[1]).to(device)

            with torch.no_grad():
                dors_output = self.trained_models["dors"].to(device)(dors_image)

            _, predicted_index = torch.max(dors_output, 1)
            predictions["dors"]["score"] = torch.nn.functional.softmax(
                dors_output, dim=1)[0, predicted_index].item()
            predictions["dors"]["genus"] = predicted_index.item()

        if fron:
            view_count += 1
            #mirrors above usage but for the fron angle
            fron_image = self.transform_input(fron, self.transformations[2]).to(device)

            with torch.no_grad():
                fron_output = self.trained_models["fron"].to(device)(fron_image)

            _, predicted_index = torch.max(fron_output, 1)
            predictions["fron"]["score"] = torch.nn.functional.softmax(
                fron_output, dim=1)[0, predicted_index].item()
            predictions["fron"]["genus"] = predicted_index.item()

        if caud:
            view_count += 1
            #mirrors above usage but for the caud angle
            caud_image = self.transform_input(caud, self.transformations[0]).to(device)

            with torch.no_grad():
                caud_output = self.trained_models["caud"].to(device)(caud_image)

            _, predicted_index = torch.max(caud_output, 1)
            predictions["caud"]["score"] = torch.nn.functional.softmax(
                caud_output, dim=1)[0, predicted_index].item()
            predictions["caud"]["genus"] = predicted_index.item()

        return self.evaluation_handler(predictions, view_count)

    def evaluation_handler(self, predictions, view_count):
        """
        Creates an evaluation by taking the predictions from the models and creating two
        nested lists of each angle and their top scores and species. With these lists
        created and the view count the method correctly calls the desired evaluation
        method and returns the predicted list.

        Returns: List of tuples [(species_name, confidence_score), ...]
            sorted by confidence(index 0 being the highest).
            A return of None, -1 indicates an error
        """

        if self.use_method == 1:
            #match uses the index returned from the method to decide which prediction to return
            return self.heaviest_is_best([predictions["fron"]["score"],
                                       predictions["dors"]["score"],
                                       predictions["late"]["score"],
                                       predictions["caud"]["score"]],
                                      [predictions["fron"]["genus"],
                                       predictions["dors"]["genus"],
                                       predictions["late"]["genus"],
                                       predictions["caud"]["genus"]])

        if self.use_method == 2:
            # Initialize weights for use in weighted eval, using the genus models accuracies
            weights = []
            score_list = []
            genus_list = []
            if self.accuracies_filename:
                with open(self.accuracies_filename, 'r', encoding='utf-8') as f:
                    accuracy_dict = json.load(f)

                for key in ["fron", "dors", "late", "caud"]:
                    if predictions[key]["genus"]:
                        weights.append(accuracy_dict[key])
                        score_list.append(predictions[key]["score"])
                        genus_list.append(predictions[key]["genus"])
                # adjust weight percentages by normalizing to sum to 1
                weights_sum = sum(weights)
                weights = [weight / weights_sum for weight in weights]
            else:
                weights = [0.25 for i in range(view_count)]

            return self.weighted_eval(score_list, genus_list, weights, view_count)

        if self.use_method == 3:
            return self.stacked_eval()

        return None, -1

    def heaviest_is_best(self, conf_scores, genus_predictions):
        """
        Takes the certainties of the models and returns the most 
        certain model's specification

        Returns: specifies most certain model
        """
        accs = []
        use_angle = None
        if self.accuracies_filename:
            with open(self.accuracies_filename, 'r', encoding='utf-8') as f:
                accuracy_dict = json.load(f)

            angle_list = ["fron", "dors", "late", "caud"]
            acc_dict_reverse = {v:k for k, v in accuracy_dict.items()}
            for i in conf_scores:
                if i != 0:
                    accs.append(accuracy_dict[angle_list[conf_scores.index(i)]])
            use_angle = acc_dict_reverse[max(accs)]

        elif genus_predictions[1] is not None:
            use_angle = "dors"
        elif genus_predictions[3] is not None:
            use_angle = "caud"
        elif genus_predictions[0] is not None:
            use_angle = "fron"
        elif genus_predictions[2] is not None:
            use_angle = "late"

        if use_angle == "fron":
            return self.genus_idx_dict[genus_predictions[0]], conf_scores[0]
        elif use_angle == "dors":
            return self.genus_idx_dict[genus_predictions[1]], conf_scores[1]
        elif use_angle == "late":
            return self.genus_idx_dict[genus_predictions[2]], conf_scores[2]
        elif use_angle == "caud":
            return self.genus_idx_dict[genus_predictions[3]], conf_scores[3]


    def weighted_eval(self, conf_scores, genus_predictions, weights, view_count):
        """
        Takes the classifications of the models and combines them based on programmer determined
        weights to create a single output

        Returns: classification of combined models
        """

        genus_scores = {}
        for i in range(view_count):
            weighted_score = weights[i] * conf_scores[i]

            if genus_predictions[i] in genus_scores:
                genus_scores[genus_predictions[i]] += weighted_score

            else:
                genus_scores[genus_predictions[i]] = weighted_score

        highest_score = -1
        highest_species = None

        for i, j in genus_scores.items():
            if j > highest_score:
                highest_score = j
                highest_species = i

        return self.genus_idx_dict[highest_species], highest_score

    def stacked_eval(self):
        """
        Takes the classifications of the models and runs them through another model that determines
        the overall output

        REACH CASE/STUB FOR SPRINT 3

        Returns: classification of combined models
        """

    def transform_input(self, image_input, transformation):
        """
        Takes the app side's image and transforms it to fit our model

        Returns: transformed image for classification
        """
        transformed_image = transformation(image_input)
        transformed_image = transformed_image.unsqueeze(0)

        return transformed_image
