from tensorflow.keras.optimizers import Adam
from model import create_model
import numpy as np
from tensorflow.keras.utils import to_categorical

# Example data loading and preprocessing (replace with actual data)
vocab_size = 10000
max_length = 50
train_images = np.random.rand(1000, 224, 224, 3)
train_captions = np.random.randint(1, vocab_size, (1000, max_length))

# One-hot encode the captions
train_labels = to_categorical(train_captions, num_classes=vocab_size)

model = create_model(vocab_size, max_length)
model.compile(optimizer=Adam(), loss='categorical_crossentropy')

# Train the model
model.fit([train_images, train_captions], train_labels, epochs=20, batch_size=64, validation_split=0.2)

# Save the entire model
model.save('image_captioning_model.h5')