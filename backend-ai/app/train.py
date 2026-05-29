import os
# import zipfile
# with zipfile.ZipFile('/images.zip', 'r') as zip_ref:
#     zip_ref.extractall('/dataset_total/images')
# !pip install pandas torch torchvision keras numpy matplotlib scikit-learn
# !pip install opencv-python-headless --target /venv/main/lib/python3.12/site-packages/
os.environ['KERAS_BACKEND'] = 'torch'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import pandas as pd
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split

import keras
from keras import layers, models
from keras.optimizers import AdamW
from keras.callbacks import EarlyStopping
from keras import mixed_precision
mixed_precision.set_global_policy('mixed_float16')

print("GPU 사용 가능:", torch.cuda.is_available())
print("GPU 이름:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "없음")

# ════════════════════════════════════════════════════════
# 1. 설정
# ════════════════════════════════════════════════════════
CSV_PATH   = "/mnt/c/Users/dksrj/OneDrive/바탕 화면/weather_final_total.csv"
IMG_DIR    = "/mnt/c/Users/dksrj/OneDrive/바탕 화면/3조_데이터셋_images"
IMG_SIZE   = (224, 224)
BATCH_SIZE = 32
EPOCHS     = 100

# ════════════════════════════════════════════════════════
# 2. 데이터 불러오기
# ════════════════════════════════════════════════════════
df = pd.read_csv(CSV_PATH)
df = df.sample(frac=1).reset_index(drop=True)

# 파일 존재 여부 확인
exists = df['img_file'].apply(lambda x: os.path.exists(os.path.join(IMG_DIR, x)))
print(f"사라진 이미지 개수: {len(df) - exists.sum()}개")
df = df[exists].reset_index(drop=True)
print(f"정제 후 남은 데이터 개수: {len(df)}개")

# weather 원핫인코딩
weather_dummies = pd.get_dummies(df['weather'])
WEATHER_CLASSES = list(weather_dummies.columns)
num_weather_classes = len(WEATHER_CLASSES)
print(f"기상 클래스: {WEATHER_CLASSES}")

# ════════════════════════════════════════════════════════
# 3. PyTorch Dataset (GPU 최적화 + 데이터 증강)
# ════════════════════════════════════════════════════════
class MultiTaskDataset(Dataset):
    def __init__(self, df, img_dir, img_size, weather_classes, augment=False):
        self.df = df.reset_index(drop=True)
        self.img_dir = img_dir
        self.img_size = img_size
        self.weather_classes = weather_classes
        self.augment = augment

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_path = os.path.join(self.img_dir, row['img_file'])
        img = cv2.imread(img_path)
        img = cv2.resize(img, self.img_size)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img / 255.0

        # 데이터 증강 (학습용만)
        if self.augment:
            # 1. 좌우 반전
            if np.random.rand() > 0.5:
                img = np.fliplr(img)

            # 2. 밝기 조절 [0.8 ~ 1.2]
            brightness = np.random.uniform(0.8, 1.2)
            img = np.clip(img * brightness, 0, 1)

            # 3. 회전 (±15도)
            angle = np.random.uniform(-15, 15)
            h, w = img.shape[:2]
            M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
            img = cv2.warpAffine((img * 255).astype(np.uint8), M, (w, h)) / 255.0

        img = torch.tensor(img, dtype=torch.float32).permute(2, 0, 1)  # HWC → CHW

        weather_one_hot = torch.tensor(
            [1.0 if row['weather'] == w else 0.0 for w in self.weather_classes],
            dtype=torch.float32
        )
        danger = torch.tensor([float(row['danger_car'])], dtype=torch.float32)

        return img, {'weather_output': weather_one_hot, 'danger_output': danger}

# 학습/검증 분리
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['weather'])

train_dataset = MultiTaskDataset(train_df, IMG_DIR, IMG_SIZE, WEATHER_CLASSES, augment=True)
val_dataset   = MultiTaskDataset(val_df,   IMG_DIR, IMG_SIZE, WEATHER_CLASSES, augment=False)

train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True,  num_workers=4, pin_memory=True)
val_loader   = DataLoader(val_dataset,   batch_size=BATCH_SIZE, shuffle=False, num_workers=4, pin_memory=True)

# ════════════════════════════════════════════════════════
# 4. 멀티태스크 모델 구축 (ResNet50 기반)
# ════════════════════════════════════════════════════════
base_model = keras.applications.ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
base_model.trainable = False

x = base_model.output
x = layers.GlobalAveragePooling2D()(x)
x = layers.Dense(512, activation='relu')(x)
x = layers.Dropout(0.5)(x)

weather_output = layers.Dense(num_weather_classes, activation='softmax', dtype='float32', name='weather_output')(x)
danger_output  = layers.Dense(1, activation='sigmoid', dtype='float32', name='danger_output')(x)

model = models.Model(inputs=base_model.input, outputs=[weather_output, danger_output])

model.summary()

# ════════════════════════════════════════════════════════
# 5. 컴파일 및 학습
# ════════════════════════════════════════════════════════
model.compile(
    optimizer=AdamW(learning_rate=0.001, weight_decay=0.004),
    loss={
        'weather_output': 'categorical_crossentropy',
        'danger_output':  'binary_crossentropy'
    },
    loss_weights={
        'weather_output': 1.0,
        'danger_output':  1.0
    },
    metrics={
        'weather_output': 'accuracy',
        'danger_output':  'accuracy'
    }
)

early_stop = EarlyStopping(monitor='val_loss', patience=7, restore_best_weights=True)

print("🚀 멀티태스크 모델 학습 시작!")

import numpy as np

def loader_to_generator(loader):
    while True:
        for imgs, labels in loader:
            # (batch, C, H, W) → (batch, H, W, C)
            x = imgs.numpy().transpose(0, 2, 3, 1)
            y_weather = labels['weather_output'].numpy()
            y_danger  = labels['danger_output'].numpy()
            yield x, {'weather_output': y_weather, 'danger_output': y_danger}

train_gen = loader_to_generator(train_loader)
val_gen   = loader_to_generator(val_loader)

history = model.fit(
    train_gen,
    steps_per_epoch=len(train_loader),
    validation_data=val_gen,
    validation_steps=len(val_loader),
    epochs=EPOCHS,
    callbacks=[early_stop]
)

# ════════════════════════════════════════════════════════
# 6. 모델 저장
# ════════════════════════════════════════════════════════
model.save('./weather_danger_multitask_model.keras')
print("✅ 멀티태스크 모델 저장 완료!")

# ════════════════════════════════════════════════════════
# 7. results.csv 저장
# ════════════════════════════════════════════════════════
os.makedirs('./runs/train', exist_ok=True)

results_df = pd.DataFrame({
    'epoch':             range(1, len(history.history['loss']) + 1),
    'train_loss':        history.history['loss'],
    'val_loss':          history.history['val_loss'],
    'train_weather_acc': history.history['weather_output_accuracy'],
    'val_weather_acc':   history.history['val_weather_output_accuracy'],
    'train_danger_acc':  history.history['danger_output_accuracy'],
    'val_danger_acc':    history.history['val_danger_output_accuracy'],
})

results_df.to_csv('./runs/train/results.csv', index=False)
print("✅ results.csv 저장 완료!")