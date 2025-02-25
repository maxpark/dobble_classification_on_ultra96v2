#
# Dobble Buddy - Training tutorial
#
# References:
#   https://www.kaggle.com/grouby/dobble-card-images
#
# Dependencies:
#   numpy
#   cv2
#   os
#   csv
#   collections
#

import numpy as np
import cv2

import os
import random
import gc

import dobble_utils as db



#-- about GPU memory --
import tensorflow as tf 
gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        # Currently, memory growth needs to be the same across GPUs
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logical_gpus = tf.config.experimental.list_logical_devices('GPU')
        print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
    except RuntimeError as e:
        # Memory growth must be set before GPUs have been initialized
        print(e)


#
# Parameters
#

DIVIDER = '-----------------------------------------'

dir = '../../dobble_dataset'
nrows = 224
ncols = 224

nchannels = 3

#card_decks = [
#    'dobble_deck01_cards_57',
#    'dobble_deck02_cards_55',
#    'dobble_deck03_cards_55',
#    'dobble_deck04_cards_55',
#    'dobble_deck05_cards_55',
#    'dobble_deck06_cards_55',
#    'dobble_deck07_cards_55',
#    'dobble_deck08_cards_55',
#    'dobble_deck09_cards_55',
#    'dobble_deck10_cards_55'
#    ]

# augmented card decks
card_decks = [
    'dobble_deck01_cards_57-augmented',
    'dobble_deck02_cards_55-augmented',
    'dobble_deck03_cards_55-augmented',
    'dobble_deck04_cards_55-augmented',
    'dobble_deck05_cards_55-augmented',
    'dobble_deck06_cards_55-augmented',
    'dobble_deck07_cards_55-augmented',
    'dobble_deck08_cards_55-augmented',
    'dobble_deck09_cards_55-augmented',
    'dobble_deck10_cards_55-augmented'
    ]
nb_card_decks = len(card_decks)
print("")
print("PARAMETERS:")
print("Normalized shape of images :", ncols, " x ", nrows )
print("Card Decks : ", nb_card_decks, card_decks)

#
# Capture images/labels from data set for training and testing
#

train_cards = []
for d in range(0,nb_card_decks):
    train_dir = dir+'/'+card_decks[d]
    train_cards.append( db.capture_card_filenames(train_dir) )


gc.collect()

#
# Read images and pre-process to fixed size
#


train_X = []
train_y = []
for d in range(0,nb_card_decks):
   X,y = db.read_and_process_image(train_cards[d],nrows,ncols)
   train_X.append( np.array(X) )
   train_y.append( np.array(y) )

train_X = np.concatenate( train_X, axis=0 )
train_y = np.concatenate( train_y, axis=0 )
ntrain = len(train_y)

del train_cards
gc.collect()

#
# Split training data set down into two data sets : training(80%) and validation(20%)
#


from sklearn.model_selection import train_test_split
train_X,val_X,train_y,val_y = train_test_split(train_X,train_y, test_size=0.20, random_state=2)

print("")
print("TRAINING/VALIDATION DATA SETS:")
print("Shape of training data (X) is :", train_X.shape)
print("Shape of training data (y) is :", train_y.shape)
print("Shape of validation data (X) is :", val_X.shape)
print("Shape of validation data (y) is :", val_y.shape)


#
# Create model
#

ntrain = len(train_X)
nval   = len(val_X)
batch_size = 32
nepochs = 59

import os; os.environ['KERAS_BACKEND'] = 'tensorflow'
import sys
import tensorflow as tf
from keras import layers
from keras import models
from keras import optimizers
from keras.utils import to_categorical
from keras.preprocessing.image import ImageDataGenerator
from keras.preprocessing.image import img_to_array, load_img
from tensorflow.keras.callbacks import ModelCheckpoint, TensorBoard, LearningRateScheduler, ReduceLROnPlateau

# convert labels in range 0-57 to one-hot encoding
train_y = to_categorical(train_y,58)
val_y = to_categorical(val_y,58)

