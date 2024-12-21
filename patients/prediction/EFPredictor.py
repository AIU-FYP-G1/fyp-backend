import os

import numpy as np
import tensorflow as tf
from keras import Model
from keras.src.applications.vgg16 import VGG16
import cv2
from keras.src.saving import load_model

from fyp_backend import settings


class EFPredictionPipeline:
    a4c_model_path = os.path.join(settings.BASE_DIR, 'static', 'models', 'a4c_model.keras')
    psax_model_path = os.path.join(settings.BASE_DIR, 'static', 'models', 'psax_model.keras')

    def __init__(self, view='a4c', frame_shape=(224, 224, 3), sequence_length=30):
        base_model = VGG16(weights='imagenet', include_top=False, input_shape=frame_shape)
        self.feature_extractor = Model(inputs=base_model.input, outputs=base_model.output)

        self.view = view

        if view == 'psax':
            respective_model_path = self.psax_model_path
        else:
            respective_model_path = self.a4c_model_path

        self.lstm_model = load_model(respective_model_path)

        self.frame_shape = frame_shape
        self.sequence_length = sequence_length

    def extract_video_features(self, video_path, interval=1):
        cap = cv2.VideoCapture(video_path)
        frame_features = []
        count = 0

        while cap.isOpened() and len(frame_features) < self.sequence_length:
            ret, frame = cap.read()
            if not ret:
                break

            if count % interval == 0:
                frame = cv2.resize(frame, (self.frame_shape[0], self.frame_shape[1]))
                frame = np.expand_dims(frame, axis=0)
                frame = tf.keras.applications.vgg16.preprocess_input(frame)

                features = self.feature_extractor.predict(frame)
                frame_features.append(features[0])

            count += 1

        cap.release()

        while len(frame_features) < self.sequence_length:
            frame_features.append(np.zeros_like(frame_features[0]))

        return np.array(frame_features)

    def process_demographic_data(self, demographic_data, volume_tracings):
        height_m = demographic_data['height'] / 100
        bmi = demographic_data['weight'] / (height_m ** 2)

        volume_stats = {
            'X_mean': np.mean(volume_tracings['X']),
            'X_std': np.std(volume_tracings['X']),
            'X_min': np.min(volume_tracings['X']),
            'X_max': np.max(volume_tracings['X']),
            'X_median': np.median(volume_tracings['X']),
            'X_q1': np.percentile(volume_tracings['X'], 25),
            'X_q3': np.percentile(volume_tracings['X'], 75),
            'Y_mean': np.mean(volume_tracings['Y']),
            'Y_std': np.std(volume_tracings['Y']),
            'Y_min': np.min(volume_tracings['Y']),
            'Y_max': np.max(volume_tracings['Y']),
            'Y_median': np.median(volume_tracings['Y']),
            'Y_q1': np.percentile(volume_tracings['Y'], 25),
            'Y_q3': np.percentile(volume_tracings['Y'], 75),
        }

        x_range = volume_stats['X_max'] - volume_stats['X_min']
        y_range = volume_stats['Y_max'] - volume_stats['Y_min']
        aspect_ratio = x_range / y_range

        AGE_BINS = [0, 30, 45, 60, 75, float('inf')]
        AGE_CATEGORIES = ['Young', 'Middle-Age', 'Early-Senior', 'Senior', 'Elderly']

        age_idx = next(i for i, threshold in enumerate(AGE_BINS[1:])
                       if demographic_data['age'] <= threshold)

        age_encoding = [1 if i == age_idx else 0 for i in range(len(AGE_CATEGORIES))]

        view_value = 1 if self.view == "a4c" else 0

        numerical_features = [
            demographic_data['age'],
            demographic_data['weight'],
            demographic_data['height'],
            bmi,
            volume_stats['X_mean'],
            volume_stats['X_std'],
            volume_stats['X_min'],
            volume_stats['X_max'],
            volume_stats['X_median'],
            volume_stats['X_q1'],
            volume_stats['X_q3'],
            volume_stats['Y_mean'],
            volume_stats['Y_std'],
            volume_stats['Y_min'],
            volume_stats['Y_max'],
            volume_stats['Y_median'],
            volume_stats['Y_q1'],
            volume_stats['Y_q3'],
            x_range,
            y_range,
            aspect_ratio
        ]

        all_features = np.concatenate([
            numerical_features,
            age_encoding,
            [view_value]
        ])

        return np.array(all_features)

    def predict_ef(self, video_path, demographic_data, volume_tracings, interval=1):
        video_path = os.path.join(settings.MEDIA_ROOT, str(video_path))
        video_features = self.extract_video_features(video_path, interval)
        demographic_features = self.process_demographic_data(demographic_data, volume_tracings)

        combined_input = {
            'input_layer': np.expand_dims(video_features, axis=0),
            'input_layer_1': np.expand_dims(demographic_features, axis=0)
        }

        ef_prediction = self.lstm_model.predict(combined_input)
        return int(ef_prediction[0][0])
