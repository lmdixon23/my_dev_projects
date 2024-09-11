import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator

def load_data(batch_size=32, img_size=(224, 224)):
    """Load and preprocess the dataset."""
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        validation_split=0.2
    )
    
    train_data = train_datagen.flow_from_directory(
        'datasets/raw/',
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='training'
    )

    val_data = train_datagen.flow_from_directory(
        'datasets/raw/',
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation'
    )

    return train_data, val_data

def load_test_data(img_size=(224, 224), batch_size=32):
    """Load and preprocess the test dataset."""
    test_datagen = ImageDataGenerator(rescale=1./255)
    
    test_data = test_datagen.flow_from_directory(
        'datasets/raw/',
        target_size=img_size,
        batch_size=batch_size,
        class_mode='categorical',
        subset='validation'
    )
    
    return test_data