model = models.Sequential()
model.add(layers.Conv2D(32,(3,3), activation='relu', input_shape=(nrows,ncols,nchannels)))
model.add(layers.MaxPooling2D((2,2)))
model.add(layers.Conv2D(64,(3,3), activation='relu'))
model.add(layers.MaxPooling2D((2,2)))
model.add(layers.Conv2D(128,(3,3), activation='relu'))
model.add(layers.MaxPooling2D((2,2)))
model.add(layers.Conv2D(128,(3,3), activation='relu'))
model.add(layers.MaxPooling2D((2,2)))
model.add(layers.Dropout(0.5))
model.add(layers.Flatten())
model.add(layers.Dense(512))
model.add(layers.Activation('relu'))
model.add(layers.Dense(58))
model.add(layers.Activation('softmax'))

model.compile(loss='categorical_crossentropy',optimizer='adam')

print("")
print("MODEL SUMMARY:")
model.summary()

# prints a layer-by-layer summary of the network
print('\n'+DIVIDER)
print(' Model Summary')
print(DIVIDER)
print(model.summary())
print("Model Inputs: {ips}".format(ips=(model.inputs)))
print("Model Outputs: {ops}".format(ops=(model.outputs)))

print("")
print("TRAIN MODEL:")

print('\n'+DIVIDER)
print('Keras version      : ',tf.keras.__version__)
print('TensorFlow version : ',tf.__version__)
print(sys.version)
print(DIVIDER)


train_datagen = ImageDataGenerator( 
    rescale=1./255,
    rotation_range=360, 
    horizontal_flip=True 
    )
val_datagen   = ImageDataGenerator( 
    rescale=1./255
    )


train_generator = train_datagen.flow(train_X,train_y,batch_size=batch_size)
val_generator = val_datagen.flow(val_X,val_y,batch_size=batch_size)

def step_decay(epoch):
    """
    Learning rate scheduler used by callback
    Reduces learning rate depending on number of epochs
    """
    lr = learnrate
    if epoch > 150:
        lr /= 1000
    elif epoch > 120:
        lr /= 100
    elif epoch > 80:
        lr /= 10
    elif epoch > 20:
        lr /= 2
    return lr

'''
Callbacks
'''

chkpt_call = ModelCheckpoint(filepath='./build/keras_model/dobble_model.h5',
                         monitor='val_acc',
                         verbose=1,
                         save_best_only=True)

tb_call = TensorBoard(log_dir='./build/tb_logs',
                  batch_size=batch_size,
                  update_freq='epoch')


lr_scheduler_call = LearningRateScheduler(schedule=step_decay,
                                      verbose=1)

lr_plateau_call = ReduceLROnPlateau(factor=np.sqrt(0.1),
                                cooldown=0,
                                patience=5,
                                min_lr=0.5e-6)

callbacks_list = [tb_call, lr_scheduler_call, lr_plateau_call, chkpt_call]

history = model.fit(
    train_generator,
    steps_per_epoch=int(ntrain/batch_size),
    epochs=nepochs,
    validation_data=val_generator,
    validation_steps=int(nval/batch_size)
    )

model.save('./build/keras_model/dobble_model.h5')

#
# Test Model Accuracy
#

model.summary()

#test_dir = dir+'/dobble_test01_cards'
test_dir = dir+'/dobble_test02_cards'

test_cards = db.capture_card_filenames(test_dir)
random.shuffle(test_cards)

test_X,test_y = db.read_and_process_image(test_cards,nrows,ncols)
del test_cards

ntest = len(test_y)

test_X = np.array(test_X)
test_y = np.array(test_y)

# normalize images
test_X = test_X * (1./255)

# convert labels in range 0-57 to one-hot encoding
test_y = to_categorical(test_y,58)

print("Shape of test data (X) is :", test_X.shape)
print("Shape of test data (y) is :", test_y.shape)


print("")
print("EVALUATE MODEL:")
model.evaluate(test_X,test_y)

test_accuracy = db.test_accuracy(model,ntest,test_X,test_y)
print(test_dir," : Test Accuracy = ", test_accuracy)



