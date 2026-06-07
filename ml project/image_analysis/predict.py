import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import os

class XRayEnsemblePredictor:
    def __init__(self, model_dir="models"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_types = ['mobilenet', 'resnet', 'densenet']
        self.models = {}
        self.class_names = []
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        
        self.load_ensemble(model_dir)

    def _get_base_model(self, model_type, num_classes):
        """Rebuilds the architecture for a specific model type."""
        if model_type == 'mobilenet':
            model = models.mobilenet_v2(weights=None)
            num_ftrs = model.classifier[1].in_features
            model.classifier[1] = nn.Linear(num_ftrs, num_classes)
        elif model_type == 'resnet':
            model = models.resnet50(weights=None)
            num_ftrs = model.fc.in_features
            model.fc = nn.Linear(num_ftrs, num_classes)
        elif model_type == 'densenet':
            model = models.densenet121(weights=None)
            num_ftrs = model.classifier.in_features
            model.classifier = nn.Linear(num_ftrs, num_classes)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        return model

    def load_ensemble(self, model_dir):
        """Loads all available models in the ensemble."""
        loaded_count = 0
        for m_type in self.model_types:
            path = os.path.join(model_dir, f"xray_model_{m_type}.pth")
            if os.path.exists(path):
                print(f"Loading {m_type} model...")
                checkpoint = torch.load(path, map_location=self.device)
                
                if not self.class_names:
                    self.class_names = checkpoint['class_names']
                
                num_classes = len(self.class_names)
                model = self._get_base_model(m_type, num_classes)
                model.load_state_dict(checkpoint['model_state_dict'])
                model = model.to(self.device)
                model.eval()
                
                self.models[m_type] = model
                loaded_count += 1
            else:
                print(f"Warning: {m_type} model not found at {path}")
        
        if loaded_count == 0:
            print("❌ Error: No ensemble models loaded!")

    def predict(self, image_path):
        if not self.models:
            return {"status": "error", "message": "No models loaded in ensemble"}
            
        try:
            img = Image.open(image_path).convert('RGB')
            img_t = self.transform(img)
            batch_t = torch.unsqueeze(img_t, 0).to(self.device)
            
            all_probs = []
            model_results = {}
            
            with torch.no_grad():
                for name, model in self.models.items():
                    outputs = model(batch_t)
                    probs = torch.nn.functional.softmax(outputs[0], dim=0)
                    all_probs.append(probs)
                    
                    # Store individual model details
                    conf, pred = torch.max(probs, 0)
                    model_results[name] = {
                        "prediction": self.class_names[pred.item()],
                        "confidence": float(conf.item()),
                        "probabilities": {cls: float(p) for cls, p in zip(self.class_names, probs)}
                    }
            
            # Average probabilities across all models
            avg_probs = torch.stack(all_probs).mean(dim=0)
            conf, pred = torch.max(avg_probs, 0)
            
            result = {
                "status": "success",
                "prediction": self.class_names[pred.item()],
                "confidence": float(conf.item()),
                "probabilities": {name: float(prob) for name, prob in zip(self.class_names, avg_probs)},
                "model_details": model_results,
                "ensemble_size": len(self.models)
            }
            return result
        except Exception as e:
            return {"status": "error", "message": f"Ensemble prediction failed: {str(e)}"}

# Compatibility wrapper for existing code
class XRayPredictor(XRayEnsemblePredictor):
    pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        predictor = XRayEnsemblePredictor()
        print(predictor.predict(sys.argv[1]))
    else:
        print("Usage: python predict.py <image_path>")
