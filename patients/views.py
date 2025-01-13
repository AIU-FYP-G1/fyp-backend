import json
import os
import random
import time

import requests
import numpy as np
import pandas as pd
from rest_framework import generics, permissions
from rest_framework.parsers import MultiPartParser, FormParser
import boto3

import numpy as np
import tensorflow as tf
from keras import Model
from keras.src.applications.vgg16 import VGG16
from keras.src.saving import load_model
import cv2

from patients.models import Patient, Diagnosis, Interpretation
from patients.serializers import PatientSerializer, DiagnosisSerializer


class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return patients associated with the logged-in doctor's profile
        return Patient.objects.filter(doctor=self.request.user.profile)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.profile)


class PatientDetailView(generics.RetrieveAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Patient.objects.filter(doctor=self.request.user.profile)


class DiagnosisListCreateView(generics.ListCreateAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    ECHO_ANALYSIS_URL = 'empty_for_now'

    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return Diagnosis.objects.filter(
            patient_id=patient_id,
            patient__doctor=self.request.user.profile
        ).prefetch_related('interpretations').order_by('-diagnosis_date')

    def perform_create(self, serializer):
        patient_id = self.kwargs.get('patient_id')
        patient = Patient.objects.get(id=patient_id, doctor=self.request.user.profile)

        diagnosis = serializer.save(patient=patient)

        try:
            self.analyze_echo(diagnosis)
        except Exception as e:
            print(f"Error analyzing echo: {str(e)}")

        self.create_interpretations(diagnosis)

    def create_interpretations(self, diagnosis):
        ef = diagnosis.ejection_fraction

        if ef >= 75:
            interpretations = [
                "Dangerously elevated ejection fraction (≥75%) suggesting possible Hypertrophic Cardiomyopathy",
                "High risk condition requiring immediate attention due to potential cardiac arrest risk",
                "Impaired ventricular filling due to extremely high ejection fraction"
            ]
        elif 50 <= ef <= 70:
            interpretations = [
                f"Normal ejection fraction ({ef}%) indicating preserved systolic function",
                "Heart pumping function within normal range",
                "Consider monitoring for HFpEF despite normal ejection fraction"
            ]
        elif 41 <= ef <= 49:
            interpretations = [
                f"Borderline low ejection fraction ({ef}%) indicating mild systolic dysfunction",
                "May experience mild symptoms during physical activity",
                "Regular monitoring and follow-up recommended"
            ]
        elif 30 <= ef <= 40:
            interpretations = [
                f"Moderately abnormal ejection fraction ({ef}%) indicating significant dysfunction",
                "Patient may experience symptoms even at rest",
                "Close monitoring and therapy adjustment may be needed"
            ]
        else:  # ef < 30
            interpretations = [
                f"Severely abnormal ejection fraction ({ef}%) indicating critical cardiac dysfunction",
                "High risk condition requiring immediate medical attention",
                "Patient likely experiencing severe symptoms with risk of cardiac arrest"
            ]

        num_interpretations = random.randint(2, 3)
        selected_interpretations = random.sample(interpretations, num_interpretations)

        for interpretation in selected_interpretations:
            Interpretation.objects.create(
                diagnosis=diagnosis,
                note=interpretation
            )

    def analyze_echo(self, diagnosis):
        try:
            API_URL = "https://5a1c-124-13-17-173.ngrok-free.app/predict"

            files = {
                'video': diagnosis.echocardiogram.file
            }

            demo_data = {
                'age': diagnosis.patient.get_age(),
                'weight': diagnosis.patient.weight if diagnosis.patient.weight else 70,
                'height': diagnosis.patient.height if diagnosis.patient.height else 180,
            }

            data = {
                'view': diagnosis.view_type,
                'demographic_data': json.dumps(demo_data),
            }

            response = requests.post(API_URL, files=files, data=data)

            if response.status_code == 200:
                result = response.json()
                print(result)
                diagnosis.ejection_fraction = result['ef_prediction']
                diagnosis.save()
            else:
                error_message = response.json().get('detail', 'Unknown error')
                raise Exception(f"API Error: {error_message}")

        except requests.RequestException as e:
            print(f"Error calling inference API: {str(e)}")
            raise
        except Exception as e:
            print(f"Error in analyze_echo: {str(e)}")
            raise
        finally:
            diagnosis.echocardiogram.close()

    # def analyze_echo(self, diagnosis):
    #     try:
    #         # tf.config.set_visible_devices([], 'GPU')
    #         # os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
    #         # os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
    #         # os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    #         #
    #         # default_view = 'a4c'
    #         #
    #         # s3 = boto3.client(
    #         #     's3',
    #         #     region_name='us-east-1',
    #         #     aws_access_key_id='AKIA4XKCFOLNNFAMKCEL',
    #         #     aws_secret_access_key='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'
    #         # )
    #         #
    #         # model_path = f'/tmp/{default_view}_model.keras'
    #         # try:
    #         #     s3.download_file(
    #         #         'fyp-models',
    #         #         f'{default_view}_model.keras',
    #         #         model_path
    #         #     )
    #         # except Exception as e:
    #         #     raise Exception(f"Failed to download model from S3: {str(e)}")
    #         #
    #         # cache_dir = '/tmp/.keras/models'
    #         # os.makedirs(cache_dir, exist_ok=True)
    #         #
    #         # base_model = VGG16(
    #         #     weights='imagenet',
    #         #     include_top=False,
    #         #     input_shape=(224, 224, 3)
    #         # )
    #         # feature_extractor = Model(inputs=base_model.input, outputs=base_model.output)
    #         #
    #         # lstm_model = load_model(model_path)
    #         #
    #         # demo_data = {
    #         #     'age': diagnosis.patient.get_age(),
    #         #     'weight': diagnosis.patient.weight if diagnosis.patient.weight else 70,
    #         #     'height': diagnosis.patient.height if diagnosis.patient.height else 180,
    #         # }
    #         #
    #         # volume_tracings = pd.DataFrame({
    #         #     'X': np.random.normal(100, 10, 100),
    #         #     'Y': np.random.normal(100, 10, 100)
    #         # })
    #         #
    #         # video_features = self.extract_video_features(
    #         #     diagnosis.echocardiogram.path,
    #         #     feature_extractor
    #         # )
    #         #
    #         # demographic_features = self.process_demographic_data(
    #         #     demo_data,
    #         #     volume_tracings,
    #         #     default_view
    #         # )
    #         #
    #         # combined_input = {
    #         #     'input_layer': np.expand_dims(video_features, axis=0),
    #         #     'input_layer_1': np.expand_dims(demographic_features, axis=0)
    #         # }
    #         #
    #         # ejection_fraction = lstm_model.predict(combined_input)
    #         # diagnosis.ejection_fraction = int(ejection_fraction[0][0])
    #         diagnosis.ejection_fraction = self.get_random_ef()
    #         diagnosis.save()
    #         #
    #         # if os.path.exists(model_path):
    #         #     os.remove(model_path)
    #
    #     except Exception as e:
    #         print(f"Error in analyze_echo: {str(e)}")
    #         raise
    #     finally:
    #         diagnosis.echocardiogram.close()

    def get_random_ef(self):
        time.sleep(4)
        weights = [
            (55, 70, 50),
            (40, 54, 25),
            (71, 90, 15),
            (10, 39, 10)
        ]

        chosen_range = random.choices(weights, weights=[w[2] for w in weights])[0]
        return random.randint(chosen_range[0], chosen_range[1])

    def extract_video_features(self, video_path, feature_extractor, sequence_length=30, interval=1):
        try:
            cap = cv2.VideoCapture(video_path)
            frame_features = []
            count = 0

            while cap.isOpened() and len(frame_features) < sequence_length:
                ret, frame = cap.read()
                if not ret:
                    break

                if count % interval == 0:
                    frame = cv2.resize(frame, (224, 224))
                    frame = np.expand_dims(frame, axis=0)
                    frame = tf.keras.applications.vgg16.preprocess_input(frame)

                    features = feature_extractor.predict(frame, batch_size=1)
                    frame_features.append(features[0])

                    # Clear memory
                    tf.keras.backend.clear_session()

                count += 1

            cap.release()

            # Pad sequence if needed
            while len(frame_features) < sequence_length:
                frame_features.append(np.zeros_like(frame_features[0]))

            return np.array(frame_features)
        except Exception as e:
            print(f"Error in extract_video_features: {str(e)}")
            raise

    def process_demographic_data(self, demographic_data, volume_tracings, view):
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
        view_value = 1 if view == "a4c" else 0

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


class DiagnosisDetailView(generics.RetrieveAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return Diagnosis.objects.filter(
            patient_id=patient_id,
            patient__doctor=self.request.user.profile)
