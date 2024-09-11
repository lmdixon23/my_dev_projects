from tensorflow.keras.applications import VGG16
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, Dropout

def create_model(input_shape=(224, 224, 3), num_classes=10):
    """Create a transfer learning model using VGG16."""
    base_model = VGG16(weights='imagenet', include_top=False, input_shape=input_shape)
    
    model = Sequential()
    model.add(base_model)
    model.add(Flatten())
    model.add(Dense(256, activation='relu'))
    model.add(Dropout(0.5))
    model.add(Dense(num_classes, activation='softmax'))
    
    # Freeze the base_model layers
    for layer in base_model.layers:
        layer.trainable = False
    
    return model
