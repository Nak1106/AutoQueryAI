from llama_cpp import Llama

llm = Llama(model_path="./models/llama-2/ggml-model-q4_0.gguf")
output = llm("What is the capital of France?")
print(output)
