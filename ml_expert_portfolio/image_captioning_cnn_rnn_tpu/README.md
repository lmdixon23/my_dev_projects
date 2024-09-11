# Image Captioning CNN RNN TPU

## Overview

**Image_Captioning_Cnn_Rnn_Tpu** is a deep learning project that combines Convolutional Neural Networks (CNNs) for image feature extraction with Recurrent Neural Networks (RNNs) for generating descriptive captions. This project utilizes Google's TPU (Tensor Processing Unit) in Google Colab to significantly speed up the training process, making it feasible to work with large datasets and complex models.

## Key Features

- **TPU Acceleration**: Leveraging Google's TPU in Colab for faster training and efficient handling of large datasets.
- **Transfer Learning**: Using pre-trained CNN models like VGG16 for feature extraction to improve performance and reduce training time.
- **Sequence Generation**: RNNs, specifically LSTMs, are used to generate sequences of words that describe the content of the image.

## Example Usage

After running the project, you can observe the following sequence of operations:

- **Image Feature Extraction**: The CNN extracts features from the input image, which are then passed to the RNN.
- **Caption Generation**: The RNN generates a descriptive caption for the image based on the extracted features.
- **Evaluation**: The generated captions are compared with ground truth captions using metrics like BLEU scores.

## Future Enhancements

- **Improved Captioning Accuracy**: Experimenting with Transformer models or attention mechanisms to improve the quality of generated captions.
- **Multi-Language Support**: Extending the model to generate captions in multiple languages.
- **Fine-Tuning Pre-trained Models**: Further fine-tuning the CNNs on specific datasets to improve feature extraction for particular image types.

## Technical Specifications

- **Language**: Python
- **Frameworks**: TensorFlow, Keras
- **Hardware**: Google Colab TPU for accelerated training

## Contributing

I welcome contributions from the community to enhance the features, performance, and accuracy of this project. Feel free to fork the repository, make your changes, and submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For further inquiries or partnership opportunities, please contact lmdixon23@gmail.com.

## Getting Started

### Downloads

- **Datasets**: [COCO Dataset, Val2017 images](http://images.cocodataset.org/zips/val2017.zip)
- **Pre-trained Model**: [saved_model_tpu.keras](https://drive.google.com/file/d/1-4cxaETjo6f1h9AHolJzcbzxssDeg_yW/view?usp=drive_link)


### Prerequisites

- **Google Colab**: A Google account to access Google Colab.
- **TensorFlow**: TensorFlow and Keras are pre-installed in Colab, but you can install specific versions if needed.

### Installation

Clone the repository and navigate into the project directory:

```bash
git clone https://github.com/lmdixon23/image_captioning_cnn_rnn.git
cd image_captioning_cnn_rnn
