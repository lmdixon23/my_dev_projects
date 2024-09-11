from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Dense, LSTM, Embedding, Dropout, Add, Flatten, RepeatVector, TimeDistributed
from tensorflow.keras.applications.vgg16 import VGG16

def create_model(vocab_size, max_length):
    # CNN Model
    inputs = Input(shape=(224, 224, 3))
    base_model = VGG16(include_top=False, input_tensor=inputs)
    
    # Flatten and reduce the feature maps from the CNN
    cnn_output = Flatten()(base_model.output)
    cnn_output = Dense(256, activation='relu')(cnn_output)
    
    # Expand the dimensions to be compatible with the LSTM (repeats the vector max_length times)
    cnn_output = RepeatVector(max_length)(cnn_output)

    # RNN Model (Decoder)
    decoder_input = Input(shape=(max_length,))
    embedding = Embedding(vocab_size, 256, mask_zero=True)(decoder_input)
    lstm_output = LSTM(256, return_sequences=True)(embedding)

    # Combine CNN and RNN outputs
    decoder_output = Add()([cnn_output, lstm_output])
    decoder_output = TimeDistributed(Dense(256, activation='relu'))(decoder_output)
    output = TimeDistributed(Dense(vocab_size, activation='softmax'))(decoder_output)

    model = Model(inputs=[inputs, decoder_input], outputs=output)
    return model