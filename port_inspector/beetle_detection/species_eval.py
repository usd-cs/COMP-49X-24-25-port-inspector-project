""" simulator.py """
import json
from PIL import Image
from .model_loader import ModelLoader
from .evaluation_method import EvaluationMethod
from .genus_evaluation_method import GenusEvaluationMethod
from django.conf import settings

# -----Run once on import-----
# read json to see size of outputs
with open("./port_inspector/beetle_detection/spec_dict.json", 'r', encoding='utf-8') as spec_dict:
    # SPECIES_OUTPUTS = len(json.load(spec_dict))
    # TODO this should be from the json file but for now we hard code to 15 because of the weights given from ML team
    pass
with open("./port_inspector/beetle_detection/gen_dict.json", 'r', encoding='utf-8') as gen_dict:
    # GENUS_OUTPUTS = len(json.load(gen_dict))
    # TODO same here, should be read from json file
    pass

SPECIES_OUTPUTS = 15
GENUS_OUTPUTS = 9

# Load species models
species_model_paths = {
        "caud" : "port_inspector/beetle_detection/spec_caud.pth", 
        "dors" : "port_inspector/beetle_detection/spec_dors.pth",
        "fron" : "port_inspector/beetle_detection/spec_fron.pth",
        "late" : "port_inspector/beetle_detection/spec_late.pth"
    }
species_ml = ModelLoader(species_model_paths, SPECIES_OUTPUTS)
species_models = species_ml.get_models()
# Set models to evaluation mode
for key in species_models:
    species_models[key].eval()

# Load genus models
genus_model_paths = {
        "caud" : "port_inspector/beetle_detection/gen_caud.pth", 
        "dors" : "port_inspector/beetle_detection/gen_dors.pth",
        "fron" : "port_inspector/beetle_detection/gen_fron.pth",
        "late" : "port_inspector/beetle_detection/gen_late.pth"
    }
genus_ml = ModelLoader(genus_model_paths, GENUS_OUTPUTS)
genus_models = genus_ml.get_models()
# Set genus models to evaluation mode
for key in genus_models:
    genus_models[key].eval()


# Initialize the EvaluationMethod object with the heaviest eval method set
species_evaluator = EvaluationMethod("./port_inspector/beetle_detection/height.txt", species_models, 1, "./port_inspector/beetle_detection/spec_dict.json")
genus_evaluator = GenusEvaluationMethod("./port_inspector/beetle_detection/height.txt", genus_models, 1, "./port_inspector/beetle_detection/gen_dict.json")

print("!!! ML Models loaded in evaluation mode !!!")


def evaluate_images(late_path, dors_path, fron_path, caud_path):
    # Load the provided images
    LATE_IMG = Image.open(late_path) if late_path else None
    DORS_IMG = Image.open(dors_path) if dors_path else None
    FRON_IMG = Image.open(fron_path) if fron_path else None
    CAUD_IMG = Image.open(caud_path) if caud_path else None    
    
    # Run the species evaluation method
    top_5_species = species_evaluator.evaluate_image(
        late=LATE_IMG, dors=DORS_IMG, fron=FRON_IMG, caud=CAUD_IMG
    )

    # Run the genus evaluation method
    top_genus = genus_evaluator.evaluate_image(
        late=LATE_IMG, dors=DORS_IMG, fron=FRON_IMG, caud=CAUD_IMG
    )

    # Print classification results
    print(f"1. Predicted Species: {top_5_species[0][0]}, Confidence: {top_5_species[0][1]:.3f}\n")
    print(f"2. Predicted Species: {top_5_species[1][0]}, Confidence: {top_5_species[1][1]:.3f}\n")
    print(f"3. Predicted Species: {top_5_species[2][0]}, Confidence: {top_5_species[2][1]:.3f}\n")
    print(f"4. Predicted Species: {top_5_species[3][0]}, Confidence: {top_5_species[3][1]:.3f}\n")
    print(f"5. Predicted Species: {top_5_species[4][0]}, Confidence: {top_5_species[4][1]:.3f}\n")
    
    print("Top genus: ", top_genus)

    # Modify confidence numbers to be a percentage
    for i in range(len(top_5_species)):
        top_5_species[i] = (top_5_species[i][0], top_5_species[i][1]*100.0)
    top_genus = top_genus[0], top_genus[1]*100.0

    return top_5_species, top_genus
