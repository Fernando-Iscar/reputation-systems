# This file trains and tests the RNN in inference.py with data sets generated by models.py
import settings
from inference_threshold_testing import *
from models_single_product import *

RD.seed()



if __name__ == '__main__':

    dynamics = market(settings.params)

    model = RNN()

    # model.empty_losses()

    print('pretraining performance on the traning set')

    # training_sample1 = dynamics.genTorchDataset(LOAD=True, filename='toy_dataset.pkl')
    # training_sample2 = dynamics.genTorchDataset(LOAD=True, filename='toy_dataset2_4000.pkl')
    # training_sample3 = dynamics.genTorchDataset(LOAD=True, filename='toy_dataset3_10000.pkl')
    # training_sample4 = dynamics.genTorchDataset(LOAD=True, filename='toy_dataset4_14000.pkl')
    # training_sample5 = dynamics.genTorchDataset(LOAD=True, filename='toy_dataset5_20000.pkl')

    training_sample = dynamics.genTorchDataset(settings.SIZE_TRAINING_SET, SAVE=True,
                                               filename='dataset_' + str(settings.SIZE_TRAINING_SET) + '_'
                                                        + settings.tracked_product_ID +
                                                        '.pkl')


    # training_sample = dynamics.genTorchDataset(LOAD=True,
    #                                            filename='dataset_' + str(settings.SIZE_TRAINING_SET) + '_'
    #                                                     + settings.tracked_product_ID +
    #                                                     '.pkl')
    # training_sample = dynamics.genTorchDataset(LOAD=True,
    #                                            filename='dataset0_200' + '_'
    #                                                     + settings.tracked_product_ID +
    #                                                     '.pkl')
    # training_sample6 = dynamics.genTorchDataset(LOAD=True,filename='dataset_5000_B0067PLM5E.pkl')
    # training_sample = training_sample1 + training_sample2 + training_sample3 + training_sample4 + training_sample5

    # training_sample6x = training_sample + training_sample + training_sample + training_sample  + training_sample  + training_sample \
    #                     + training_sample + training_sample + training_sample + training_sample + training_sample + training_sample \
    #                     + training_sample + training_sample

    # print(training_sample)
    print(100 * model.evaluateAveragePerformance(training_sample))

    print('doTraining on the traning set')

    model.doTraining(training_sample, batch_size = settings.BATCH_SIZE, window_length_loss=settings.WINDOW_LENGTH,
                     verbose = True, save = True , file_name = 'model_tuned_' + settings.tracked_product_ID + '.pkl')

    # model = model.load_from_file('model_tuned_' + settings.tracked_product_ID + '.pkl')

    print('perforamce on Trainging set AFTER')
    print(100 * model.evaluateAveragePerformance(training_sample))
    model.plot_losses(file_name='losses' + settings.tracked_product_ID + '.png')
    model.save_losses()
    print(model.training_losses)


    print('performance on Test set after training')

    test_sample = dynamics.genTorchDataset(settings.SIZE_TEST_SET, SAVE=True, filename='dataset_'
                                                                                       + str(settings.SIZE_TRAINING_SET)
                                                                                       + '_'+ settings.tracked_product_ID
                                                                                       + '.pkl')

    # test_sample = dynamics.genTorchDataset(100)
    print(100 * model.evaluateAveragePerformance(test_sample))
