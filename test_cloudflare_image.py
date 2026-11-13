
from ai.image_generator import CloudflareImageGenerator

generator = CloudflareImageGenerator()

image_path = generator.generate_image("Tripataka")

print("Image generated successfully!")
print("Saved at:", image_path)