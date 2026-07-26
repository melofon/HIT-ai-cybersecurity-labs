# Triton model repository

Place exported models under this directory using Triton's standard layout:

```
model_repository/
  anomaly/
    config.pbtxt
    1/
      model.onnx
```

The repository intentionally contains no binary model. Configure `config/settings.yaml`
with the deployed model name and use `MORPHEUS_INFERENCE_PROVIDER=triton`.
