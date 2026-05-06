import xgboost as xgb
from skl2onnx import convert_sklearn
from onnxmltools.convert.common.data_types import FloatTensorType
import onnx
from onnxmltools.convert import convert_xgboost
from pathlib import Path

def main():
    model_path = Path("models/xgboost_model.json")
    if not model_path.exists():
        print(f"Model file {model_path} not found. Run train.py first.")
        return
        
    print(f"Loading XGBoost model from {model_path}")
    model = xgb.XGBClassifier()
    model.load_model(model_path)
    
    # Define the inputs (18 features of type float32)
    initial_types = [('float_input', FloatTensorType([None, 18]))]
    
    print("Converting to ONNX...")
    # Using convert_xgboost for native XGBoost models
    onnx_model = convert_xgboost(model, initial_types=initial_types, target_opset=12)
    
    out_path = Path("models/xgboost_model.onnx")
    onnx.save(onnx_model, out_path)
    print(f"ONNX model saved to {out_path}")
    
    # Optional: Quantization can be done using onnxruntime.quantization if needed
    # but for simple XGBoost tree models, standard ONNX is already extremely fast (<1ms).
    # Quantization is usually more beneficial for deep learning models.

if __name__ == "__main__":
    main()
