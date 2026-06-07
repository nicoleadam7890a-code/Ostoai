import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
import os
import time
import copy

# Configuration
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "OS Collected Data")
MODEL_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "xray_model")
BATCH_SIZE = 16
NUM_EPOCHS = 2  # Sufficient for demonstration and basic accuracy
LEARNING_RATE = 0.001
MODELS_TO_TRAIN = ['mobilenet', 'resnet', 'densenet']

def get_model(model_type, num_classes):
    """Helper to initialize different model architectures."""
    if model_type == 'mobilenet':
        model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        # Freeze bg
        for param in model.parameters(): param.requires_grad = False
        num_ftrs = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(num_ftrs, num_classes)
        return model, model.classifier[1].parameters()
    
    elif model_type == 'resnet':
        model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        for param in model.parameters(): param.requires_grad = False
        num_ftrs = model.fc.in_features
        model.fc = nn.Linear(num_ftrs, num_classes)
        return model, model.fc.parameters()
        
    elif model_type == 'densenet':
        model = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)
        for param in model.parameters(): param.requires_grad = False
        num_ftrs = model.classifier.in_features
        model.classifier = nn.Linear(num_ftrs, num_classes)
        return model, model.classifier.parameters()
    
    return None, None

def train_single_model(model_type, dataloaders, dataset_sizes, class_names):
    """Trains a specific model architecture."""
    num_classes = len(class_names)
    print(f"\n--- Training: {model_type.upper()} ---")
    
    model, params_to_train = get_model(model_type, num_classes)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(params_to_train, lr=LEARNING_RATE)

    best_model_wts = copy.deepcopy(model.state_dict())
    best_acc = 0.0

    for epoch in range(NUM_EPOCHS):
        print(f'Epoch {epoch}/{NUM_EPOCHS - 1} ({model_type})')
        for phase in ['train', 'val']:
            if phase == 'train': model.train()
            else: model.eval()

            running_loss, running_corrects = 0.0, 0
            for inputs, labels in dataloaders[phase]:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad()
                with torch.set_grad_enabled(phase == 'train'):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)
                    if phase == 'train':
                        loss.backward()
                        optimizer.step()
                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)
            
            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]
            print(f'{phase} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}')

            if phase == 'val' and epoch_acc > best_acc:
                best_acc = epoch_acc
                best_model_wts = copy.deepcopy(model.state_dict())

    # Save model
    save_path = f"{MODEL_BASE_PATH}_{model_type}.pth"
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    model.load_state_dict(best_model_wts)
    torch.save({
        'model_state_dict': model.state_dict(),
        'class_names': class_names,
        'model_type': model_type
    }, save_path)
    print(f"Model saved to {save_path}")

def train_all_models():
    # Setup data
    data_transforms = {
        'train': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        'val': transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    full_dataset = datasets.ImageFolder(DATA_DIR, transform=data_transforms['train'])
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(full_dataset, [train_size, val_size])
    val_dataset.dataset.transform = data_transforms['val']

    dataloaders = {
        'train': DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True),
        'val': DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    }
    dataset_sizes = {'train': train_size, 'val': val_size}
    class_names = full_dataset.classes

    for model_type in MODELS_TO_TRAIN:
        train_single_model(model_type, dataloaders, dataset_sizes, class_names)

if __name__ == "__main__":
    train_all_models()
