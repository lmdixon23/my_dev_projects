from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping
from src.model import create_model
from src.data_loader import load_data

def train_model():
    # Load data
    train_data, val_data = load_data()

    # Create model
    model = create_model(num_classes=train_data.num_classes)

    # Define callbacks
    checkpoint = ModelCheckpoint('saved_models/model.keras', save_best_only=True, monitor='val_loss')
    early_stopping = EarlyStopping(monitor='val_loss', patience=5)

    # Compile model
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    # Train model
    model.fit(train_data, epochs=20, validation_data=val_data, callbacks=[checkpoint, early_stopping])

if __name__ == "__main__":
    train_model()
