import onnxruntime as ort
import numpy as np

class OnnxScorer:
    def __init__(self, model_path: str):
        self.session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        # Note: Depending on skl2onnx conversion, output could be probabilities or label.
        # XGBoost ONNX output usually has two outputs: label, probabilities.
        self.output_names = [o.name for o in self.session.get_outputs()]

    def score(self, features: np.ndarray) -> tuple[float, str]:
        outputs = self.session.run(self.output_names, {self.input_name: features})
        
        # In typical skl2onnx classification, outputs[1] is a list of dicts mapping class to probability
        # Or a tensor of shape (N, C). Let's extract the probability of class 1 (fraud).
        try:
            if isinstance(outputs[1], list) and isinstance(outputs[1][0], dict):
                anomaly_score = float(outputs[1][0].get(1, 0.0))
            else:
                # If it's a tensor
                anomaly_score = float(outputs[1][0][1])
        except Exception:
            # Fallback if structure is different
            anomaly_score = float(outputs[0][0])
            
        decision = "ALLOW"
        if anomaly_score > 0.9:
            decision = "BLOCK"
        elif anomaly_score > 0.7:
            decision = "FLAG"
            
        return anomaly_score, decision
