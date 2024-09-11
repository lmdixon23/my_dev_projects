from tensorflow.keras.applications import VGG16
from tensorflow.keras.layers import Dense, Flatten, Input
from tensorflow.keras.models import Model

# Define the input shape for the images (224x224 pixels with 3 color channels). This specifies that we are loading weights pre-trained on the ImageNet dataset.
input_tensor = Input(shape=(224, 224, 3))

# Load the VGG16 model pre-trained on ImageNet, excluding the top layers of the network, as we’ll be adding our own layers later.
vgg16 = VGG16(weights='imagenet', include_top=False, input_tensor=input_tensor)

# Freeze the VGG16 layers to prevent them from being trained.
for layer in vgg16.layers:
    layer.trainable = False

# Flatten the output of the VGG16 model (by converting the 3D output of the last convolutional layer of VGG16 into a 1D vector)
flatten = Flatten()(vgg16.output)

# Add a fully connected layer with 256 units and ReLU activation function.
fc = Dense(256, activation='relu')(flatten)

# Create the CNN encoder model: the input to the model is the input tensor defined earlier, and the output is the final dense layer we added.
cnn_encoder = Model(inputs=vgg16.input, outputs=fc)

# Print the summary of the model to check its architecture.
cnn_encoder.summary()

# (Optional) Compile the model to check its structure
# This step is usually done when integrating with the RNN decoder
# cnn_encoder.compile(optimizer='adam', loss='categorical_crossentropy')
