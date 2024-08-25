import os
import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import nltk
from nltk.translate.bleu_score import sentence_bleu
from data_preprocessing import preprocess_image  # Ensure this matches the actual import path
from model import create_model  # Ensure this matches the actual import path

# Download necessary NLTK resources
nltk.download('punkt')

# Load the trained model and tokenizer
model = create_model(vocab_size=10000, max_length=50)  # Adjust vocab_size and max_length accordingly
model.load_weights('path_to_saved_model')  # Replace with the path to your saved model

# Load the tokenizer (replace with actual loading code)
# tokenizer = 'path_to_saved_tokenizer'  # Replace this with the actual loading code for your tokenizer

# Define function to generate captions
def generate_caption(model, tokenizer, image, max_length):
    in_text = '<start>'
    for i in range(max_length):
        sequence = tokenizer.texts_to_sequences([in_text])[0]
        sequence = pad_sequences([sequence], maxlen=max_length)
        yhat = model.predict([image, sequence], verbose=0)
        yhat = np.argmax(yhat)
        word = tokenizer.index_word.get(yhat, '<unk>')
        in_text += ' ' + word
        if word == '<end>':
            break
    return in_text

# Define function to evaluate the model
def evaluate_model(model, tokenizer, images, captions, max_length):
    actual, predicted = list(), list()
    for img, caption in zip(images, captions):
        y_pred = generate_caption(model, tokenizer, img, max_length)
        actual.append(caption.split())
        predicted.append(y_pred.split())
    return actual, predicted

# Get a list of all image files in the dataset directory
image_dir = r'image_captioning_cnn_rnn\datasets\val2017'
image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith('.jpg')]

# Load and preprocess one image for evaluation
image_path = image_files[0]  # Replace with logic to select specific image if needed
image = preprocess_image(image_path)
image = np.expand_dims(image, axis=0)

# Generate and print the caption
# tokenizer = 'path_to_saved_tokenizer'  # Load your tokenizer here
caption = generate_caption(model, tokenizer, image, max_length=50)
print(f'Generated Caption: {caption}')

# Assuming test_images and test_captions are loaded
# Evaluate on the full test set (update the paths as necessary)
# actual, predicted = evaluate_model(model, tokenizer, test_images, test_captions, max_length=50)

# Calculate BLEU scores
# bleu_scores = [sentence_bleu([ref], pred) for ref, pred in zip(actual, predicted)]
# print(f'Average BLEU Score: {np.mean(bleu_scores)}')

# Visualize one of the results
def visualize_caption(image_path, caption, ground_truth):
    plt.imshow(plt.imread(image_path))
    plt.title(f'Predicted: {caption}\nGround Truth: {ground_truth}')
    plt.axis('off')
    plt.show()

# Replace with paths and captions for visualization
visualize_caption(image_path, caption, 'ground_truth_caption_here')