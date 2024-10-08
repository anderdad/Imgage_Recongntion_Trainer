import os
import torch
import timm
import json

from torchvision import datasets, transforms
from torch.utils.data import DataLoader


train_path = ""
val_path = ""
classes = []

with open('config.json') as f:
    data = json.load(f)
    train_path = data['relative_training_path']
    val_path = data['relative_validation_path']
    classes = data['classes']    

# Function to create class to index mapping
def idx_json():
    idx = {}
    c = 0
    for i in classes.split(","):
        idx[i] = c
        c+=1  
        
    return idx


def save_predictions(model, dataloader, device, output_file):
    model.eval()
    predictions = []
    labels = []
    
    with torch.no_grad():
        for inputs, targets in dataloader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            _, preds = torch.max(outputs, 1)
            predictions.extend(preds.cpu().numpy())
            labels.extend(targets.cpu().numpy())
    
    # Save predictions and labels to a file
    with open(output_file, 'w') as f:
        for pred, label in zip(predictions, labels):
            f.write(f"{pred},{label}\n")

def main():
    # Step 1: Define transformations
    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # Resize images to 224x224
        transforms.ToTensor(),          # Convert images to PyTorch tensors
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])  # Normalize with ImageNet mean and std
    ])

    # Step 2: Load the datasets
    idx = idx_json()
    dataset = datasets.ImageFolder(root=val_path, transform=transform)
    dataset.class_to_idx = idx
    #dataset.class_to_idx = {'Duiker': 0, 'Leopard': 1, 'Lion': 2, 'WildDog': 3, 'Hyena': 4, 'WartHog': 5, 'Jackal': 6}

    # Step 3: Create data loader
    dataloader = DataLoader(dataset, batch_size=32, shuffle=False, num_workers=4)

    # Step 4: Load the model
    checkpoint_path = "./resnet50_best.pth.tar"
    if os.path.exists(checkpoint_path):
        model = timm.create_model(
            'resnet50', 
            pretrained=False,
            num_classes= len(idx),
            checkpoint_path=checkpoint_path
        )
        print(f"Loaded model from checkpoint: {checkpoint_path}")

        # Step 5: Save predictions
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        save_predictions(model, dataloader, device, "predictions.csv")

if __name__ == "__main__":
    main()