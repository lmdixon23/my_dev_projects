import os
import numpy as np
from PIL import Image
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.utils import to_categorical

# Set the path to the dataset
IMAGE_DIR = 'datasets/val2017/'
MAX_LENGTH = 50  # Maximum length of the caption sequences
VOCAB_SIZE = 10000  # Assume a vocabulary size of 10,000

def preprocess_image(image_path, target_size=(224, 224)):
    """
    Load and preprocess a single image.
    :param image_path: Path to the image file
    :param target_size: Target size to resize the image
    :return: Preprocessed image as a numpy array
    """
    image = Image.open(image_path).resize(target_size)
    image = np.array(image) / 255.0  # Normalize the image
    return image

def preprocess_images(image_dir):
    """
    Preprocess all images in a directory.
    :param image_dir: Directory containing images
    :return: Numpy array of preprocessed images
    """
    images = []
    for img_name in os.listdir(image_dir):
        img_path = os.path.join(image_dir, img_name)
        image = preprocess_image(img_path)
        images.append(image)
    return np.array(images)

def preprocess_captions(captions, tokenizer, max_length):
    """
    Tokenize and pad the captions.
    :param captions: List of caption strings
    :param tokenizer: Fitted Keras Tokenizer
    :param max_length: Maximum length of the padded sequences
    :return: Padded and one-hot encoded sequences
    """
    sequences = tokenizer.texts_to_sequences(captions)
    padded_sequences = pad_sequences(sequences, maxlen=max_length, padding='post')
    one_hot_labels = to_categorical(padded_sequences, num_classes=VOCAB_SIZE)
    return one_hot_labels

def load_data(image_dir, captions, max_length):
    """
    Load and preprocess images and captions.
    :param image_dir: Directory containing images
    :param captions: List of caption strings
    :param max_length: Maximum length of the padded sequences
    :return: Preprocessed images and one-hot encoded captions
    """
    # Preprocess images
    images = preprocess_images(image_dir)
    
    # Initialize and fit the tokenizer on the captions
    tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token='<OOV>')
    tokenizer.fit_on_texts(captions)
    
    # Preprocess captions
    captions = preprocess_captions(captions, tokenizer, max_length)
    
    return images, captions, tokenizer

# Example usage (replace with your actual data)
# captions = ["a caption for image 1", "another caption for image 2", ...]
# images, captions, tokenizer = load_data(IMAGE_DIR, captions, MAX_LENGTH)

# Save tokenizer if needed
# import pickle
# with open('tokenizer.pkl', 'wb') as f:
#     pickle.dump(tokenizer, f)
