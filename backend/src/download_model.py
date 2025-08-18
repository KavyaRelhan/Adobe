from sentence_transformers import SentenceTransformer

model_name = 'all-MiniLM-L6-v2'
save_path = './models/all-MiniLM-L6-v2'

print(f"Downloading model '{model_name}' to '{save_path}'...")
model = SentenceTransformer(model_name)
model.save(save_path)
print("Download complete.")
